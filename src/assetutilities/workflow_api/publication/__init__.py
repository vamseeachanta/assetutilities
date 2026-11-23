# ABOUTME: Public surface for the publication + staged-promotion contract (workspace-hub#3433).
"""Publication + staged promotion for the deterministic workflow API.

Composes the five on-branch record modules (identity / artifact / inputs /
output_contract / metrics) into a publishable :class:`RunProjection`, drives it
through the evidence-bearing promotion state machine, gates every egress point
fail-closed, projects to Hugging Face through an injectable port, and records
acceptance in an append-only source-repo publication ledger.
"""

from assetutilities.workflow_api.publication.projection import (
    RunProjection,
    ProjectionError,
    build_projection,
    HF_DATA_PLANE_TABLES,
    SOURCE_REPO_AUTHORITY_PLANE,
    REPORT_PATH_PATTERN,
)
from assetutilities.workflow_api.publication.promotion import (
    PromotionMachine,
    PromotionJournal,
    PromotionError,
    PROMOTION_STATES,
    TRANSITIONS,
    REQUIREMENTS,
    requirements_for,
    verify_journal,
    is_exact_revision,
)
from assetutilities.workflow_api.publication.egress import (
    EgressGate,
    EgressDenied,
    GateResult,
)
from assetutilities.workflow_api.publication.hf_port import (
    HfPort,
    InMemoryHfPort,
    HuggingFaceHubHfPort,
    HfError,
    HfTransientError,
    HfUnavailableError,
)
from assetutilities.workflow_api.publication.ledger import (
    Ledger,
    LedgerError,
    PUBLICATIONS_LEDGER_PATH,
    LEDGER_PLANE,
)

__all__ = [
    # projection
    "RunProjection",
    "ProjectionError",
    "build_projection",
    "HF_DATA_PLANE_TABLES",
    "SOURCE_REPO_AUTHORITY_PLANE",
    "REPORT_PATH_PATTERN",
    # promotion
    "PromotionMachine",
    "PromotionJournal",
    "PromotionError",
    "PROMOTION_STATES",
    "TRANSITIONS",
    "REQUIREMENTS",
    "requirements_for",
    "verify_journal",
    "is_exact_revision",
    # egress
    "EgressGate",
    "EgressDenied",
    "GateResult",
    # hf port
    "HfPort",
    "InMemoryHfPort",
    "HuggingFaceHubHfPort",
    "HfError",
    "HfTransientError",
    "HfUnavailableError",
    # ledger
    "Ledger",
    "LedgerError",
    "PUBLICATIONS_LEDGER_PATH",
    "LEDGER_PLANE",
]
