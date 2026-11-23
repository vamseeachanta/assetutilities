# ABOUTME: Algorithm-specific metric definition + observation contract (workspace-hub#3432):
# ABOUTME: single-algorithm scope, whole-prefix ownership, immutable versioned definitions,
# ABOUTME: closed quality_state enum, fail-closed population, no cross-algorithm equivalence.
"""Algorithm-specific metric definitions and observations.

This module implements the on-main
``docs/architecture/algorithm-run-dataset-contract.yaml`` ``records.metric_definition``
+ ``records.metric_observation`` + ``metrics`` blocks and the approved+remediated
#3432 plan. It is stdlib-only plus :mod:`identity` (the canonical-serialization +
digest owner) and reuses :mod:`identity` terminal-status semantics, matching
:mod:`envelope`, :mod:`identity`, :mod:`artifact`, :mod:`output_contract`.

Design invariants (from the approved+remediated #3432 plan):

- **Scope is a single algorithm.** ``metrics.scope == single_algorithm`` and
  ``definition_owner_cardinality == 1``: a metric belongs to EXACTLY one algorithm.
  ``metric_id`` MUST be WHOLE-PREFIX-owned by its ``algorithm_id`` -- validated by a
  segment-boundary prefix match, NOT split-on-last-``/`` (a workflow_id may itself
  contain ``/``). The :class:`MetricDefinitionStore` enforces one owner per metric_id.
- **metric_definition_id binds the semantics and is immutable once published.** It is
  an :func:`identity.canonical_digest` over metric_id + algorithm_id +
  definition_version + the full definition body. Re-registering an existing
  (metric_id, definition_version) with ANY differing field FAILS CLOSED; a semantic
  change MUST mint a NEW ``definition_version``. The store is append-only.
- **directionality is ALWAYS present** (deliberate strengthening): explicit ``"none"``
  when a direction is not meaningful, never omission -- so "no direction" is
  machine-distinguishable from "unspecified".
- **quality_state is a closed 4-value enum** (valid | not_applicable | invalid |
  missing) keeping not-applicable, null and numeric-zero mutually DISTINCT and
  machine-validatable. ``unit_or_dimension == "NA"`` (a DEFINITION statement: no
  dimension concept) and ``quality_state == "not_applicable"`` (an OBSERVATION
  statement) share the "NA" token but are DISTINCT meanings in DISTINCT fields.
- **Independent versioning.** Definitions are versioned independently from
  observations; an observation snapshots the EXACT ``metric_definition_version`` /
  ``metric_definition_id`` it used, so a later definition version never mutates it.
- **Fail-closed population.** Only a terminal ``succeeded`` (validated, reproducible)
  run with observation ``quality_state == valid`` AND a matching algorithm owner AND a
  validating (registered) ``definition_version`` enters metric populations. Failed /
  non-reproducible runs are EXCLUDED from metrics AND insights AND decisions (not just
  metrics) while staying visible in run_health (see :mod:`output_contract`).
- **No cross-algorithm equivalence.** Relating/comparing two different algorithms'
  metrics is REJECTED -- an explicit Phase-1 non-goal; ``meaning`` is non-transferable.
"""

from __future__ import annotations

from assetutilities.workflow_api import identity

# ---- on-main contract constants -------------------------------------------
SCOPE = "single_algorithm"
DEFINITION_OWNER_CARDINALITY = 1
CROSS_ALGORITHM_EQUIVALENCE = "forbidden_in_phase_1"
ELIGIBLE_RUN_STATUSES = ("succeeded_validated_reproducible",)

DEFINITION_DATASET_TABLE = "metric_definitions"
DEFINITION_OWNER = "source_repository"
OBSERVATION_DATASET_TABLE = "metric_observations"
OBSERVATION_OWNER = "dedicated_hf_dataset"

# The contract-required definition fields (verbatim from ``metrics.required_definition_fields``).
REQUIRED_DEFINITION_FIELDS = (
    "metric_id",
    "algorithm_id",
    "definition_version",
    "meaning",
    "unit_or_dimension",
    "derivation",
    "applicability",
    "quality_rule",
)

# The plan strengthens the record with label + data_type + an ALWAYS-present
# directionality; these are required by this module in addition to the contract set.
_EXTRA_REQUIRED_FIELDS = ("label", "data_type", "directionality")

# The only run status that may populate metrics (validated + reproducible succeeded).
_SUCCEEDED = "succeeded"

# Closed 4-value quality_state enum. numeric-zero (valid) != not_applicable != missing.
QUALITY_STATES = frozenset({"valid", "not_applicable", "invalid", "missing"})

# Surfaces a failed run is excluded from (mirrors output_contract's forbidden set,
# named for the population layer): failed runs never reach these.
POPULATION_SURFACES = frozenset({"metrics", "insights", "decisions"})

# The metric_id segment separator used for whole-prefix ownership.
_SEGMENT_SEP = "/"


class MetricsError(ValueError):
    """Raised when a metric definition/observation violates the #3432 contract."""


# ---------------------------------------------------------------------------
# whole-prefix ownership
# ---------------------------------------------------------------------------

def is_owned_prefix(metric_id, algorithm_id) -> bool:
    """True iff ``metric_id`` is WHOLE-PREFIX-owned by ``algorithm_id``.

    The metric_id must equal the algorithm_id followed by ``/`` and a non-empty
    metric segment. This is a segment-boundary match (NOT ``str.startswith`` alone),
    so ``algorithm_id`` may itself contain ``/`` (a workflow_id) and a sibling like
    ``team/algo1x/...`` is NOT falsely owned by ``team/algo1``.
    """
    if not isinstance(metric_id, str) or not isinstance(algorithm_id, str):
        return False
    if not algorithm_id or not metric_id:
        return False
    prefix = algorithm_id + _SEGMENT_SEP
    return metric_id.startswith(prefix) and len(metric_id) > len(prefix)


# ---------------------------------------------------------------------------
# metric definition
# ---------------------------------------------------------------------------

def make_metric_definition(
    *,
    metric_id=None,
    algorithm_id=None,
    definition_version=None,
    label=None,
    meaning=None,
    unit_or_dimension=None,
    data_type=None,
    derivation=None,
    applicability=None,
    directionality=None,
    quality_rule=None,
) -> dict:
    """Build + validate a :class:`dict` MetricDefinition, minting its
    ``metric_definition_id``.

    Fail-closed rules:

    - Every contract-required field (:data:`REQUIRED_DEFINITION_FIELDS`) plus the
      plan's strengthened fields (label, data_type, directionality) MUST be present
      and non-empty; ``directionality`` MUST be explicit (use ``"none"`` when a
      direction is not meaningful).
    - ``metric_id`` MUST be whole-prefix-owned by ``algorithm_id`` (single owner).
    - ``metric_definition_id`` is an :func:`identity.canonical_digest` binding
      metric_id + algorithm_id + definition_version + the full body; a changed field
      mints a different id (the basis for append-only immutability in the store).
    """
    body = {
        "metric_id": metric_id,
        "algorithm_id": algorithm_id,
        "definition_version": definition_version,
        "label": label,
        "meaning": meaning,
        "unit_or_dimension": unit_or_dimension,
        "data_type": data_type,
        "derivation": derivation,
        "applicability": applicability,
        "directionality": directionality,
        "quality_rule": quality_rule,
    }
    missing = [
        k
        for k in (*REQUIRED_DEFINITION_FIELDS, *_EXTRA_REQUIRED_FIELDS)
        if body.get(k) is None or body.get(k) == ""
    ]
    if missing:
        raise MetricsError(
            f"metric definition missing required field(s): {sorted(missing)} "
            "(directionality is ALWAYS required -- use 'none' when not meaningful)"
        )
    if not is_owned_prefix(metric_id, algorithm_id):
        raise MetricsError(
            f"metric_id {metric_id!r} is not whole-prefix-owned by algorithm_id "
            f"{algorithm_id!r}; a metric belongs to exactly one algorithm and its id "
            f"must be '{algorithm_id}{_SEGMENT_SEP}<metric-segment>'"
        )
    metric_definition_id = identity.canonical_digest("metric_definition_id", body)
    return {**body, "metric_definition_id": metric_definition_id}


# ---------------------------------------------------------------------------
# append-only, immutable definition store (single owner per metric_id)
# ---------------------------------------------------------------------------

class MetricDefinitionStore:
    """Append-only store of MetricDefinitions with immutable published versions.

    Enforces (fail-closed):

    - **One algorithm owner per metric_id** (``definition_owner_cardinality == 1``):
      registering a metric_id already owned by a different ``algorithm_id`` is rejected.
    - **Immutable (metric_id, definition_version)**: re-registering the SAME key with a
      differing body (a differing ``metric_definition_id``) is rejected; an identical
      re-register is idempotent. A semantic change MUST mint a NEW ``definition_version``
      (a distinct key), which is appended so history is retained.
    """

    def __init__(self):
        self._by_key = {}  # (metric_id, definition_version) -> definition dict
        self._owner = {}  # metric_id -> algorithm_id

    def register(self, definition) -> dict:
        """Register ``definition`` (append-only). Returns the stored definition."""
        if not isinstance(definition, dict):
            raise MetricsError("definition must be a dict")
        metric_id = definition.get("metric_id")
        algorithm_id = definition.get("algorithm_id")
        version = definition.get("definition_version")
        did = definition.get("metric_definition_id")
        if not metric_id or not algorithm_id or not version or not did:
            raise MetricsError(
                "definition must be built via make_metric_definition (needs metric_id, "
                "algorithm_id, definition_version, metric_definition_id)"
            )

        owner = self._owner.get(metric_id)
        if owner is not None and owner != algorithm_id:
            raise MetricsError(
                f"metric_id {metric_id!r} is already owned by algorithm {owner!r}; "
                f"a second owner {algorithm_id!r} violates definition_owner_cardinality=1"
            )

        key = (metric_id, version)
        existing = self._by_key.get(key)
        if existing is not None:
            if existing["metric_definition_id"] != did:
                raise MetricsError(
                    f"metric definition ({metric_id!r}, version {version!r}) is already "
                    "published and immutable; a changed field must mint a NEW "
                    "definition_version, not overwrite the existing one"
                )
            return existing  # idempotent re-register of the identical body

        stored = dict(definition)
        self._by_key[key] = stored
        self._owner[metric_id] = algorithm_id
        return stored

    def get(self, metric_id, definition_version) -> dict:
        """Return the stored definition for ``(metric_id, definition_version)``."""
        try:
            return self._by_key[(metric_id, definition_version)]
        except KeyError:
            raise MetricsError(
                f"no registered definition for ({metric_id!r}, {definition_version!r})"
            )

    def versions(self, metric_id) -> tuple:
        """Return all registered ``definition_version`` values for ``metric_id``."""
        return tuple(v for (m, v) in self._by_key if m == metric_id)

    def is_registered(self, metric_definition_id) -> bool:
        """True iff a definition with this exact ``metric_definition_id`` is stored."""
        return any(
            d["metric_definition_id"] == metric_definition_id
            for d in self._by_key.values()
        )


# ---------------------------------------------------------------------------
# metric observation
# ---------------------------------------------------------------------------

def make_metric_observation(
    *,
    definition,
    run_id,
    value,
    quality_state,
    derivation_evidence,
    uncertainty=None,
) -> dict:
    """Build + validate a MetricObservation bound to ``run_id`` + the EXACT definition
    version, minting its ``metric_observation_id``.

    Snapshots ``metric_definition_id`` / ``metric_definition_version`` / ``algorithm_id``
    from ``definition`` so a later definition version never mutates this observation.

    Fail-closed rules:

    - ``quality_state`` MUST be in :data:`QUALITY_STATES`.
    - ``quality_state == valid`` REQUIRES a present ``value`` (so a real numeric ZERO
      stays DISTINCT from ``missing`` / ``not_applicable`` -- never collapses to null).
    - ``quality_state`` in {``not_applicable``, ``missing``} MUST NOT carry a value.
    - ``run_id`` and ``derivation_evidence`` are required (units unambiguous:
      the ``unit_or_dimension`` lives on the definition, not smuggled into ``value``).
    """
    if not isinstance(definition, dict) or not definition.get("metric_definition_id"):
        raise MetricsError("observation needs a definition built via make_metric_definition")
    if not run_id:
        raise MetricsError("observation requires a non-empty run_id")
    if quality_state not in QUALITY_STATES:
        raise MetricsError(
            f"quality_state {quality_state!r} is not in the closed enum "
            f"{sorted(QUALITY_STATES)}"
        )
    if quality_state == "valid" and value is None:
        raise MetricsError(
            "quality_state 'valid' requires a present value; a real numeric 0 is a "
            "value, but None is 'missing'/'not_applicable', which stays distinct"
        )
    if quality_state in ("not_applicable", "missing") and value is not None:
        raise MetricsError(
            f"quality_state {quality_state!r} MUST NOT carry a value "
            f"(got {value!r}); not-applicable/missing are the absence of a value"
        )
    if not derivation_evidence:
        raise MetricsError("observation requires non-empty derivation_evidence")

    body = {
        "run_id": run_id,
        "metric_definition_id": definition["metric_definition_id"],
        "metric_definition_version": definition["definition_version"],
        "algorithm_id": definition["algorithm_id"],
        "value": value,
        "quality_state": quality_state,
        "uncertainty": uncertainty,
    }
    metric_observation_id = identity.canonical_digest("metric_observation_id", body)
    return {
        **body,
        "derivation_evidence": derivation_evidence,
        "metric_observation_id": metric_observation_id,
    }


# ---------------------------------------------------------------------------
# fail-closed population eligibility
# ---------------------------------------------------------------------------

def population_eligible(*, terminal_status, run_algorithm_id, observation, store) -> bool:
    """True iff ``observation`` may enter a metric population (fail-closed).

    ALL of the following must hold (any miss -> ``False``):

    1. ``terminal_status == 'succeeded'`` (validated + reproducible);
    2. ``observation.quality_state == 'valid'``;
    3. the run's algorithm matches the metric's owning algorithm
       (``run_algorithm_id == observation.algorithm_id``);
    4. the observation's ``metric_definition_id`` is a validating (registered) version
       in ``store``.
    """
    if terminal_status != _SUCCEEDED:
        return False
    if not isinstance(observation, dict):
        return False
    if observation.get("quality_state") != "valid":
        return False
    if run_algorithm_id != observation.get("algorithm_id"):
        return False
    if store is None or not store.is_registered(observation.get("metric_definition_id")):
        return False
    return True


def assert_population_admissible(terminal_status, surface) -> bool:
    """Reject a failed run entering a population surface (fail-closed).

    Failed / non-reproducible runs are EXCLUDED from metrics AND insights AND
    decisions (not just metrics) -- only a terminal ``succeeded`` run is admissible.
    ``surface`` MUST be one of :data:`POPULATION_SURFACES` (run_health is NOT a
    population surface -- failed runs stay visible there, handled by
    :mod:`output_contract`). Returns ``True`` when admissible.
    """
    if surface not in POPULATION_SURFACES:
        raise MetricsError(
            f"{surface!r} is not a population surface {sorted(POPULATION_SURFACES)}; "
            "run_health visibility of failed runs is owned by output_contract"
        )
    if terminal_status != _SUCCEEDED:
        raise MetricsError(
            f"a {terminal_status!r} run is excluded from the {surface!r} population "
            "(only validated+reproducible 'succeeded' runs enter metrics/insights/decisions)"
        )
    return True


# ---------------------------------------------------------------------------
# no cross-algorithm equivalence (Phase-1 non-goal)
# ---------------------------------------------------------------------------

def assert_no_cross_algorithm(definition_a, definition_b) -> bool:
    """Reject relating/comparing two DIFFERENT algorithms' metrics (fail-closed).

    Cross-algorithm equivalence is ``forbidden_in_phase_1``: ``meaning`` is declared
    non-transferable, so two metrics from different ``algorithm_id`` values may never
    be related or compared. Two metrics of the SAME algorithm are not a
    cross-algorithm relation and are permitted. Returns ``True`` when same-algorithm.
    """
    if not isinstance(definition_a, dict) or not isinstance(definition_b, dict):
        raise MetricsError("both definitions must be dicts")
    algo_a = definition_a.get("algorithm_id")
    algo_b = definition_b.get("algorithm_id")
    if not algo_a or not algo_b:
        raise MetricsError("both definitions must carry an algorithm_id")
    if algo_a != algo_b:
        raise MetricsError(
            f"cross-algorithm equivalence is {CROSS_ALGORITHM_EQUIVALENCE}: cannot "
            f"relate metric of {algo_a!r} to metric of {algo_b!r} (meaning is "
            "non-transferable; Phase-1 non-goal)"
        )
    return True
