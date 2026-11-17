import pytest

from artifact_sort.deletion_objective import TargetPerformance, summarize_losses


def target(identity, category, loss, family="one"):
    return TargetPerformance(identity, family, category, 100, 100 * (1 - loss))


def test_pattern_and_authoring_counts_do_not_multiply_category_or_family_weight():
    targets = [target("current", "current", 0.3)]
    targets += [target(f"ordinary-{i}", "ordinary", 0.6) for i in range(31)]
    targets += [target(f"strong-{i}", "strong", 0) for i in range(31)]
    targets += [
        target(f"other-{category}", category, 0, "two")
        for category in ("current", "ordinary", "strong")
    ]
    result = summarize_losses(targets)
    assert result.worst_loss == pytest.approx(0.6)
    assert result.family_average == pytest.approx(0.15)
    assert not result.gaps


def test_exceptional_losses_cannot_change_primary_objectives():
    targets = [
        target(category, category, 0.1)
        for category in ("current", "ordinary", "strong")
    ]
    original = summarize_losses(targets)
    with_exceptional = summarize_losses(
        [*targets, target("exceptional", "exceptional", 0.9)]
    )
    assert original.worst_loss == with_exceptional.worst_loss
    assert original.family_average == with_exceptional.family_average
    assert with_exceptional.exceptional_worst_loss == pytest.approx(0.9)
    unknown = summarize_losses(
        [*targets, TargetPerformance("unknown", "one", "exceptional", None, None)]
    )
    assert unknown.worst_loss == original.worst_loss
    assert unknown.exceptional_worst_loss is None
    assert unknown.gaps


@pytest.mark.parametrize(
    "baseline,retained,gap",
    [
        (None, 10, "unresolved_or_absent_baseline"),
        (10, None, "unresolved_retained_performance"),
        (10, 11, "retained_exceeds_baseline"),
    ],
)
def test_uncertain_or_invalid_ratios_are_visible_and_do_not_rank_selections(
    baseline, retained, gap
):
    targets = [
        TargetPerformance("current", "one", "current", baseline, retained),
        target("ordinary", "ordinary", 0),
        target("strong", "strong", 0),
    ]
    result = summarize_losses(targets)
    assert result.worst_loss is result.family_average is None
    assert result.targets[0].loss is None
    assert result.targets[0].gap == gap


def test_proven_zero_retained_performance_is_full_loss_for_positive_baseline():
    result = summarize_losses(
        [
            target(category, category, 1)
            for category in ("current", "ordinary", "strong")
        ]
    )
    assert result.worst_loss == result.family_average == 1


def test_only_measurable_categories_receive_equal_shares():
    result = summarize_losses([target("current", "current", 0.1)])
    assert result.family_average == pytest.approx(0.1)
    assert not result.gaps


@pytest.mark.parametrize("baseline", [0, -10])
def test_nonpositive_baselines_are_reported_and_excluded(baseline):
    result = summarize_losses(
        [
            TargetPerformance("absent", "one", "current", baseline, None),
            target("ordinary", "ordinary", 0.2),
            target("strong", "strong", 0.6),
            TargetPerformance("empty-family", "empty", "strong", 0, 0),
            TargetPerformance("exceptional-empty", "one", "exceptional", 0, 0),
            target("exceptional", "exceptional", 0.9),
        ]
    )
    assert result.worst_loss == pytest.approx(0.6)
    assert result.family_average == pytest.approx(0.4)
    assert result.exceptional_worst_loss == pytest.approx(0.9)
    assert result.targets[0].loss is None
    assert result.targets[0].gap == "nonpositive_baseline"
    assert len(result.gaps) == 3
