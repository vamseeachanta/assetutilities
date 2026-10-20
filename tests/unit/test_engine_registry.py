"""Dispatch expectations transcribed independently from the legacy engine.

Each row names the public basename, implementation and method in the old
dispatch chain. Synthetic handlers establish the return/mutation contract;
real workflow outputs are covered by the existing workflow and embed tests.
"""

from types import SimpleNamespace

import pytest

from assetutilities import engine_registry
from assetutilities.engine_registry import HandlerRegistry, registry


@pytest.mark.parametrize(
    "basename,attribute,method",
    [
        ("excel_utilities", "ExcelUtilities", "excel_utility_router"),
        ("visualization", "VisualizationComponents", "visualization_router"),
        ("file_management", "FileManagement", "router"),
        ("file_edit", "FileEdit", "router"),
        ("read_pdf", "ReadPDF", "read_pdf"),
        ("edit_pdf", "EditPDF", "edit_pdf"),
        ("word_utilities", "WordUtilities", "router"),
        ("data_exploration", "DataExploration", "router"),
        ("web_scraping", "WebScraping", "router"),
        ("download_data", "DownloadDataFromURL", "router"),
        ("yaml_utilities", "WorkingWithYAML", "router"),
        ("yml_utilities", "WorkingWithYAML", "router"),
        ("reportgen", "run", None),
        ("zip_utilities", "ZipUtilities", "router"),
    ],
)
def test_builtin_dispatch_contract(monkeypatch, basename, attribute, method):
    calls = []

    def run(cfg):
        calls.append(cfg)
        cfg["handled"] = True
        return ["page text"] if basename == "read_pdf" else None

    implementation = run if method is None else lambda: SimpleNamespace(**{method: run})
    module = SimpleNamespace(**{attribute: implementation})
    monkeypatch.setattr(engine_registry, "import_module", lambda name: module)
    cfg = {"basename": basename}
    assert registry.dispatch(basename, cfg) is cfg
    assert calls == [cfg]
    assert cfg["handled"]
    if basename == "read_pdf":
        assert cfg["result"] == ["page text"]


def test_custom_handler_and_alias_need_no_engine_edit():
    handlers = HandlerRegistry()
    replacement = {"completed": True}
    handlers.register("custom", lambda cfg: replacement, aliases=("alternate",))
    assert handlers.dispatch("alternate", {}) is replacement
    assert set(handlers.names()) == {"custom", "alternate"}


def test_duplicate_registration_is_atomic():
    handlers = HandlerRegistry()
    handlers.register("existing", lambda cfg: cfg)
    with pytest.raises(ValueError, match="already registered"):
        handlers.register("new", lambda cfg: cfg, aliases=("existing",))
    assert handlers.names() == ("existing",)


def test_handler_must_return_mapping_or_none():
    handlers = HandlerRegistry()
    handlers.register("invalid", lambda cfg: "discarded config")
    with pytest.raises(TypeError, match="mapping"):
        handlers.dispatch("invalid", {})


@pytest.mark.parametrize("basename", ["gitpython", "text_analytics", "csv_utilities"])
def test_stubs_are_not_advertised(basename):
    assert basename not in registry.names()
    with pytest.raises(NotImplementedError, match="stub"):
        registry.resolve(basename)


def test_unknown_handler_is_not_imported(monkeypatch):
    def unexpected_import(name):
        pytest.fail("A config value must never become an import target")

    monkeypatch.setattr(engine_registry, "import_module", unexpected_import)
    with pytest.raises(ValueError, match="not found"):
        registry.dispatch("untrusted.module:callable", {})


def test_reportgen_output_path_does_not_replace_config(monkeypatch):
    """The report writer returns an output path; the legacy engine ignored it."""
    monkeypatch.setattr(
        engine_registry,
        "import_module",
        lambda name: SimpleNamespace(run=lambda cfg: "outputs/report.docx"),
    )
    cfg = {"basename": "reportgen"}
    assert registry.dispatch("reportgen", cfg) is cfg


def test_custom_engine_handler_can_replace_config_with_plain_mapping(
    tmp_path, monkeypatch
):
    from assetutilities.engine import engine

    (tmp_path / "results").mkdir()
    replacement = {
        "basename": "custom",
        "Analysis": {"analysis_root_folder": str(tmp_path), "file_name": "custom"},
        "completed": True,
    }
    monkeypatch.setitem(registry._handlers, "custom", lambda cfg: replacement)
    result = engine(cfg={"basename": "custom"}, config_flag=False)
    assert result["completed"] is True
    assert (tmp_path / "results" / "custom.yml").is_file()


def test_published_workflows_have_registered_handlers():
    from pathlib import Path

    import yaml

    path = Path(__file__).resolve().parents[2] / "docs/registry/workflows.yaml"
    for row in yaml.safe_load(path.read_text())["workflows"]:
        assert row["basename"] in registry.names()
