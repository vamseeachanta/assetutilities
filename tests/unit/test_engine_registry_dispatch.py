"""Engine migration contracts derived from the pre-registry dispatch branches."""

import importlib
from unittest.mock import Mock

import pytest

from assetutilities.engine_registry import EngineRunner, RunnerRegistry

engine_module = importlib.import_module("assetutilities.engine")


@pytest.fixture
def save_cfg(monkeypatch):
    save = Mock(side_effect=lambda cfg_base: cfg_base)
    monkeypatch.setattr(engine_module.app_manager, "save_cfg", save)
    return save


def test_extension_uses_fresh_instance_and_meta_basename(monkeypatch, save_cfg):
    registry = RunnerRegistry()
    instances = []

    @registry.register("echo", "alias")
    class Echo(EngineRunner):
        def __init__(self):
            instances.append(self)

        def run(self, cfg):
            return {**cfg, "answer": cfg["input"].upper()}

    monkeypatch.setattr(engine_module, "runner_registry", registry)
    for name in ("echo", "alias"):
        cfg = {"meta": {"basename": name}, "input": "alpha"}
        result = engine_module.engine(cfg=cfg, config_flag=False)
        assert result == {**cfg, "answer": "ALPHA"}
        save_cfg.assert_called_with(cfg_base=result)
    first, second = instances
    assert first is not second


def test_runner_error_propagates_without_save(monkeypatch, save_cfg):
    registry = RunnerRegistry()
    error = KeyError("handler failure")

    @registry.register("broken")
    class Broken(EngineRunner):
        def run(self, cfg):
            raise error

    monkeypatch.setattr(engine_module, "runner_registry", registry)
    with pytest.raises(KeyError) as exc:
        engine_module.engine(cfg={"basename": "broken"}, config_flag=False)
    assert exc.value is error
    save_cfg.assert_not_called()


@pytest.mark.parametrize(
    "basename,module,class_name,method,mode",
    [
        ("read_pdf", "modules.pdf_utilities.read_pdf", "ReadPDF", "read_pdf", "result"),
        ("edit_pdf", "modules.pdf_utilities.edit_pdf", "EditPDF", "edit_pdf", "ignore"),
        (
            "zip_utilities",
            "modules.zip_utilities.zip_utilities",
            "ZipUtilities",
            "router",
            "replace",
        ),
    ],
)
def test_migrated_return_conventions(
    monkeypatch, save_cfg, basename, module, class_name, method, mode
):
    handler_module = importlib.import_module(f"assetutilities.{module}")
    returned = {"sentinel": "handler output"}
    handler = Mock(return_value=returned)
    monkeypatch.setattr(getattr(handler_module, class_name), method, handler)
    cfg = {"basename": basename}
    result = engine_module.engine(cfg=cfg, config_flag=False)
    handler.assert_called_once_with(cfg)
    if mode == "result":
        assert result is cfg
        assert result["result"] is returned
    elif mode == "ignore":
        assert result is cfg
        assert "result" not in result
    else:
        assert result is returned
    save_cfg.assert_called_once_with(cfg_base=result)


@pytest.mark.parametrize("basename", ["yaml_utilities", "yml_utilities"])
def test_legacy_aliases_keep_dispatch(monkeypatch, save_cfg, basename):
    cfg = {"basename": basename}
    handler = Mock(return_value=cfg)
    monkeypatch.setattr(engine_module.wwyaml, "router", handler)
    assert engine_module.engine(cfg=cfg, config_flag=False) is cfg
    handler.assert_called_once_with(cfg)


def test_worked_example_saves_answer(tmp_path, monkeypatch):
    """Independent oracle: a->A, l->L, p->P, h->H, a->A; beta->BETA.

    The separating space is unchanged. Expected answer: ALPHA BETA.
    This text example contains no numerical model or acceptance limits.
    """
    import runpy
    from pathlib import Path

    import yaml

    registry_module = importlib.import_module("assetutilities.engine_registry")
    registry = RunnerRegistry()
    monkeypatch.setattr(registry_module, "register_runner", registry.register)
    monkeypatch.setattr(engine_module, "runner_registry", registry)
    example = Path(__file__).resolve().parents[2] / "examples" / "engine_registry.py"
    namespace = runpy.run_path(str(example))
    result = namespace["run_example"](str(tmp_path))
    assert result["answer"] == "ALPHA BETA"
    saved_files = list((tmp_path / "results").glob("*.yml"))
    (saved_file,) = saved_files
    saved = yaml.safe_load(saved_file.read_text())
    assert saved["answer"] == "ALPHA BETA"
    assert saved["text"] == "alpha beta"


def test_registry_import_keeps_optional_handlers_lazy(tmp_path):
    """Importing the registry alone must not load any migrated handler."""
    import os
    import subprocess
    import sys
    from pathlib import Path

    env = os.environ.copy()
    env["PYTHONPATH"] = str(Path(__file__).resolve().parents[2] / "src")
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import sys; import assetutilities.engine_registry; "
                "assert 'PyPDF2' not in sys.modules; "
                "assert 'tabula' not in sys.modules; "
                "assert 'assetutilities.modules.zip_utilities.zip_utilities' "
                "not in sys.modules"
            ),
        ],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
        check=False,
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
    )
    assert result.returncode == 0, result.stderr
