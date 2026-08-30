from __future__ import annotations

import argparse
from dataclasses import asdict, is_dataclass
from hashlib import sha256
import json
from pathlib import Path
import shlex
from typing import Any, Mapping, Sequence

import numpy as np

from .cache import ResultCache, cache_key
from .farming import (
    DefinitionSpec,
    FarmConfig,
    ReshapeSpec,
    analyze_materials,
    simulate_farming,
)
from .model import load_good
from .optimizer import BuildOptimizer, DeletionAnalyzer
from .scenarios import (
    BuiltinEvaluator,
    Scenario,
    generic_scenarios,
    load_scenarios,
    scenario_to_mapping,
)
from .simulation import (
    CritValuePolicy,
    CritValueUpgradePolicy,
    ArchetypeWeightPolicy,
    PortfolioDeletionPolicy,
    PortfolioUpgradePolicy,
    RandomDeletionPolicy,
    RandomUpgradePolicy,
    RecordedDeletionPolicy,
    StaticWeightPolicy,
    benchmark_deletion,
    benchmark_upgrades,
)
from .sources import GOEvaluator, akasha_scenarios, import_akasha, import_go
from .upgrades import UpgradeAnalyzer


def _jsonable(value: object) -> object:
    if is_dataclass(value) and not isinstance(value, type):
        return _jsonable(asdict(value))
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, Mapping):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_jsonable(item) for item in value]
    if isinstance(value, float) and not np.isfinite(value):
        return None
    return value


def _emit(value: object, output: str | None = None) -> None:
    payload = json.dumps(_jsonable(value), indent=2, sort_keys=True)
    if output:
        Path(output).write_text(payload + "\n", encoding="utf-8")
    else:
        print(payload)


def _scenario_inputs(values: Sequence[str] | None) -> list[Scenario]:
    if not values:
        return generic_scenarios()
    scenarios: list[Scenario] = []
    for value in values:
        if value == "generic":
            scenarios.extend(generic_scenarios())
        else:
            scenarios.extend(load_scenarios(value))
    ids: set[str] = set()
    unique = []
    for scenario in scenarios:
        if scenario.id not in ids:
            ids.add(scenario.id)
            unique.append(scenario)
    return unique


def _evaluator_and_scenarios(
    scenarios: Sequence[Scenario], adapter_command: str | None
) -> tuple[BuiltinEvaluator | GOEvaluator, list[Scenario], list[str]]:
    exact_go = [scenario for scenario in scenarios if scenario.metadata.get("adapter_required")]
    warnings: list[str] = []
    if adapter_command:
        if len(exact_go) != len(scenarios):
            raise ValueError("a GO adapter run cannot currently mix GO and built-in scenarios")
        return GOEvaluator(shlex.split(adapter_command)), list(scenarios), warnings
    exact_ids = {id(scenario) for scenario in exact_go}
    enabled = [scenario for scenario in scenarios if id(scenario) not in exact_ids]
    if exact_go:
        warnings.append(
            "disabled GO scenarios requiring the pinned GO evaluator: "
            + ", ".join(scenario.id for scenario in exact_go)
        )
    if not enabled:
        raise ValueError(
            "all selected scenarios require --go-adapter; no formula was approximated"
        )
    return BuiltinEvaluator(), enabled, warnings


def _scenario_hash(scenarios: Sequence[Scenario]) -> str:
    payload = [scenario_to_mapping(scenario) for scenario in scenarios]
    return sha256(json.dumps(payload, sort_keys=True, default=str).encode()).hexdigest()


def _cached(
    namespace: str,
    batch_fingerprint: str,
    scenarios: Sequence[Scenario],
    evaluator: BuiltinEvaluator | GOEvaluator,
    parameters: Mapping[str, object],
    cache_path: str | None,
    compute: Any,
) -> object:
    if cache_path is None:
        return compute()
    cache = ResultCache(cache_path)
    key = cache_key(
        artifact_fingerprint=batch_fingerprint,
        scenario_hash=_scenario_hash(scenarios),
        evaluator_version=evaluator.version,
        parameters=parameters,
    )
    found = cache.get(namespace, key)
    if found is not None:
        return found
    result = _jsonable(compute())
    cache.put(namespace, key, result)
    return result


def _command_import_go(args: argparse.Namespace) -> None:
    scenarios = import_go(args.team_export)
    _emit(
        {
            "format": "artifact-sort-scenarios",
            "version": 1,
            "scenarios": [scenario_to_mapping(scenario) for scenario in scenarios],
        },
        args.output,
    )


def _command_import_akasha(args: argparse.Namespace) -> None:
    snapshot = import_akasha(args.snapshot)
    _emit(
        {
            "format": "artifact-sort-akasha-snapshot",
            "version": snapshot.version,
            "builds": snapshot.builds,
            "scenarios": [
                scenario_to_mapping(scenario) for scenario in akasha_scenarios(snapshot)
            ],
        },
        args.output,
    )


def _analysis(args: argparse.Namespace) -> tuple[object, dict[str, Any], list[Scenario], object, list[str]]:
    batch, data = load_good(args.good)
    requested = _scenario_inputs(args.scenarios)
    evaluator, scenarios, warnings = _evaluator_and_scenarios(
        requested, getattr(args, "go_adapter", None)
    )
    return batch, data, scenarios, evaluator, warnings


def _command_delete(args: argparse.Namespace) -> None:
    batch, _, scenarios, evaluator, warnings = _analysis(args)
    optimizer = BuildOptimizer(
        batch,
        evaluator,
        candidate_limit=args.candidate_limit,
        beam_width=args.beam_width,
    )

    def compute() -> object:
        option_values = None
        if not args.no_protect_unfinished:
            option_values = UpgradeAnalyzer(
                optimizer,
                scenarios,
                probability_floor=args.probability_floor,
                complement_pool_size=args.upgrade_pool,
            ).option_values(max_candidates=args.upgrade_candidates)
        return DeletionAnalyzer(
            optimizer, scenarios, loadouts_per_scenario=args.loadouts
        ).analyze(args.free, pinned_ids=args.pin, option_values=option_values)

    result = _cached(
        "delete",
        batch.fingerprint(),
        scenarios,
        evaluator,
        {
            "free": args.free,
            "pin": args.pin,
            "probability_floor": args.probability_floor,
            "protect_unfinished": not args.no_protect_unfinished,
            "candidate_limit": args.candidate_limit,
            "beam_width": args.beam_width,
            "loadouts": args.loadouts,
        },
        args.cache,
        compute,
    )
    _emit(
        {
            "warnings": warnings,
            "trust": {
                "status": "unvalidated",
                "reason": (
                    "run benchmark-policy against calibration and held-out scenarios "
                    "before treating deletion analysis as a recommendation"
                ),
            },
            "result": result,
        },
        args.output,
    )


def _command_upgrades(args: argparse.Namespace) -> None:
    batch, _, scenarios, evaluator, warnings = _analysis(args)
    optimizer = BuildOptimizer(
        batch, evaluator, candidate_limit=args.candidate_limit, beam_width=args.beam_width
    )
    result = _cached(
        "upgrades",
        batch.fingerprint(),
        scenarios,
        evaluator,
        {
            "epsilon": args.epsilon,
            "probability_floor": args.probability_floor,
            "max_candidates": args.max_candidates,
        },
        args.cache,
        lambda: UpgradeAnalyzer(
            optimizer,
            scenarios,
            epsilon=args.epsilon,
            probability_floor=args.probability_floor,
            complement_pool_size=args.complement_pool,
        ).analyze(max_candidates=args.max_candidates),
    )
    _emit({"warnings": warnings, "recommendations": result}, args.output)


def _command_farm(args: argparse.Namespace) -> None:
    batch, _, scenarios, _, warnings = _analysis(args)
    config = FarmConfig(
        domain_sets=(args.domain_set[0], args.domain_set[1]),
        max_resin=args.max_resin,
        strongbox=not args.no_strongbox,
        check_every_drops=args.check_every,
    )
    definitions = [
        DefinitionSpec(values[0], values[1], values[2], (values[3], values[4]))
        for values in args.define
    ]
    reshapes = [
        ReshapeSpec(values[0], int(values[1])) for values in args.reshape
    ]
    result = simulate_farming(
        batch,
        scenarios,
        increase=args.increase,
        config=config,
        trials=args.trials,
        seed=args.seed,
        definitions=definitions,
        reshapes=reshapes,
    )
    _emit({"warnings": warnings, "result": result}, args.output)


def _command_materials(args: argparse.Namespace) -> None:
    batch, data = load_good(args.good)
    _emit(analyze_materials(batch, data), args.output)


def _load_recorded_order(path: str | None) -> list[str] | None:
    if path is None:
        return None
    with Path(path).open(encoding="utf-8") as handle:
        data = json.load(handle)
    values = data.get("deleted_ids", data) if isinstance(data, Mapping) else data
    if not isinstance(values, list):
        raise ValueError("recorded order must be a JSON array or contain deleted_ids")
    return [str(value) for value in values]


def _command_benchmark(args: argparse.Namespace) -> None:
    batch, _, calibration, _, warnings = _analysis(args)
    heldout = _scenario_inputs(args.heldout) if args.heldout else []
    recorded = _load_recorded_order(args.recorded_order)
    if args.kind == "deletion":
        policies = [
            RandomDeletionPolicy(),
            CritValuePolicy(),
            ArchetypeWeightPolicy(),
            StaticWeightPolicy(),
        ]
        if recorded:
            policies.append(RecordedDeletionPolicy(recorded))
        policies.extend(
            PortfolioDeletionPolicy(probability_floor=floor)
            for floor in (0.001, 0.01, 0.05)
        )
        result = benchmark_deletion(
            batch,
            calibration,
            heldout,
            policies,
            free=args.free,
            trials=args.trials,
            seed=args.seed,
        )
    else:
        result = benchmark_upgrades(
            batch,
            tuple(calibration) + tuple(heldout),
            [RandomUpgradePolicy(), CritValueUpgradePolicy(), PortfolioUpgradePolicy()],
            trials=args.trials,
            seed=args.seed,
            progress_target=args.increase,
            max_checkpoints=args.max_checkpoints,
            resin_per_exp=args.resin_per_exp,
        )
    _emit({"warnings": warnings, "result": result}, args.output)


def _add_scenarios(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--scenarios",
        nargs="+",
        help="scenario JSON/TOML paths or 'generic' (default: generated envelope)",
    )
    parser.add_argument("--go-adapter", help="quoted local GO adapter command")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="artifact-sort")
    subparsers = parser.add_subparsers(dest="command", required=True)

    import_go_parser = subparsers.add_parser("import-go")
    import_go_parser.add_argument("team_export")
    import_go_parser.add_argument("--output")
    import_go_parser.set_defaults(func=_command_import_go)

    import_akasha_parser = subparsers.add_parser("import-akasha")
    import_akasha_parser.add_argument("snapshot")
    import_akasha_parser.add_argument("--output")
    import_akasha_parser.set_defaults(func=_command_import_akasha)

    delete_parser = subparsers.add_parser("delete")
    delete_parser.add_argument("good")
    _add_scenarios(delete_parser)
    delete_parser.add_argument("--free", type=int, required=True)
    delete_parser.add_argument("--pin", action="append", default=[])
    delete_parser.add_argument("--probability-floor", type=float, default=0.01)
    delete_parser.add_argument("--no-protect-unfinished", action="store_true")
    delete_parser.add_argument("--upgrade-candidates", type=int, default=32)
    delete_parser.add_argument("--upgrade-pool", type=int, default=100)
    delete_parser.add_argument("--candidate-limit", type=int, default=36)
    delete_parser.add_argument("--beam-width", type=int, default=6000)
    delete_parser.add_argument("--loadouts", type=int, default=80)
    delete_parser.add_argument("--cache", default=".artifact-sort/cache.sqlite")
    delete_parser.add_argument("--output")
    delete_parser.set_defaults(func=_command_delete)

    upgrade_parser = subparsers.add_parser("upgrades")
    upgrade_parser.add_argument("good")
    _add_scenarios(upgrade_parser)
    upgrade_parser.add_argument("--epsilon", type=float, default=0.01)
    upgrade_parser.add_argument("--probability-floor", type=float, default=0.01)
    upgrade_parser.add_argument("--max-candidates", type=int, default=24)
    upgrade_parser.add_argument("--complement-pool", type=int, default=160)
    upgrade_parser.add_argument("--candidate-limit", type=int, default=32)
    upgrade_parser.add_argument("--beam-width", type=int, default=4000)
    upgrade_parser.add_argument("--cache", default=".artifact-sort/cache.sqlite")
    upgrade_parser.add_argument("--output")
    upgrade_parser.set_defaults(func=_command_upgrades)

    farm_parser = subparsers.add_parser("farm")
    farm_parser.add_argument("good")
    _add_scenarios(farm_parser)
    farm_parser.add_argument("--increase", type=float, required=True)
    farm_parser.add_argument("--domain-set", nargs=2, default=("DomainSetA", "DomainSetB"))
    farm_parser.add_argument("--trials", type=int, default=100)
    farm_parser.add_argument("--seed", type=int, default=0)
    farm_parser.add_argument("--max-resin", type=int, default=100_000)
    farm_parser.add_argument("--check-every", type=int, default=10)
    farm_parser.add_argument("--no-strongbox", action="store_true")
    farm_parser.add_argument(
        "--define",
        nargs=5,
        action="append",
        default=[],
        metavar=("SET", "SLOT", "MAIN", "SUB1", "SUB2"),
    )
    farm_parser.add_argument(
        "--reshape",
        nargs=2,
        action="append",
        default=[],
        metavar=("ARTIFACT_ID", "ATTEMPTS"),
    )
    farm_parser.add_argument("--output")
    farm_parser.set_defaults(func=_command_farm)

    material_parser = subparsers.add_parser("materials")
    material_parser.add_argument("good")
    material_parser.add_argument("--output")
    material_parser.set_defaults(func=_command_materials)

    benchmark_parser = subparsers.add_parser("benchmark-policy")
    benchmark_parser.add_argument("good")
    _add_scenarios(benchmark_parser)
    benchmark_parser.add_argument("--heldout", nargs="+")
    benchmark_parser.add_argument("--kind", choices=("deletion", "upgrade"), default="deletion")
    benchmark_parser.add_argument("--free", type=int, default=20)
    benchmark_parser.add_argument("--increase", type=float, default=0.05)
    benchmark_parser.add_argument("--trials", type=int, default=20)
    benchmark_parser.add_argument("--seed", type=int, default=0)
    benchmark_parser.add_argument(
        "--recorded-order",
        help="JSON artifact-ID ordering from any external policy to replay",
    )
    benchmark_parser.add_argument("--max-checkpoints", type=int, default=300)
    benchmark_parser.add_argument("--resin-per-exp", type=float)
    benchmark_parser.add_argument("--output")
    benchmark_parser.set_defaults(func=_command_benchmark)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        args.func(args)
    except (ValueError, RuntimeError) as exc:
        parser.error(str(exc))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
