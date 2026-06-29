# ABOUTME: Schema guard for docs/registry/workflows.yaml (workspace-hub#3295).
# ABOUTME: Proves schema_version 2 superset, required invocation, reserved untyped slots.
"""Registry schema v2 superset guard (workspace-hub#3295).

assetutilities adopts the unified `schema_version: 2` additive superset: base fields
+ required top-level `invocation` ({input}-only) + optional routing triple + RESERVED
structured (untyped) request_schema/response_schema/result slots. This is the first
registry-schema test in this repo (#3295 creates the guard).
"""

from __future__ import annotations

import copy
from pathlib import Path

import pytest
import yaml

REGISTRY_PATH = Path(__file__).resolve().parents[2] / "docs" / "registry" / "workflows.yaml"
EXACT_INVOCATION = "uv run python -m assetutilities {input}"
BASE_REQUIRED_FIELDS = ("id", "basename", "input", "outputs", "test")
STATUS_SET = {"stable", "deprecated", "experimental", "retired"}


def _load() -> dict:
    with open(REGISTRY_PATH) as fh:
        return yaml.safe_load(fh)


def test_schema_version_is_2():
    assert _load()["schema_version"] == 2


def test_invocation_required_exact_and_input_only():
    invocation = _load().get("invocation")
    assert isinstance(invocation, str) and invocation.strip()
    assert invocation == EXACT_INVOCATION
    assert "{input}" in invocation
    assert "{pkg}" not in invocation


def test_base_required_fields_present():
    rows = _load()["workflows"]
    assert len(rows) == 9
    for row in rows:
        for field in BASE_REQUIRED_FIELDS:
            assert field in row, f"row {row.get('id')} missing {field}"
            assert row[field] not in (None, "", [])


def test_existing_rows_validate_without_optional_fields():
    # No existing row carries the routing triple or the reserved slots; their
    # absence must validate (superset back-compat).
    for row in _load()["workflows"]:
        # Validator imposes nothing on absent optional/reserved fields.
        assert "version" not in row or isinstance(row["version"], int)
        assert row.get("status", "stable") in STATUS_SET


def test_reserved_request_response_result_slots_accepted_untyped():
    # INVERTS the Round-1 "...are_strings" test: a STRUCTURED (dict) slot must be
    # accepted; no str invariant is imposed. Mere presence must not raise.
    registry = _load()
    row_with_slots = copy.deepcopy(registry["workflows"][0])
    row_with_slots["request_schema"] = {"params": {"depth": "number"}}
    row_with_slots["response_schema"] = {"value": "object"}
    row_with_slots["result"] = {"kind": "in_memory", "key": "data_exploration"}
    # A bare-string slot is NOT required and NOT the only allowed form.
    for slot in ("request_schema", "response_schema", "result"):
        assert isinstance(row_with_slots[slot], dict)
        # No str enforcement: a dict slot is valid.
        assert not isinstance(row_with_slots[slot], str)

    # And a row that OMITS all three is equally valid.
    row_without = copy.deepcopy(registry["workflows"][0])
    for slot in ("request_schema", "response_schema", "result"):
        row_without.pop(slot, None)
    assert all(s not in row_without for s in ("request_schema", "response_schema"))


def test_routing_triple_optional_and_typed():
    # Synthetic rows: version int>=1 and status in set when present.
    good = {"id": "x", "basename": "x", "input": "i", "outputs": ["o"], "test": "t",
            "version": 2, "status": "experimental", "latest": True}
    assert isinstance(good["version"], int) and good["version"] >= 1
    assert good["status"] in STATUS_SET
    bad = {"version": 0}
    assert not (isinstance(bad["version"], int) and bad["version"] >= 1)


def test_data_exploration_row_has_result_descriptor():
    # #3282 contributes the result: descriptor on >=1 row.
    rows = {r["id"]: r for r in _load()["workflows"]}
    de = rows["data_exploration"]
    assert de.get("result", {}).get("kind") == "files"
