"""Load and evaluate version-4 offline scenarios independently of legacy analysis."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import asdict, dataclass
from hashlib import sha256
from importlib.resources import files
import json
import math
from pathlib import Path
from types import MappingProxyType
from typing import Iterable, Mapping, TypeVar, cast

from jsonschema import Draft202012Validator

from .formulas import (
    Channel,
    Component,
    Expression,
    Json,
    LibraryError,
    Scalar,
    STAGES,
    Stats,
    compile_expression,
    dimension,
    parse_expression,
    parse_predicate,
    stat_dimension,
)
from .model import STAT_KEYS
from .library_runtime import (
    EVALUATOR_VERSION,
    INTRINSIC_STATS,
    LEGAL_MAINS,
    PRIMARY_STATS,
    CompiledEffect,
    CompiledLibrary,
    CompiledScenario,
    Mechanics,
    ScenarioDefinition,
    normalize_good_stats,
)

Definition = TypeVar("Definition", Component, Channel)
SCHEMA = json.loads(
    files("artifact_sort").joinpath("scenario-library.schema.json").read_text()
)
VALIDATOR = Draft202012Validator(SCHEMA)


def _finite(value: Json, path: str = "$") -> None:
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if not math.isfinite(value):
            raise LibraryError(f"{path}: nonfinite number")
    elif isinstance(value, dict):
        for key, item in value.items():
            _finite(item, f"{path}.{key}")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            _finite(item, f"{path}[{index}]")


def _validate(data: dict[str, Json]) -> None:
    _finite(data)
    error = next(VALIDATOR.iter_errors(data), None)
    if error:
        location = ".".join(str(key) for key in error.absolute_path) or "$"
        raise LibraryError(f"{location}: {error.message}")


def _merge(parent: dict[str, Json], changes: dict[str, Json]) -> dict[str, Json]:
    result = deepcopy(parent)
    for key, value in changes.items():
        if value is None:
            result.pop(key, None)
        elif isinstance(value, dict):
            result[key] = _merge(cast(dict[str, Json], result.get(key, {})), value)
        else:
            result[key] = deepcopy(value)
    return result


def _stats(value: Json) -> Stats:
    return MappingProxyType(
        {
            key: float(cast(float, number))
            for key, number in cast(dict[str, Json], value).items()
        }
    )


def _conditions(value: Json) -> Mapping[str, Scalar]:
    return MappingProxyType(
        {
            key: (
                float(number)
                if isinstance(number, (int, float)) and not isinstance(number, bool)
                else cast(Scalar, number)
            )
            for key, number in cast(dict[str, Json], value).items()
        }
    )


def _scenario(node: dict[str, Json], collection: str) -> ScenarioDefinition:
    minimums, maximums = _stats(node.get("minimums", {})), _stats(
        node.get("maximums", {})
    )
    for key in minimums.keys() & maximums.keys():
        if minimums[key] > maximums[key]:
            raise LibraryError(f'{node["id"]}: minimum {key} exceeds maximum')
    strategies = tuple(
        MappingProxyType(cast(dict[str, int], strategy))
        for strategy in cast(list[Json], node["sets"])
    )
    if any(sum(strategy.values()) > 5 for strategy in strategies):
        raise LibraryError(f'{node["id"]}: set strategy requires more than five pieces')
    mains = {
        slot: tuple(cast(list[str], keys))
        for slot, keys in cast(dict[str, Json], node.get("mains", {})).items()
    }
    for slot, keys in mains.items():
        if not set(keys) <= LEGAL_MAINS[slot]:
            raise LibraryError(f'{node["id"]}: illegal main stat for {slot}')
    return ScenarioDefinition(
        cast(str, node["id"]),
        collection,
        cast(str, node["scoring_formula"]),
        _stats(node["base"]),
        _stats(node.get("buffs", {})),
        minimums,
        maximums,
        strategies,
        _conditions(node.get("conditions", {})),
        _stats(node.get("parameters", {})),
        MappingProxyType(mains),
        tuple(cast(list[str], node.get("effects", []))),
        tuple(cast(list[str], node.get("characters", []))),
        cast(str | None, node.get("family")),
    )


@dataclass(frozen=True, slots=True)
class ScenarioLibrary:
    revision: str
    mechanics: str
    scenarios: Mapping[str, ScenarioDefinition]
    components: Mapping[str, Component]
    scoring_formulas: Mapping[str, tuple[Expression, str]]
    channels: Mapping[str, Channel]
    effects: tuple[str, ...]
    research_statuses: Mapping[tuple[str, str], str]
    canonical_content: str
    research_content: str | None

    def compile(
        self,
        mechanics: Mechanics,
        *,
        allow_draft: bool = False,
        scenario_ids: Iterable[str] | None = None,
    ) -> CompiledLibrary:
        if mechanics.id != self.mechanics:
            raise LibraryError(
                f"mechanics pin {self.mechanics!r} does not match installed {mechanics.id!r}"
            )
        components = _combine(self.components, mechanics.components or {}, "component")
        channels = _combine(self.channels, mechanics.channels or {}, "channel")
        _validate_graph(components, channels, self.scoring_formulas)
        selected = (
            tuple(self.scenarios) if scenario_ids is None else tuple(scenario_ids)
        )
        if len(set(selected)) != len(selected) or set(selected) - self.scenarios.keys():
            raise LibraryError("selected scenario IDs must be unique and resolve")
        compiled: dict[str, CompiledScenario] = {}
        limitations: set[str] = set()
        if not mechanics.validated:
            limitations.add(f"mechanics release {mechanics.id!r} is not validated")
        for key in selected:
            scenario = self.scenarios[key]
            if set(scenario.characters) - mechanics.characters:
                raise LibraryError(f"{key}: unknown character keys")
            if any(set(strategy) - mechanics.sets for strategy in scenario.sets):
                raise LibraryError(f"{key}: unknown set keys")
            expr, unit = self.scoring_formulas[scenario.scoring_formula]
            score = compile_expression(
                expr,
                dimension(unit),
                components=components,
                channels=channels,
                parameters=scenario.parameters,
                conditions=scenario.conditions,
            )
            effects: list[CompiledEffect] = []
            component_ids = set(score.component_reads)
            for effect_id in dict.fromkeys((*self.effects, *scenario.effects)):
                if effect_id not in components or not components[effect_id].target:
                    raise LibraryError(f"{key}: unresolved effect {effect_id!r}")
                component = components[effect_id]
                if component.when and component.when.set_keys - mechanics.sets:
                    raise LibraryError(f"{effect_id}: unknown activation set keys")
                program = compile_expression(
                    component.expression,
                    component.unit,
                    components=components,
                    channels=channels,
                    stage=component.stage,
                    parameters=scenario.parameters,
                    conditions=scenario.conditions,
                )
                effects.append(
                    CompiledEffect(
                        effect_id,
                        component.stage,
                        component.target,
                        component.when,
                        program,
                    )
                )
                component_ids.add(effect_id)
                component_ids.update(program.component_reads)
            programs = (score, *(effect.program for effect in effects))
            required_stats = set(scenario.minimums) | set(scenario.maximums)
            for program in programs:
                for stage, stat in program.stat_reads:
                    if stage > 0:
                        required_stats.add(stat)
                    if (
                        stage == 0 or stat in INTRINSIC_STATS
                    ) and stat not in scenario.base:
                        raise LibraryError(
                            f"{key}: missing intrinsic/base stat {stat!r}"
                        )
            for stat in set(scenario.minimums) | set(scenario.maximums):
                if stat in INTRINSIC_STATS and stat not in scenario.base:
                    raise LibraryError(f"{key}: missing intrinsic/base stat {stat!r}")
            for stat in tuple(required_stats):
                if stat in PRIMARY_STATS:
                    required_stats.add(f"{stat}_")
            records = [
                ("scenarios", key),
                ("scoring_formulas", scenario.scoring_formula),
            ]
            # Pinned component accuracy is part of the mechanics release's validation assertion.
            records.extend(
                ("components", component_id)
                for component_id in component_ids
                if component_id in self.components
            )
            for table, record_id in records:
                if self.research_statuses.get((table, record_id)) != "validated":
                    limitations.add(f"{table}.{record_id} is not validated")
            compiled[key] = CompiledScenario(
                scenario,
                score,
                tuple(effects),
                channels,
                mechanics.sets,
                frozenset(required_stats),
            )
        if limitations and not allow_draft:
            raise LibraryError(
                "library is not a validated release: " + "; ".join(sorted(limitations))
            )
        fingerprint = _fingerprint(
            self.canonical_content, mechanics, selected, allow_draft
        )
        return CompiledLibrary(
            MappingProxyType(compiled),
            fingerprint,
            mechanics,
            bool(limitations),
            tuple(sorted(limitations)),
        )


def _combine(
    local: Mapping[str, Definition], pinned: Mapping[str, Definition], kind: str
) -> Mapping[str, Definition]:
    if local.keys() & pinned.keys():
        raise LibraryError(
            f"conflicting local/pinned {kind} IDs: {sorted(local.keys() & pinned.keys())}"
        )
    return MappingProxyType({**pinned, **local})


def _validate_graph(
    components: Mapping[str, Component],
    channels: Mapping[str, Channel],
    formulas: Mapping[str, tuple[Expression, str]],
) -> None:
    for key, channel in channels.items():
        if channel.combine not in ("add", "multiply"):
            raise LibraryError(
                f"channel {key}: invalid aggregation {channel.combine!r}"
            )
    for key, component in components.items():
        try:
            compile_expression(
                component.expression,
                component.unit,
                components=components,
                channels=channels,
                stage=component.stage,
            )
            if component.target:
                if "." not in component.target:
                    raise LibraryError("invalid contribution target")
                kind, target = component.target.split(".", 1)
                if kind not in ("stats", "channels"):
                    raise LibraryError("invalid contribution target")
                if kind == "stats":
                    if component.stage not in (0, 1) or target not in STAT_KEYS:
                        raise LibraryError(
                            "static/conversion effects must target known stats"
                        )
                    target_unit = stat_dimension(target)
                else:
                    if component.stage != 2 or target not in channels:
                        raise LibraryError(
                            "bonus effects must target declared channels"
                        )
                    target_unit = channels[target].unit
                if component.unit != target_unit:
                    raise LibraryError("effect and target have incompatible units")
            elif component.when:
                raise LibraryError("pure components cannot have activation predicates")
        except LibraryError as error:
            raise LibraryError(f"component {key}: {error}") from error
    for key, (expression, unit) in formulas.items():
        try:
            compile_expression(
                expression, dimension(unit), components=components, channels=channels
            )
        except LibraryError as error:
            raise LibraryError(f"scoring_formula {key}: {error}") from error


def _fingerprint(
    content: str, mechanics: Mechanics, selected: tuple[str, ...], allow_draft: bool
) -> str:
    # Serialize the installed numerical definitions, not just a potentially reused release name.
    pinned = {
        "id": mechanics.id,
        "game_version": mechanics.game_version,
        "sets": sorted(mechanics.sets),
        "characters": sorted(mechanics.characters),
        "components": {
            key: asdict(value) for key, value in (mechanics.components or {}).items()
        },
        "channels": {
            key: asdict(value) for key, value in (mechanics.channels or {}).items()
        },
        "validated": mechanics.validated,
    }
    payload = json.dumps(
        [EVALUATOR_VERSION, json.loads(content), pinned, selected, allow_draft],
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )
    return sha256(payload.encode()).hexdigest()


def _components(value: Json) -> dict[str, Component]:
    result = {}
    for key, entry in cast(dict[str, dict[str, Json]], value).items():
        result[key] = Component(
            STAGES[cast(str, entry["stage"])],
            dimension(cast(str, entry["unit"])),
            parse_expression(entry["expression"]),
            cast(str, entry.get("contributes_to", "")),
            parse_predicate(entry["when"]) if "when" in entry else None,
        )
    return result


def _channels(value: Json) -> dict[str, Channel]:
    return {
        key: Channel(dimension(cast(str, entry["unit"])), cast(str, entry["combine"]))
        for key, entry in cast(dict[str, dict[str, Json]], value).items()
    }


def library_from_data(
    data: Mapping[str, Json], *, research: Mapping[str, Json] | None = None
) -> ScenarioLibrary:
    document = deepcopy(dict(data))
    _validate(document)
    definitions: dict[str, tuple[dict[str, Json], str]] = {}
    for collection in ("established", "parameter_variations", "structural_variations"):
        for value in cast(list[Json], document[collection]):
            node = cast(dict[str, Json], value)
            key = cast(str, node["id"])
            if key in definitions:
                raise LibraryError(f"duplicate scenario ID {key!r}")
            definitions[key] = node, collection
    expanded: dict[str, dict[str, Json]] = {}

    def expand(key: str, parents: tuple[str, ...] = ()) -> dict[str, Json]:
        if key in parents:
            raise LibraryError(f'parent cycle: {" -> ".join((*parents, key))}')
        if key not in definitions:
            raise LibraryError(f"unresolved scenario parent {key!r}")
        if key not in expanded:
            node, collection = definitions[key]
            if collection == "parameter_variations":
                parent = cast(str, node["extends"])
                if (
                    parent in definitions
                    and definitions[parent][1] == "structural_variations"
                ):
                    raise LibraryError(
                        "parameter variants may not extend structural variations"
                    )
                node = _merge(
                    expand(parent, (*parents, key)),
                    cast(dict[str, Json], node["changes"]),
                )
                node["id"] = key
            expanded[key] = node
        return expanded[key]

    scenarios: dict[str, ScenarioDefinition] = {}
    for key, (_, collection) in definitions.items():
        node = expand(key)
        # Apply the complete-scenario schema after merge/null removal.
        wrapped: dict[str, Json] = dict(document)
        wrapped.update(
            established=[node], parameter_variations=[], structural_variations=[]
        )
        _validate(wrapped)
        scenarios[key] = _scenario(node, collection)
    components = _components(document["components"])
    channels = _channels(document["channels"])
    formulas = {}
    for key, value in cast(dict[str, Json], document["scoring_formulas"]).items():
        node = cast(dict[str, Json], value)
        formulas[key] = parse_expression(node["expression"]), cast(str, node["unit"])
    for scenario in scenarios.values():
        if scenario.scoring_formula not in formulas:
            raise LibraryError(
                f"{scenario.id}: unresolved scoring formula {scenario.scoring_formula!r}"
            )
    statuses: dict[tuple[str, str], str] = {}
    research_content = None
    if research is not None:
        _finite(dict(research))
        if research.get("library_revision") != document["revision"]:
            raise LibraryError("research revision does not match library revision")
        sources = research.get("sources", {})
        if not isinstance(sources, dict):
            raise LibraryError("research sources must be an object")
        for table, expected_ids in (
            ("scenarios", scenarios.keys()),
            ("components", components.keys()),
            ("scoring_formulas", formulas.keys()),
        ):
            records = research.get(table, {})
            if not isinstance(records, dict) or set(records) != set(expected_ids):
                raise LibraryError(
                    f"research {table} IDs must match library definitions"
                )
            for key, record in records.items():
                if not isinstance(record, dict) or record.get("status") not in (
                    "draft",
                    "reviewed",
                    "validated",
                ):
                    raise LibraryError(f"invalid research status for {table}.{key}")
                references = record.get("sources", [])
                if not isinstance(references, list) or any(
                    not isinstance(ref, str) or ref not in sources for ref in references
                ):
                    raise LibraryError(f"unresolved research sources for {table}.{key}")
                statuses[table, key] = cast(str, record["status"])
        research_content = json.dumps(
            research, sort_keys=True, separators=(",", ":"), allow_nan=False
        )
    # Store expanded numerical definitions so inheritance edits affect cache identity.
    canonical = dict(
        document,
        established=[
            expanded[key]
            for key in scenarios
            if scenarios[key].collection == "established"
        ],
        parameter_variations=[
            expanded[key]
            for key in scenarios
            if scenarios[key].collection == "parameter_variations"
        ],
        structural_variations=[
            expanded[key]
            for key in scenarios
            if scenarios[key].collection == "structural_variations"
        ],
    )
    return ScenarioLibrary(
        cast(str, document["revision"]),
        cast(str, document["mechanics"]),
        MappingProxyType(scenarios),
        MappingProxyType(components),
        MappingProxyType(formulas),
        MappingProxyType(channels),
        tuple(cast(list[str], document["effects"])),
        MappingProxyType(statuses),
        json.dumps(canonical, sort_keys=True, separators=(",", ":"), allow_nan=False),
        research_content,
    )


def _read_json(path: Path) -> dict[str, Json]:
    def unique_pairs(pairs: list[tuple[str, Json]]) -> dict[str, Json]:
        result: dict[str, Json] = {}
        for key, value in pairs:
            if key in result:
                raise LibraryError(f"{path}: duplicate JSON key {key!r}")
            result[key] = value
        return result

    try:
        document = json.loads(
            path.read_text(encoding="utf-8"), object_pairs_hook=unique_pairs
        )
    except (OSError, json.JSONDecodeError) as error:
        raise LibraryError(f"cannot load {path}: {error}") from error
    if not isinstance(document, dict):
        raise LibraryError(f"{path}: expected a JSON object")
    return cast(dict[str, Json], document)


def load_library(
    path: str | Path, *, research_path: str | Path | None = None
) -> ScenarioLibrary:
    path = Path(path)
    sidecar = (
        Path(research_path)
        if research_path is not None
        else path.with_suffix(".research.json")
    )
    research = (
        _read_json(sidecar) if research_path is not None or sidecar.exists() else None
    )
    return library_from_data(_read_json(path), research=research)


def load_mechanics(path: str | Path) -> Mechanics:
    """Load an explicit numerical rules manifest; validation is a publisher assertion.

    Component/channel encodings use the same schema as authored libraries.
    This does not retrieve game data or validate the accuracy of a rules release.
    """
    return mechanics_from_data(_read_json(Path(path)))


def mechanics_from_data(data: Mapping[str, Json]) -> Mechanics:
    """Normalize an uploaded numerical manifest using the file loader's contract."""
    document = deepcopy(dict(data))
    schema = {
        "type": "object",
        "additionalProperties": False,
        "$defs": SCHEMA["$defs"],
        "properties": {
            "format": {"const": "artifact-sort-mechanics"},
            "version": {"const": 1},
            "id": {"type": "string", "minLength": 1},
            "game_version": {"type": "string", "minLength": 1},
            "sets": {
                "type": "array",
                "uniqueItems": True,
                "items": {"type": "string", "minLength": 1},
            },
            "characters": {
                "type": "array",
                "uniqueItems": True,
                "items": {"type": "string", "minLength": 1},
            },
            "validated": {"type": "boolean"},
            "components": SCHEMA["properties"]["components"],
            "channels": SCHEMA["properties"]["channels"],
        },
        "required": ["format", "version", "id", "game_version", "sets"],
    }
    errors = sorted(
        Draft202012Validator(schema).iter_errors(document),
        key=lambda error: str(error.path),
    )
    if errors:
        raise LibraryError(errors[0].message)
    _finite(document)
    components = _components(document.get("components", {}))
    channels = _channels(document.get("channels", {}))
    return Mechanics(
        cast(str, document["id"]),
        cast(str, document["game_version"]),
        frozenset(cast(list[str], document["sets"])),
        frozenset(cast(list[str], document.get("characters", []))),
        components,
        channels,
        cast(bool, document.get("validated", False)),
    )
