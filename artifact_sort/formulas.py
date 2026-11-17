"""Typed arithmetic compilation for the offline scenario library.

Expressions become a dependency-ordered program; no authored text is executed.
All percentage stats are dimensionless decimal ratios.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import math
import re
from typing import Mapping, TypeAlias, cast

import numpy as np
from numpy.typing import NDArray

from .model import STAT_KEYS

Json: TypeAlias = None | bool | int | float | str | list["Json"] | dict[str, "Json"]
Scalar: TypeAlias = bool | float | str
Dimension: TypeAlias = tuple[tuple[str, int], ...]
Stats: TypeAlias = Mapping[str, float]
BatchValue: TypeAlias = float | NDArray[np.float64]
BatchStats: TypeAlias = Mapping[str, BatchValue]
# Python 3.12+ uses compensated floating-point summation in sum().
_COMPENSATED_SUM = sum([1e16, 1.0, -1e16]) == 1.0
STAGES = {"static": 0, "conversion": 1, "bonus": 2, "score": 3}
STAT_STAGES = {"base": 0, "raw": 1, "effective": 2}


ARITIES: dict[str, tuple[int, int | None]] = {
    "constant": (0, 0),
    "stat": (0, 0),
    "channel": (0, 0),
    "parameter": (0, 0),
    "condition": (0, 0),
    "ref": (0, 0),
    "add": (2, None),
    "multiply": (2, None),
    "min": (2, None),
    "max": (2, None),
    "subtract": (2, 2),
    "divide": (2, 2),
    "clamp": (3, 3),
}


class LibraryError(ValueError):
    """Invalid library definition or unresolved mechanics."""


class EvaluationError(ValueError):
    """Invalid candidate inputs or undefined numerical calculation."""


def dimension(unit: str) -> Dimension:
    powers: Counter[str] = Counter()
    sign = 1
    for token in re.split(r"([*/])", unit):
        if token in ("*", "/"):
            sign = -1 if token == "/" else 1
        elif token != "scalar":
            powers[token] += sign
    return tuple(sorted((key, power) for key, power in powers.items() if power))


def stat_dimension(key: str) -> Dimension:
    return () if key.endswith("_") else dimension("em" if key == "eleMas" else key)


@dataclass(frozen=True, slots=True)
class Expression:
    op: str
    args: tuple[Expression, ...] = ()
    key: str = ""
    stage: int = 0
    value: float = 0.0
    unit: Dimension = ()


def parse_expression(value: Json) -> Expression:
    """Normalize schema-validated JSON once at the loading boundary."""
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return Expression("constant", value=float(value))
    node = cast(dict[str, Json], value)
    if "value" in node:
        return Expression(
            "constant",
            value=float(cast(float, node["value"])),
            unit=dimension(cast(str, node["unit"])),
        )
    for op in ("stat", "ref", "parameter", "condition", "channel"):
        if op in node:
            stage = STAT_STAGES[cast(str, node["stage"])] if op == "stat" else 0
            return Expression(op, key=cast(str, node[op]), stage=stage)
    op = cast(str, node["op"])
    if op == "extension":
        # Wire format reserved; no arbitrary callable registration in this engine.
        name, version = node["name"], node["version"]
        raise LibraryError(f"unsupported extension {name}@{version}")
    return Expression(
        op, args=tuple(parse_expression(arg) for arg in cast(list[Json], node["args"]))
    )


@dataclass(frozen=True, slots=True)
class Predicate:
    op: str
    args: tuple[Predicate, ...] = ()
    key: str = ""
    value: Scalar = False
    pieces: int = 0

    def evaluate(
        self, conditions: Mapping[str, Scalar], sets: Mapping[str, int]
    ) -> bool:
        match self.op:
            case "all":
                return all(arg.evaluate(conditions, sets) for arg in self.args)
            case "any":
                return any(arg.evaluate(conditions, sets) for arg in self.args)
            case "not":
                return not self.args[0].evaluate(conditions, sets)
            case "set":
                return sets.get(self.key, 0) >= self.pieces
            case "condition":
                if self.key not in conditions:
                    raise EvaluationError(f"missing activation condition {self.key!r}")
                actual = conditions[self.key]
                return type(actual) is type(self.value) and actual == self.value
        raise EvaluationError(f"unknown predicate {self.op!r}")

    @property
    def set_keys(self) -> frozenset[str]:
        return frozenset({self.key} if self.op == "set" else ()).union(
            *(arg.set_keys for arg in self.args)
        )


def parse_predicate(value: Json) -> Predicate:
    node = cast(dict[str, Json], value)
    for op in ("all", "any"):
        if op in node:
            return Predicate(
                op, tuple(parse_predicate(arg) for arg in cast(list[Json], node[op]))
            )
    if "not" in node:
        return Predicate("not", (parse_predicate(node["not"]),))
    if "set" in node:
        return Predicate(
            "set", key=cast(str, node["set"]), pieces=cast(int, node["pieces"])
        )
    expected = node["equals"]
    if isinstance(expected, (int, float)) and not isinstance(expected, bool):
        expected = float(expected)
    return Predicate(
        "condition", key=cast(str, node["condition"]), value=cast(Scalar, expected)
    )


@dataclass(frozen=True, slots=True)
class Component:
    stage: int
    unit: Dimension
    expression: Expression
    target: str = ""
    when: Predicate | None = None


@dataclass(frozen=True, slots=True)
class Channel:
    unit: Dimension
    combine: str


@dataclass(frozen=True, slots=True)
class Instruction:
    op: str
    args: tuple[int, ...] = ()
    key: str = ""
    stage: int = 0
    value: float = 0.0


def arithmetic(op: str, values: list[float]) -> float:
    match op:
        case "add":
            result = sum(values)
        case "multiply":
            result = math.prod(values)
        case "subtract":
            result = values[0] - values[1]
        case "divide":
            if values[1] == 0:
                raise EvaluationError("division by zero")
            result = values[0] / values[1]
        case "min":
            result = min(values)
        case "max":
            result = max(values)
        case "clamp":
            if values[1] > values[2]:
                raise EvaluationError("reversed clamp bounds")
            result = min(max(values[0], values[1]), values[2])
        case _:
            raise EvaluationError(f"unsupported operation {op!r}")
    if not math.isfinite(result):
        raise EvaluationError(f"nonfinite result from {op}")
    return result


@dataclass(frozen=True, slots=True)
class Program:
    instructions: tuple[Instruction, ...]
    result: int
    unit: Dimension
    stat_reads: frozenset[tuple[int, str]]
    channel_reads: frozenset[str]
    component_reads: frozenset[str]

    def evaluate_batch(
        self,
        stats: tuple[BatchStats, BatchStats, BatchStats],
        channels: BatchStats,
        count: int,
    ) -> NDArray[np.float64]:
        """Execute the same instruction stream on arrays of candidate values."""
        values = []
        with np.errstate(divide="ignore", invalid="ignore", over="ignore"):
            for instruction in self.instructions:
                op = instruction.op
                if op == "constant":
                    result = instruction.value
                elif op == "stat":
                    try:
                        result = stats[instruction.stage][instruction.key]
                    except KeyError as error:
                        raise EvaluationError(f"missing stat {instruction.key!r}") from error
                elif op == "channel":
                    result = channels[instruction.key]
                else:
                    args = [values[i] for i in instruction.args]
                    if op == "add" and _COMPENSATED_SUM and len(args) > 2:
                        high = np.zeros(count)
                        low = np.zeros(count)
                        for arg in args:
                            updated = high + arg
                            low += np.where(np.abs(high) >= np.abs(arg),
                                            (high - updated) + arg,
                                            (arg - updated) + high)
                            high = updated
                        result = high + low
                    elif op in ("add", "multiply", "min", "max"):
                        result = args[0]
                        operation = {"add": np.add, "multiply": np.multiply,
                                     "min": np.minimum, "max": np.maximum}[op]
                        for arg in args[1:]:
                            result = operation(result, arg)
                    elif op == "subtract":
                        result = np.subtract(*args)
                    elif op == "divide":
                        if np.any(np.asarray(args[1]) == 0):
                            raise EvaluationError("division by zero")
                        result = np.divide(*args)
                    elif op == "clamp":
                        if np.any(np.asarray(args[1]) > args[2]):
                            raise EvaluationError("reversed clamp bounds")
                        result = np.minimum(np.maximum(args[0], args[1]), args[2])
                    else:
                        raise EvaluationError(f"unsupported operation {op!r}")
                if not np.all(np.isfinite(result)):
                    raise EvaluationError(f"nonfinite value in {op}")
                values.append(result)
        return np.broadcast_to(values[self.result], (count,))

    def evaluate(self, stats: tuple[Stats, Stats, Stats], channels: Stats) -> float:
        values: list[float] = []
        for instruction in self.instructions:
            match instruction.op:
                case "constant":
                    result = instruction.value
                case "stat":
                    if instruction.key not in stats[instruction.stage]:
                        raise EvaluationError(f"missing stat {instruction.key!r}")
                    result = stats[instruction.stage][instruction.key]
                case "channel":
                    result = channels[instruction.key]
                case "parameter" | "condition":
                    raise EvaluationError(
                        "cannot evaluate an unbound validation program"
                    )
                case _:
                    result = arithmetic(
                        instruction.op, [values[i] for i in instruction.args]
                    )
            if not math.isfinite(result):
                raise EvaluationError(f"nonfinite value in {instruction.op}")
            values.append(result)
        return values[self.result]

    def differentiate(
        self,
        stats: tuple[Stats, Stats, Stats],
        channels: Stats,
        stat_derivatives: tuple[
            Mapping[str, NDArray[np.float64]],
            Mapping[str, NDArray[np.float64]],
            Mapping[str, NDArray[np.float64]],
        ],
        channel_derivatives: Mapping[str, NDArray[np.float64]],
    ) -> tuple[float, NDArray[np.float64], bool]:
        """Forward-mode derivatives of the compiled arithmetic, in STAT_KEYS order.

        At min/max/clamp ties, use the first active branch and report a boundary
        when tied branches have different derivatives. No finite-difference step
        or manually selected stat weights enter this calculation.
        """
        values: list[float] = []
        derivatives: list[NDArray[np.float64]] = []
        zero = np.zeros(len(STAT_KEYS), dtype=np.float64)
        boundary = False
        for instruction in self.instructions:
            match instruction.op:
                case "constant":
                    value, derivative = instruction.value, zero
                case "stat":
                    if instruction.key not in stats[instruction.stage]:
                        raise EvaluationError(f"missing stat {instruction.key!r}")
                    value = stats[instruction.stage][instruction.key]
                    derivative = stat_derivatives[instruction.stage].get(
                        instruction.key, zero
                    )
                case "channel":
                    value = channels[instruction.key]
                    derivative = channel_derivatives.get(instruction.key, zero)
                case "parameter" | "condition":
                    raise EvaluationError("cannot differentiate an unbound program")
                case _:
                    args = [values[i] for i in instruction.args]
                    gradients = [derivatives[i] for i in instruction.args]
                    value = arithmetic(instruction.op, args)
                    match instruction.op:
                        case "add":
                            derivative = np.sum(gradients, axis=0)
                        case "subtract":
                            derivative = gradients[0] - gradients[1]
                        case "multiply":
                            derivative = sum(
                                (
                                    gradient * math.prod(args[:i] + args[i + 1 :])
                                    for i, gradient in enumerate(gradients)
                                ),
                                zero.copy(),
                            )
                        case "divide":
                            derivative = (gradients[0] - value * gradients[1]) / args[1]
                        case "min" | "max":
                            active = [i for i, arg in enumerate(args) if arg == value]
                            derivative = gradients[active[0]]
                            boundary |= any(
                                not np.array_equal(derivative, gradients[i])
                                for i in active[1:]
                            )
                        case "clamp":
                            # Match min(max(x, lower), upper), including first-branch ties.
                            inner = 0 if args[0] >= args[1] else 1
                            selected = inner if args[inner] <= args[2] else 2
                            derivative = gradients[selected]
                            boundary |= (
                                args[0] == args[1]
                                and args[0] <= args[2]
                                and not np.array_equal(gradients[0], gradients[1])
                            ) or (
                                args[inner] == args[2]
                                and not np.array_equal(gradients[inner], gradients[2])
                            )
                        case _:
                            raise EvaluationError(
                                f"unsupported derivative {instruction.op!r}"
                            )
            if not math.isfinite(value) or not np.all(np.isfinite(derivative)):
                raise EvaluationError(f"nonfinite derivative/value in {instruction.op}")
            values.append(value)
            derivatives.append(derivative)
        return values[self.result], derivatives[self.result].copy(), boundary


class _Compiler:
    def __init__(
        self,
        components: Mapping[str, Component],
        channels: Mapping[str, Channel],
        parameters: Stats | None,
        conditions: Mapping[str, Scalar] | None,
    ):
        self.components = components
        self.channels = channels
        self.parameters = parameters
        self.conditions = conditions
        self.instructions: list[Instruction] = []
        self.memo: dict[Expression, tuple[int, Dimension]] = {}
        self.references: dict[str, tuple[int, Dimension]] = {}
        self.active: list[str] = []
        self.stat_reads: set[tuple[int, str]] = set()
        self.channel_reads: set[str] = set()
        self.component_reads: set[str] = set()

    def emit(self, node: Expression, stage: int) -> tuple[int, Dimension]:
        if node.op not in ARITIES:
            raise LibraryError(f"unsupported operation {node.op!r}")
        minimum, maximum = ARITIES[node.op]
        if len(node.args) < minimum or maximum is not None and len(node.args) > maximum:
            raise LibraryError(f"invalid argument count for {node.op}")
        if node.op == "constant" and not math.isfinite(node.value):
            raise LibraryError("nonfinite constant")
        if node.op == "stat" and (
            node.key not in STAT_KEYS or node.stage not in (0, 1, 2)
        ):
            raise LibraryError("unknown stat or stat stage")
        # Stage checks precede memo lookup: reuse must not bypass ordering rules.
        if node.op == "stat" and node.stage > min(stage, 2):
            raise LibraryError("stat reference reads a future calculation stage")
        if node.op == "channel" and stage != 3:
            raise LibraryError("only score expressions may read completed channels")
        if node.op == "ref":
            if node.key not in self.components:
                raise LibraryError(f"unresolved component {node.key!r}")
            component = self.components[node.key]
            if component.target:
                raise LibraryError(
                    f"effect {node.key!r} cannot be used as a pure reference"
                )
            if component.stage > stage:
                raise LibraryError(f"component {node.key!r} reads a future stage")
            if node.key in self.active:
                raise LibraryError(
                    f'component cycle: {" -> ".join(self.active + [node.key])}'
                )
            self.component_reads.add(node.key)
            if node.key not in self.references:
                self.active.append(node.key)
                result = self.emit(component.expression, component.stage)
                self.active.pop()
                if result[1] != component.unit:
                    raise LibraryError(f"component {node.key!r} has inconsistent units")
                self.references[node.key] = result
            return self.references[node.key]
        # Composite expressions need stage checking even if already memoized.
        args = tuple(self.emit(arg, stage) for arg in node.args)
        if node in self.memo:
            return self.memo[node]
        unit = node.unit
        instruction = Instruction(
            node.op, tuple(i for i, _ in args), node.key, node.stage, node.value
        )
        match node.op:
            case "stat":
                unit = stat_dimension(node.key)
                self.stat_reads.add((node.stage, node.key))
            case "channel":
                if node.key not in self.channels:
                    raise LibraryError(f"unresolved channel {node.key!r}")
                unit = self.channels[node.key].unit
                self.channel_reads.add(node.key)
            case "parameter" | "condition":
                inputs = self.parameters if node.op == "parameter" else self.conditions
                if inputs is not None:
                    if node.key not in inputs:
                        raise LibraryError(f"missing {node.op} {node.key!r}")
                    value = inputs[node.key]
                    if isinstance(value, (str, bool)):
                        raise LibraryError(f"{node.op} {node.key!r} must be numeric")
                    instruction = Instruction("constant", value=float(value))
            case "add" | "subtract" | "min" | "max" | "clamp":
                unit = args[0][1]
                if any(arg_unit != unit for _, arg_unit in args):
                    raise LibraryError(f"incompatible units in {node.op}")
            case "multiply" | "divide":
                powers: Counter[str] = Counter(dict(args[0][1]))
                for _, arg_unit in args[1:]:
                    sign = -1 if node.op == "divide" else 1
                    for key, power in arg_unit:
                        powers[key] += sign * power
                unit = tuple(
                    sorted((key, power) for key, power in powers.items() if power)
                )
        result = len(self.instructions), unit
        self.instructions.append(instruction)
        self.memo[node] = result
        return result


def compile_expression(
    expression: Expression,
    unit: Dimension,
    *,
    components: Mapping[str, Component],
    channels: Mapping[str, Channel],
    stage: int = 3,
    parameters: Stats | None = None,
    conditions: Mapping[str, Scalar] | None = None,
) -> Program:
    if stage not in (0, 1, 2, 3):
        raise LibraryError("unknown component stage")
    compiler = _Compiler(components, channels, parameters, conditions)
    index, inferred = compiler.emit(expression, stage)
    if inferred != unit:
        raise LibraryError(
            f"declared unit {unit} differs from expression unit {inferred}"
        )
    return Program(
        tuple(compiler.instructions),
        index,
        inferred,
        frozenset(compiler.stat_reads),
        frozenset(compiler.channel_reads),
        frozenset(compiler.component_reads),
    )
