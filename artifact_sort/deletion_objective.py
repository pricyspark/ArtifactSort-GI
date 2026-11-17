"""Explicit losses and equal-category, family-balanced deletion objectives.

This computes objectives from supplied performance evidence. It does not certify
search results, infer families, or decide coverage protections for missing data.
"""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Literal, Sequence

Category = Literal["current", "ordinary", "strong", "exceptional"]
PRIMARY_CATEGORIES = ("current", "ordinary", "strong")


@dataclass(frozen=True, slots=True)
class TargetPerformance:
    id: str
    family: str
    category: Category
    baseline: float | None
    retained: float | None


@dataclass(frozen=True, slots=True)
class TargetLoss:
    target: TargetPerformance
    loss: float | None
    gap: str | None


@dataclass(frozen=True, slots=True)
class DeletionObjective:
    targets: tuple[TargetLoss, ...]
    worst_loss: float | None
    family_average: float | None
    exceptional_worst_loss: float | None
    gaps: tuple[str, ...]


def summarize_losses(targets: Sequence[TargetPerformance]) -> DeletionObjective:
    """Average contexts within category, categories within family, then families.

    Only positive baselines contribute. Average the measurable categories in
    each family equally; report excluded targets without assigning zero loss. Known
    worst loss is insufficient to rank selections when another target is unknown.
    Exceptional evidence is separate and cannot alter either primary objective.
    """
    if not targets or len({target.id for target in targets}) != len(targets):
        raise ValueError("targets must be nonempty and have unique identities")
    losses = []
    primary: dict[str, dict[str, list[float]]] = {}
    exceptional = []
    primary_gaps = []
    gaps = []
    for target in targets:
        if (
            not target.id
            or not target.family
            or target.category not in (*PRIMARY_CATEGORIES, "exceptional")
        ):
            raise ValueError(
                "every target needs an identity, explicit family, and valid category"
            )
        if any(
            value is not None and not math.isfinite(value)
            for value in (target.baseline, target.retained)
        ):
            raise ValueError(f"{target.id}: performance must be finite or unresolved")
        gap = None
        loss = None
        if target.baseline is None:
            gap = "unresolved_or_absent_baseline"
        elif target.baseline <= 0:
            gap = "nonpositive_baseline"
        elif target.retained is None:
            gap = "unresolved_retained_performance"
        elif target.retained > target.baseline:
            gap = "retained_exceeds_baseline"
        else:
            loss = 1 - target.retained / target.baseline
        losses.append(TargetLoss(target, loss, gap))
        if gap:
            gaps.append(f"{target.id}: {gap}")
        if gap == "nonpositive_baseline":
            continue
        if target.category == "exceptional":
            exceptional.append(loss)
        else:
            categories = primary.setdefault(target.family, {})
            values = categories.setdefault(target.category, [])
            if loss is None:
                primary_gaps.append(target.id)
            else:
                values.append(loss)
    if not primary:
        primary_gaps.append("no_primary_families")
        gaps.append("no_primary_families")
    worst = average = None
    if not primary_gaps:
        worst = max(
            value
            for categories in primary.values()
            for values in categories.values()
            for value in values
        )
        average = math.fsum(
            math.fsum(math.fsum(values) / len(values) for values in categories.values())
            / len(categories)
            for categories in primary.values()
        ) / len(primary)
    exceptional_worst = None
    if exceptional and all(value is not None for value in exceptional):
        exceptional_worst = max(value for value in exceptional if value is not None)
    return DeletionObjective(
        tuple(losses), worst, average, exceptional_worst, tuple(gaps)
    )
