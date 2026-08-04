# ABOUTME: Tests that assetutilities library code raises instead of exiting the process (issue #80).
# ABOUTME: Also pins the absence of bare except clauses, which swallow SystemExit/KeyboardInterrupt.

import ast
import pathlib

import pytest

COMMON_DIR = (
    pathlib.Path(__file__).resolve().parents[2] / "src" / "assetutilities" / "common"
)


def _python_files():
    return sorted(COMMON_DIR.rglob("*.py"))


def _sites(predicate):
    """Return 'relpath:lineno' for every AST node in common/ matching predicate."""
    found = []
    for path in _python_files():
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if predicate(node):
                found.append(f"{path.relative_to(COMMON_DIR)}:{node.lineno}")
    return found


def _is_bare_except(node):
    return isinstance(node, ast.ExceptHandler) and node.type is None


def _is_sys_exit_call(node):
    if not isinstance(node, ast.Call):
        return False
    func = node.func
    return (
        isinstance(func, ast.Attribute)
        and func.attr == "exit"
        and isinstance(func.value, ast.Name)
        and func.value.id == "sys"
    )


class TestNoProcessExitInLibraryCode:
    def test_common_package_contains_no_sys_exit_calls(self):
        # Library code must raise so callers can build a summary/provenance
        # block; only CLI entry points may terminate the process.
        assert _sites(_is_sys_exit_call) == []


class TestNoBareExceptInLibraryCode:
    def test_common_package_contains_no_bare_except_clauses(self):
        # A bare except also catches SystemExit and KeyboardInterrupt.
        assert _sites(_is_bare_except) == []


try:
    from assetutilities.common.ApplicationManager import ConfigureApplicationInputs
    from assetutilities.common.visualizations import Visualization
except ModuleNotFoundError as exc:  # pragma: no cover - env-dependent
    pytest.skip(
        f"assetutilities.common optional dependency missing: {exc}",
        allow_module_level=True,
    )


class TestGenerateYMLInputRaisesOnUnreadableCustomYaml:
    def _manager(self, custom_yaml):
        manager = ConfigureApplicationInputs.__new__(ConfigureApplicationInputs)
        manager.ApplicationInputFile = "does-not-exist.yml"
        manager.ApplicationInputFile_dict = {"basename": "probe"}
        manager.customYaml = custom_yaml
        manager.CustomInputs = None
        return manager

    def test_unreadable_custom_yaml_raises_valueerror(self, tmp_path):
        missing = str(tmp_path / "absent.yml")
        with pytest.raises(ValueError):
            self._manager(missing).generateYMLInput({}, {})

    def test_unreadable_custom_yaml_does_not_raise_systemexit(self, tmp_path):
        missing = str(tmp_path / "absent.yml")
        try:
            self._manager(missing).generateYMLInput({}, {})
        except SystemExit:  # pragma: no cover - the defect being fixed
            raised_systemexit = True
        except ValueError:
            raised_systemexit = False
        assert raised_systemexit is False

    def test_readable_custom_yaml_still_merges_into_the_configuration(self, tmp_path):
        custom = tmp_path / "custom.yml"
        custom.write_text("basename: probe\nsettings:\n  dpi: 300\n")
        cfg = self._manager(str(custom)).generateYMLInput({}, {})
        assert cfg["settings"]["dpi"] == 300


class TestScatterPlotErrorRaisesInsteadOfExiting:
    def _visualization_and_frame(self, monkeypatch):
        import matplotlib
        import pandas as pd

        matplotlib.use("Agg")
        viz = Visualization()
        df = pd.DataFrame({"a": [1, 2], "b": [3, 4]})
        settings = {
            "x": ["a"],
            "y": ["b"],
            "label": ["series"],
            "plt_kind": "scatter",
        }
        return viz, df, settings

    def test_datetime_scatter_failure_raises_valueerror(self, monkeypatch):
        viz, df, settings = self._visualization_and_frame(monkeypatch)

        def boom(*args, **kwargs):
            raise TypeError("float() argument must be a number, not datetime.date")

        monkeypatch.setattr(viz.plot_object, "scatter", boom)
        with pytest.raises(ValueError):
            viz.from_df_columns(df, settings)

    def test_datetime_scatter_failure_does_not_raise_systemexit(self, monkeypatch):
        viz, df, settings = self._visualization_and_frame(monkeypatch)

        def boom(*args, **kwargs):
            raise TypeError("float() argument must be a number, not datetime.date")

        monkeypatch.setattr(viz.plot_object, "scatter", boom)
        try:
            viz.from_df_columns(df, settings)
        except SystemExit:  # pragma: no cover - the defect being fixed
            raised_systemexit = True
        except ValueError:
            raised_systemexit = False
        assert raised_systemexit is False

    def test_working_scatter_plot_is_unaffected(self, monkeypatch):
        viz, df, settings = self._visualization_and_frame(monkeypatch)
        calls = []
        monkeypatch.setattr(viz.plot_object, "scatter", lambda *a, **k: calls.append(1))
        viz.from_df_columns(df, settings)
        assert len(calls) == 1
