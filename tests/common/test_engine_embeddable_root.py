"""Tests for the embeddable assetutilities engine (workspace-hub#3297).

Two additive mechanisms, both defaulting to today's exact behavior:

1. ``root_folder`` parameter threaded through ``engine`` -> ``configure`` ->
   ``get_application_configuration_parameters`` -> ``configure_result_folder`` ->
   ``set_logging``. When ``None`` (every existing caller) resolution is
   byte-identical to today.
2. A dedicated embed run path (``engine(cfg=..., embed=True, root_folder=<dir>)``
   / ``ConfigureApplicationInputs.configure_embed(...)``) that dispatches the
   caller's in-memory cfg directly (no ``unify`` discard), sandboxes all writes
   under the injected root, and uses no-file logging.

The backward-compat goldens (``test_default_no_injection_uses_cwd``,
``test_default_clobber_preserves_cwd_over_stale_preset``,
``test_cli_path_output_locations_unchanged_golden``) prove the default/CLI path
is unchanged.
"""

import glob
import logging
import os

import pytest

from assetutilities.common.ApplicationManager import ConfigureApplicationInputs
from assetutilities.common.set_logging import set_logging
from assetutilities.engine import engine

REPO_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), os.pardir, os.pardir)
)
CSV_1 = os.path.join(
    REPO_ROOT, "tests", "modules", "data_exploration", "csv", "test_1.csv"
)
CSV_2 = os.path.join(
    REPO_ROOT, "tests", "modules", "data_exploration", "csv", "test_2.csv"
)
DF_BASIC_STATS_YML = os.path.join(
    REPO_ROOT, "tests", "modules", "data_exploration", "df_basic_statistics.yml"
)

SENTINEL_KEY = "_embed_sentinel_key"
SENTINEL_VALUE = "embed-sentinel-3297"


@pytest.fixture(autouse=True)
def _restore_cwd_and_logging():
    """Isolate each test from cwd changes and process-global logging state."""
    cwd = os.getcwd()
    yield
    os.chdir(cwd)
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)


def _embed_cfg():
    """A complete in-memory data_exploration run cfg with ABSOLUTE input paths
    (so input resolution is independent of cwd and the injected root) and a
    sentinel key that only the caller cfg carries."""
    return {
        "basename": "data_exploration",
        "type": {
            "df_statistics": {"flag": True, "df_array": True, "df": True},
        },
        "data": {
            "type": "csv",
            "groups": [
                {"label": "FST1", "file_name": CSV_1},
                {"label": "FST2", "file_name": CSV_2},
            ],
        },
        "master_settings": {"groups": {"columns": {"x": ["Heading"], "y": ["Cx"]}}},
        "default": {"log_level": "DEBUG", "config": {"overwrite": {"output": True}}},
        SENTINEL_KEY: SENTINEL_VALUE,
    }


def _listdir(path):
    return set(os.listdir(path)) if os.path.isdir(path) else set()


# --------------------------------------------------------------------------- #
# Embed path
# --------------------------------------------------------------------------- #
def test_embed_honors_in_memory_cfg(tmp_path):
    """(crux / MAJOR) the embed path keeps caller cfg keys instead of discarding
    them, and actually dispatches the caller cfg (output produced)."""
    root = str(tmp_path / "rootA")
    os.makedirs(root)

    cfg_out = engine(cfg=_embed_cfg(), embed=True, root_folder=root)

    # caller sentinel survived (merge-not-replace; packaged base_config never loaded)
    assert cfg_out[SENTINEL_KEY] == SENTINEL_VALUE
    # workflow actually dispatched on the caller cfg -> result CSVs under root
    produced = glob.glob(os.path.join(root, "results", "*.csv"))
    assert produced, "embed run produced no result CSVs under the injected root"


def test_embed_rebases_config_dir_path(tmp_path):
    """(Wave-2 addendum) configure_embed rebases cfg['_config_dir_path'] to the
    injected root so config-relative routers write under root, not cwd."""
    root = str(tmp_path / "rootCDP")
    os.makedirs(root)

    cfg_out = engine(cfg=_embed_cfg(), embed=True, root_folder=root)

    assert cfg_out["_config_dir_path"] == root


def test_embed_writes_only_under_root(tmp_path):
    """embed writes results/{,Data,Plot} under the injected root and nothing at cwd."""
    root = str(tmp_path / "rootB")
    os.makedirs(root)
    scratch_cwd = str(tmp_path / "scratch_cwd")
    os.makedirs(scratch_cwd)
    os.chdir(scratch_cwd)
    before = _listdir(scratch_cwd)

    engine(cfg=_embed_cfg(), embed=True, root_folder=root)

    assert os.path.isdir(os.path.join(root, "results"))
    assert os.path.isdir(os.path.join(root, "results", "Data"))
    assert os.path.isdir(os.path.join(root, "results", "Plot"))
    # cwd untouched: no new logs/ or results/ created at cwd
    after = _listdir(scratch_cwd)
    assert after == before, f"embed run wrote to cwd: {after - before}"


def test_embed_no_logfile_no_logs_dir(tmp_path):
    """embed default (log_to_file=False) writes no .log and creates no logs/."""
    root = str(tmp_path / "rootC")
    os.makedirs(root)
    scratch_cwd = str(tmp_path / "scratch_cwd")
    os.makedirs(scratch_cwd)
    os.chdir(scratch_cwd)

    engine(cfg=_embed_cfg(), embed=True, root_folder=root, log_to_file=False)

    assert not os.path.isdir(os.path.join(root, "logs")), "embed created logs/ dir"
    assert not glob.glob(os.path.join(root, "**", "*.log"), recursive=True)
    assert not glob.glob(os.path.join(scratch_cwd, "**", "*.log"), recursive=True)


def test_embed_repeated_calls_reentrant(tmp_path):
    """(re-entrancy / MAJOR-7) two sequential embed calls with different roots
    stay isolated -> per-call instance, no customYaml/CustomInputs bleed."""
    root_a = str(tmp_path / "rootR_A")
    root_b = str(tmp_path / "rootR_B")
    os.makedirs(root_a)
    os.makedirs(root_b)

    engine(cfg=_embed_cfg(), embed=True, root_folder=root_a)
    engine(cfg=_embed_cfg(), embed=True, root_folder=root_b)

    # each call wrote only under its own root
    assert glob.glob(os.path.join(root_a, "results", "*.csv"))
    assert glob.glob(os.path.join(root_b, "results", "*.csv"))
    # no cross-contamination: A's results dir holds no file naming root_b and vice versa
    a_results = os.path.join(root_a, "results")
    b_results = os.path.join(root_b, "results")
    assert not any("rootR_B" in p for p in os.listdir(a_results))
    assert not any("rootR_A" in p for p in os.listdir(b_results))


def test_embed_requires_cfg_and_root():
    """configure_embed fails closed when cfg or root_folder is missing."""
    cai = ConfigureApplicationInputs()
    with pytest.raises(ValueError):
        cai.configure_embed(None, "data_exploration", "/tmp/x")
    with pytest.raises(ValueError):
        cai.configure_embed(_embed_cfg(), "data_exploration", None)


# --------------------------------------------------------------------------- #
# File / default path: root_folder override
# --------------------------------------------------------------------------- #
def test_file_path_root_folder_override(tmp_path):
    """root_folder param on the file/default path redirects ALL outputs to the
    injected dir; the input file's own dir gets nothing."""
    import shutil

    input_dir = str(tmp_path / "input_dir")
    os.makedirs(input_dir)
    input_yml = os.path.join(input_dir, "df_basic_statistics.yml")
    shutil.copy(DF_BASIC_STATS_YML, input_yml)
    root = str(tmp_path / "override_root")
    os.makedirs(root)

    # cwd = repo root so the yml's repo-relative csv paths resolve
    os.chdir(REPO_ROOT)
    engine(input_yml, root_folder=root)

    assert os.path.isdir(os.path.join(root, "results"))
    assert glob.glob(os.path.join(root, "results", "*.csv"))
    assert glob.glob(os.path.join(root, "logs", "*.log"))
    # input file's own dir untouched (no results/ or logs/ created there)
    assert not os.path.isdir(os.path.join(input_dir, "results"))
    assert not os.path.isdir(os.path.join(input_dir, "logs"))


# --------------------------------------------------------------------------- #
# Backward-compat goldens
# --------------------------------------------------------------------------- #
def test_default_no_injection_uses_cwd(tmp_path):
    """(backward-compat) no root_folder, no embed -> default in-memory path
    resolves root to os.getcwd() and creates <cwd>/logs/*.log + <cwd>/results
    exactly as today (forced file logging)."""
    scratch_cwd = str(tmp_path / "default_cwd")
    os.makedirs(scratch_cwd)
    os.chdir(scratch_cwd)

    # The default config_flag=True in-memory path discards the caller cfg and
    # loads the packaged base_config (today's behavior), which carries
    # repo-relative csv paths unresolvable from this scratch cwd -> dispatch
    # raises. Folder + log creation happens in configure() BEFORE dispatch, so
    # we assert today's output-location contract regardless of dispatch outcome.
    try:
        engine(cfg=_embed_cfg())
    except Exception:
        pass

    assert os.path.isdir(os.path.join(scratch_cwd, "logs"))
    assert glob.glob(os.path.join(scratch_cwd, "logs", "*.log"))
    assert os.path.isdir(os.path.join(scratch_cwd, "results"))
    assert os.path.isdir(os.path.join(scratch_cwd, "results", "Data"))
    assert os.path.isdir(os.path.join(scratch_cwd, "results", "Plot"))


def test_default_clobber_preserves_cwd_over_stale_preset(tmp_path):
    """(backward-compat / MAJOR-1 regression) a cfg carrying a stale/relative
    Analysis.analysis_root_folder AND no root_folder still resolves the root to
    os.getcwd() -- the load-bearing clobber (worldenergydata fixtures rely on it)."""
    scratch_cwd = str(tmp_path / "clobber_cwd")
    os.makedirs(scratch_cwd)
    os.chdir(scratch_cwd)

    cai = ConfigureApplicationInputs()
    # mimic the unify-step preconditions for the in-memory default path
    cai.customYaml = None
    cai.CustomInputs = None
    cai.ApplicationInputFile = os.path.join("base_configs", "data_exploration.yml")

    cfg = {
        "Analysis": {"analysis_root_folder": "tests\\test_data\\stale\\results"},
        "default": {"log_level": "DEBUG", "config": {"overwrite": {"output": True}}},
    }

    out = cai.get_application_configuration_parameters(
        None, "data_exploration", cfg, root_folder=None
    )

    assert out["Analysis"]["analysis_root_folder"] == os.getcwd()


def test_cli_path_output_locations_unchanged_golden():
    """(backward-compat golden) the file-based CLI path lands outputs under the
    input file's results/ dir, same as the pre-change baseline."""
    os.chdir(REPO_ROOT)
    engine(DF_BASIC_STATS_YML)

    results_dir = os.path.join(
        REPO_ROOT, "tests", "modules", "data_exploration", "results"
    )
    assert os.path.isdir(results_dir)
    assert glob.glob(os.path.join(results_dir, "*.csv"))


# --------------------------------------------------------------------------- #
# set_logging no-file mode
# --------------------------------------------------------------------------- #
def test_no_file_mode_makedirs_not_called(tmp_path):
    """(MINOR-5) with log_to_file=False, set_logging creates no logs/ dir even
    if log_folder points at a non-existent path; stdout logging still works."""
    nonexistent = str(tmp_path / "does_not_exist_logs")
    cfg = {
        "default": {"log_level": "INFO"},
        "Analysis": {
            "log_to_file": False,
            "log_folder": nonexistent,
            "file_name": "noop",
        },
    }

    out = set_logging(cfg)

    assert not os.path.exists(nonexistent), "no-file mode created the log folder"
    assert out is cfg
    logging.info("stdout logging works in no-file mode")
