# ABOUTME: TDD tests for the algorithm-specific metric definition + observation
# ABOUTME: contract (workspace-hub#3432): single-algorithm scope, immutable versioned
# ABOUTME: definitions, closed quality_state enum, fail-closed population, no cross-algo equivalence.
"""Algorithm-specific metric definition + observation contract tests (no engine dependency).

These pin the normative rules from the on-main
``docs/architecture/algorithm-run-dataset-contract.yaml`` ``records.metric_definition``
+ ``records.metric_observation`` + ``metrics`` + ``failure_policy`` blocks and the
approved+remediated #3432 plan:

- A MetricDefinition carries metric_id, algorithm_id, definition_version, label,
  meaning, unit_or_dimension, data_type, derivation, applicability, directionality
  (ALWAYS present -- explicit ``"none"`` when not meaningful) and quality_rule.
- ``metric_id`` MUST be whole-prefix-owned by its ``algorithm_id`` (a workflow_id may
  itself contain ``/``); exactly ONE algorithm owns a metric_id.
- ``metric_definition_id`` is a digest binding metric_id + algorithm_id +
  definition_version + the body; immutable once published (a changed field on an
  existing (metric_id, definition_version) fails closed; new semantics -> new version).
- Definitions are versioned INDEPENDENTLY of observations; a historical observation
  retains the EXACT definition_version it used.
- ``quality_state`` is a closed 4-value enum (valid | not_applicable | invalid |
  missing) keeping not-applicable, null and numeric-zero mutually DISTINCT.
- Population is fail-closed: only terminal ``succeeded`` + ``valid`` + matching
  algorithm owner + a validating definition_version enters metrics; failed runs are
  excluded from metrics AND insights AND decisions.
- No cross-algorithm equivalence (Phase-1 non-goal): relating two algorithms' metrics
  is rejected.
"""

from __future__ import annotations

import pytest

from assetutilities.workflow_api import identity, metrics


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _def_kwargs(**over) -> dict:
    base = dict(
        metric_id="team/wave/algo1/rmse",
        algorithm_id="team/wave/algo1",
        definition_version="1.0.0",
        label="Root mean squared error",
        meaning="RMSE of predicted vs measured response for algo1.",
        unit_or_dimension="m",
        data_type="scalar",
        derivation="ref:derivations/rmse@1",
        applicability="rule:applies_when_response_present",
        directionality="lower_is_better",
        quality_rule="rule:reject_if_nan_or_negative",
    )
    base.update(over)
    return base


def _definition(**over) -> dict:
    return metrics.make_metric_definition(**_def_kwargs(**over))


def _observation(definition, **over) -> dict:
    kwargs = dict(
        run_id="run-" + "a" * 8,
        value=1.5,
        quality_state="valid",
        derivation_evidence="ref:evidence/run-aaaaaaaa/rmse",
        uncertainty=None,
    )
    kwargs.update(over)
    return metrics.make_metric_observation(definition=definition, **kwargs)


# ---------------------------------------------------------------------------
# 1. required fields + directionality always present
# ---------------------------------------------------------------------------

def test_metric_definition_carries_all_required_fields():
    d = _definition()
    for field in (
        "metric_id",
        "algorithm_id",
        "definition_version",
        "label",
        "meaning",
        "unit_or_dimension",
        "data_type",
        "derivation",
        "applicability",
        "directionality",
        "quality_rule",
    ):
        assert field in d and d[field] is not None
    # digest identity is present and deterministic.
    assert d["metric_definition_id"] == _definition()["metric_definition_id"]

    # Omitting ANY contract-required field fails closed.
    for field in metrics.REQUIRED_DEFINITION_FIELDS:
        bad = _def_kwargs()
        bad.pop(field)
        with pytest.raises(metrics.MetricsError):
            metrics.make_metric_definition(**bad)

    # directionality is ALWAYS required and must be explicit (never None/absent);
    # when not meaningful it is the explicit token "none", not omission.
    with pytest.raises(metrics.MetricsError):
        metrics.make_metric_definition(**_def_kwargs(directionality=None))
    none_dir = _definition(
        metric_id="team/wave/algo1/category", data_type="categorical",
        unit_or_dimension="NA", directionality="none",
    )
    assert none_dir["directionality"] == "none"


# ---------------------------------------------------------------------------
# 2. whole-prefix ownership (workflow_id may contain '/')
# ---------------------------------------------------------------------------

def test_metric_id_prefixed_by_algorithm_id_whole_prefix():
    # algorithm_id itself contains '/', and the metric_id extends it by a '/'-segment.
    ok = _definition(
        algorithm_id="team/wave/algo1", metric_id="team/wave/algo1/precision"
    )
    assert ok["algorithm_id"] == "team/wave/algo1"

    # Wrong prefix: shares a leading string but not on a segment boundary -> reject.
    with pytest.raises(metrics.MetricsError):
        metrics.make_metric_definition(
            **_def_kwargs(algorithm_id="team/wave/algo1",
                          metric_id="team/wave/algo1x/precision")
        )
    # Unrelated prefix -> reject.
    with pytest.raises(metrics.MetricsError):
        metrics.make_metric_definition(
            **_def_kwargs(algorithm_id="team/wave/algo1",
                          metric_id="other/algo/precision")
        )
    # metric_id equal to algorithm_id (no metric segment) -> reject.
    with pytest.raises(metrics.MetricsError):
        metrics.make_metric_definition(
            **_def_kwargs(algorithm_id="team/wave/algo1",
                          metric_id="team/wave/algo1")
        )


# ---------------------------------------------------------------------------
# 3. exactly one algorithm owner per metric_id
# ---------------------------------------------------------------------------

def test_single_algorithm_owner_per_metric_id():
    store = metrics.MetricDefinitionStore()
    # A parent algorithm and a child whose id extends the parent: the SAME
    # metric_id "team/wave/algo/sub/m" is a valid whole-prefix of both, but only
    # ONE may own it (definition_owner_cardinality == 1).
    d_child = metrics.make_metric_definition(
        **_def_kwargs(algorithm_id="team/wave/algo/sub",
                      metric_id="team/wave/algo/sub/m")
    )
    store.register(d_child)
    d_parent = metrics.make_metric_definition(
        **_def_kwargs(algorithm_id="team/wave/algo",
                      metric_id="team/wave/algo/sub/m")
    )
    with pytest.raises(metrics.MetricsError):
        store.register(d_parent)


# ---------------------------------------------------------------------------
# 4. immutability once published
# ---------------------------------------------------------------------------

def test_definition_version_is_immutable_once_published():
    store = metrics.MetricDefinitionStore()
    v1 = _definition()
    store.register(v1)
    # Idempotent re-register of the identical body is fine.
    again = store.register(_definition())
    assert again["metric_definition_id"] == v1["metric_definition_id"]

    # ANY changed field on the SAME (metric_id, definition_version) fails closed.
    changed = _definition(meaning="a materially different meaning")
    assert changed["metric_definition_id"] != v1["metric_definition_id"]
    with pytest.raises(metrics.MetricsError):
        store.register(changed)

    # A semantic change MUST mint a NEW definition_version -> accepted, appended.
    v2 = _definition(definition_version="2.0.0",
                     meaning="a materially different meaning")
    store.register(v2)
    assert set(store.versions("team/wave/algo1/rmse")) == {"1.0.0", "2.0.0"}


# ---------------------------------------------------------------------------
# 5. independent versioning: history retained
# ---------------------------------------------------------------------------

def test_definitions_versioned_independently_history_retained():
    store = metrics.MetricDefinitionStore()
    v1 = _definition(definition_version="1.0.0")
    store.register(v1)
    obs = _observation(v1)
    assert obs["metric_definition_version"] == "1.0.0"
    assert obs["metric_definition_id"] == v1["metric_definition_id"]

    # Publishing a new version does NOT mutate the past observation or lose v1.
    v2 = _definition(definition_version="2.0.0", unit_or_dimension="mm")
    store.register(v2)
    assert obs["metric_definition_version"] == "1.0.0"
    assert obs["metric_definition_id"] == v1["metric_definition_id"]
    assert store.get("team/wave/algo1/rmse", "1.0.0")["metric_definition_id"] == v1[
        "metric_definition_id"
    ]
    assert store.get("team/wave/algo1/rmse", "2.0.0")["unit_or_dimension"] == "mm"


# ---------------------------------------------------------------------------
# 6. observation binds run + exact definition_version
# ---------------------------------------------------------------------------

def test_observation_binds_run_and_definition_version():
    d = _definition()
    obs = _observation(d, run_id="run-12345678")
    assert obs["run_id"] == "run-12345678"
    assert obs["metric_definition_version"] == d["definition_version"]
    assert obs["metric_definition_id"] == d["metric_definition_id"]
    assert obs["algorithm_id"] == d["algorithm_id"]
    # observation identity binds the run + the exact definition version.
    assert obs["metric_observation_id"] == _observation(d, run_id="run-12345678")[
        "metric_observation_id"
    ]
    assert obs["metric_observation_id"] != _observation(d, run_id="run-99999999")[
        "metric_observation_id"
    ]


# ---------------------------------------------------------------------------
# 7. closed quality_state enum: NA vs null vs numeric-zero distinct
# ---------------------------------------------------------------------------

def test_quality_state_enum_distinguishes_na_null_zero():
    d = _definition()
    assert metrics.QUALITY_STATES == frozenset(
        {"valid", "not_applicable", "invalid", "missing"}
    )
    # A real measured ZERO is a VALID value, not "no value".
    zero = _observation(d, value=0, quality_state="valid")
    na = _observation(d, value=None, quality_state="not_applicable")
    missing = _observation(d, value=None, quality_state="missing")
    assert zero["value"] == 0 and zero["quality_state"] == "valid"
    assert na["quality_state"] == "not_applicable" and na["value"] is None
    assert missing["quality_state"] == "missing" and missing["value"] is None
    # All three states are mutually distinct.
    assert len({zero["quality_state"], na["quality_state"], missing["quality_state"]}) == 3

    # An out-of-enum quality_state fails closed.
    with pytest.raises(metrics.MetricsError):
        _observation(d, quality_state="bogus")
    # valid REQUIRES a present value (so numeric-zero != missing/NA cannot collapse).
    with pytest.raises(metrics.MetricsError):
        _observation(d, value=None, quality_state="valid")
    # not_applicable / missing MUST NOT smuggle a numeric value.
    with pytest.raises(metrics.MetricsError):
        _observation(d, value=0, quality_state="not_applicable")
    with pytest.raises(metrics.MetricsError):
        _observation(d, value=0, quality_state="missing")


# ---------------------------------------------------------------------------
# 8. only succeeded + valid + owner-matched + validating-version enter population
# ---------------------------------------------------------------------------

def test_only_succeeded_valid_owner_matched_enter_population():
    store = metrics.MetricDefinitionStore()
    d = _definition()
    store.register(d)
    obs = _observation(d)

    # All four conditions satisfied -> eligible.
    assert metrics.population_eligible(
        terminal_status="succeeded",
        run_algorithm_id=d["algorithm_id"],
        observation=obs,
        store=store,
    ) is True

    # (a) non-succeeded terminal status -> excluded.
    assert not metrics.population_eligible(
        terminal_status="reproducible_failure",
        run_algorithm_id=d["algorithm_id"], observation=obs, store=store,
    )
    # (b) non-valid quality_state -> excluded.
    assert not metrics.population_eligible(
        terminal_status="succeeded", run_algorithm_id=d["algorithm_id"],
        observation=_observation(d, value=None, quality_state="missing"), store=store,
    )
    # (c) run's algorithm owner mismatch -> excluded.
    assert not metrics.population_eligible(
        terminal_status="succeeded", run_algorithm_id="team/wave/other",
        observation=obs, store=store,
    )
    # (d) definition_version not registered / not validating -> excluded.
    unregistered = metrics.MetricDefinitionStore()
    assert not metrics.population_eligible(
        terminal_status="succeeded", run_algorithm_id=d["algorithm_id"],
        observation=obs, store=unregistered,
    )


# ---------------------------------------------------------------------------
# 9. failed run excluded from metrics AND insights AND decisions
# ---------------------------------------------------------------------------

def test_failed_run_excluded_from_metrics_insights_decisions():
    for surface in ("metrics", "insights", "decisions"):
        assert metrics.assert_population_admissible("succeeded", surface) is True
        with pytest.raises(metrics.MetricsError):
            metrics.assert_population_admissible("reproducible_failure", surface)
        with pytest.raises(metrics.MetricsError):
            metrics.assert_population_admissible("indeterminate_failure", surface)
    # run_health stays visible for failed runs (not a population surface here).
    with pytest.raises(metrics.MetricsError):
        metrics.assert_population_admissible("succeeded", "run_health")


# ---------------------------------------------------------------------------
# 10. no cross-algorithm equivalence (Phase-1 non-goal)
# ---------------------------------------------------------------------------

def test_no_cross_algorithm_equivalence_edge():
    a = _definition(algorithm_id="team/wave/algo1", metric_id="team/wave/algo1/rmse")
    b = _definition(algorithm_id="team/wave/algo2", metric_id="team/wave/algo2/rmse")
    with pytest.raises(metrics.MetricsError):
        metrics.assert_no_cross_algorithm(a, b)
    # Same algorithm -> not a cross-algorithm relation.
    a2 = _definition(algorithm_id="team/wave/algo1", metric_id="team/wave/algo1/mae")
    assert metrics.assert_no_cross_algorithm(a, a2) is True


# ---------------------------------------------------------------------------
# 11. fixtures cover every observation shape
# ---------------------------------------------------------------------------

def test_fixtures_cover_scalar_categorical_vector_uncertainty_na_invalid():
    scalar_def = _definition(metric_id="team/wave/algo1/rmse", data_type="scalar")
    cat_def = _definition(
        metric_id="team/wave/algo1/regime", data_type="categorical",
        unit_or_dimension="NA", directionality="none",
    )
    vec_def = _definition(
        metric_id="team/wave/algo1/spectrum", data_type="vector",
        unit_or_dimension="m", directionality="none",
    )

    scalar = _observation(scalar_def, value=2.0, quality_state="valid")
    categorical = _observation(cat_def, value="turbulent", quality_state="valid")
    vector = _observation(vec_def, value=[0.1, 0.2, 0.3], quality_state="valid")
    with_uncertainty = _observation(
        scalar_def, value=2.0, quality_state="valid",
        uncertainty={"kind": "stddev", "value": 0.05, "unit": "m"},
    )
    na = _observation(cat_def, value=None, quality_state="not_applicable")
    invalid = _observation(scalar_def, value=None, quality_state="invalid")

    assert scalar["value"] == 2.0
    assert categorical["value"] == "turbulent"
    assert vector["value"] == [0.1, 0.2, 0.3]
    assert with_uncertainty["uncertainty"]["value"] == 0.05
    assert na["quality_state"] == "not_applicable"
    assert invalid["quality_state"] == "invalid"

    # unit_or_dimension "NA" (a DEFINITION statement: no dimension) is a DISTINCT
    # concept from quality_state "not_applicable" (an OBSERVATION statement) even
    # though both spell "NA"; they live in different fields.
    assert cat_def["unit_or_dimension"] == "NA"
    assert na["quality_state"] == "not_applicable"
    assert "unit_or_dimension" not in na
    assert "quality_state" not in cat_def
