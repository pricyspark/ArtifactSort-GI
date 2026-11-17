"""Shared legal contexts from current gear and independent hypothetical builds."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
import math
from time import monotonic
from typing import TYPE_CHECKING, Literal

from .artifact_sampling import SamplingRules, sample_slot
from .inventory import Artifact, Inventory
from .library_runtime import CompiledScenario, Linearization
from .library_search import SearchResult, search_builds
from .model import SLOT_KEYS

if TYPE_CHECKING:
    from .library_cache import AnalysisCache


@dataclass(frozen=True, slots=True)
class ReferenceContext:
    source: Literal["inventory", "hypothetical"]
    inventory: Inventory
    linearization: Linearization


@dataclass(frozen=True, slots=True)
class ContextPortfolio:
    contexts: tuple[ReferenceContext, ...]
    inventory_search: SearchResult
    hypothetical_search: SearchResult
    sampling_fingerprint: str
    sampling_validated: bool


def generate_reference_contexts(
    inventory: Inventory,
    scenario: CompiledScenario,
    rules: SamplingRules,
    *,
    population_per_set_slot: int = 32,
    top_k: int = 8,
    max_evaluations: int = 100_000,
    time_limit: float | None = None,
    seed: int = 0,
    cache: AnalysisCache | None = None,
) -> ContextPortfolio:
    """Freeze contexts from both sources before comparing any deletion sets.

    Hypothetical candidate sampling covers all known sets and does not depend
    on owned pieces. Missing inventory builds therefore cannot remove that
    source of contexts. Exact search of a sampled pool is still approximate
    coverage of the possible hypothetical builds, not proof of global failure.
    Counts are calibration parameters, not accuracy guarantees. This initial
    portfolio retains discovered representatives of main assignments, activated
    effects, and set strategies without a stat-distance threshold. It cannot
    certify coverage of unseen numerical regimes or future stat allocations.
    """
    if type(population_per_set_slot) is not int or population_per_set_slot <= 0:
        raise ValueError("population_per_set_slot must be a positive integer")
    if type(top_k) is not int or top_k <= 0:
        raise ValueError("top_k must be a positive integer")
    if type(max_evaluations) is not int or max_evaluations <= 0:
        raise ValueError("max_evaluations must be a positive integer")
    if type(seed) is not int:
        raise ValueError("seed must be an integer")
    if time_limit is not None and (not math.isfinite(time_limit) or time_limit <= 0):
        raise ValueError("time_limit must be finite and positive")
    # Separate equal source budgets prevent one source from consuming the whole
    # deadline. The hypothetical budget includes population generation.
    source_limit = None if time_limit is None else time_limit / 2
    current = search_builds(
        inventory,
        scenario,
        top_k=top_k,
        max_evaluations=max_evaluations,
        time_limit=source_limit,
        seed=seed,
        collect_contexts=True,
        cache=cache,
    )
    deadline = math.inf if source_limit is None else monotonic() + source_limit
    pieces: list[Artifact] = []
    stopped = False
    for set_key in sorted(scenario.known_sets):
        for slot in SLOT_KEYS:
            if monotonic() >= deadline:
                stopped = True
                break
            payload = json.dumps(
                ["hypothetical-contexts-1", seed, scenario.definition.id, set_key, slot]
            )
            sample_seed = int.from_bytes(sha256(payload.encode()).digest(), "big")
            pieces.extend(
                (sample_slot if cache is None else cache.population)(
                    slot, set_key, population_per_set_slot, rules, seed=sample_seed
                ).artifacts
            )
        if stopped:
            break
    candidates = Inventory(tuple(pieces))
    remaining = deadline - monotonic()
    if remaining <= 0:
        hypothetical = SearchResult((), "timed_out", 0, 0)
    else:
        found = search_builds(
            candidates,
            scenario,
            top_k=top_k,
            max_evaluations=max_evaluations,
            time_limit=None if source_limit is None else remaining,
            seed=seed,
            collect_contexts=True,
            cache=cache,
        )
        hypothetical = SearchResult(
            found.builds,
            "timed_out" if found.status == "timed_out" else "approximate",
            found.evaluated,
            found.combinations,
            found.context_builds,
        )
    contexts = []
    sources: tuple[
        tuple[Literal["inventory", "hypothetical"], Inventory, SearchResult], ...
    ] = (("inventory", inventory, current), ("hypothetical", candidates, hypothetical))
    for source, pool, search in sources:
        by_id = {a.id: a for a in pool.artifacts}
        for result in search.context_builds or search.builds:
            context = Inventory(tuple(by_id[key] for key in result.build.artifact_ids))
            local = scenario.linearize(
                result.build.stats,
                result.build.set_counts,
                main_stats=result.build.main_stats,
            )
            contexts.append(ReferenceContext(source, context, local))
    return ContextPortfolio(
        tuple(contexts), current, hypothetical, rules.fingerprint, rules.validated
    )
