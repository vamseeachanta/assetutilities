# ABOUTME: Public surface for the deterministic workflow API (workspace-hub#3282).
"""Deterministic, in-process workflow API for assetutilities.

Exposes the typed :class:`ResultEnvelope` contract and the
``run_workflow(workflow_id, params=None, cfg=None, verify_reproducible=False)``
entrypoint built on the embeddable engine path (workspace-hub#3297).
"""

from assetutilities.workflow_api.envelope import (
    ResultEnvelope,
    code_version,
    compute_reproducible,
    input_hash,
    make_provenance,
    result_hash,
)
from assetutilities.workflow_api.runner import (
    ResultLocator,
    build_cfg,
    extract_result,
    run_workflow,
)
from assetutilities.workflow_api.output_contract import (
    OutputContractError,
    make_output_record,
    output_equality_digest,
)
from assetutilities.workflow_api.report import render_report

__all__ = [
    "ResultEnvelope",
    "run_workflow",
    "ResultLocator",
    "build_cfg",
    "extract_result",
    "code_version",
    "compute_reproducible",
    "input_hash",
    "result_hash",
    "make_provenance",
    "OutputContractError",
    "make_output_record",
    "output_equality_digest",
    "render_report",
]
