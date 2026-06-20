# ABOUTME: Tests for engine.engine() dispatch fixes from issue #91.
# ABOUTME: Routed-but-unreachable handlers (read_pdf/edit_pdf) + loud stubs.

"""Engine dispatch regression tests (issue #91).

Covers the concrete dispatch defects:
  - read_pdf / edit_pdf: previously had no dispatch branch and hit the
    generic ``else`` raise. They must now reach their handlers.
  - gitpython: pointed at a non-existent module
    (``assetutilities.tools.git.git_python_utilities``) -> opaque
    ModuleNotFoundError. Must now raise a clear NotImplementedError.
  - csv_utilities / text_analytics: no-op ``pass`` stubs that silently
    produced no output. Must now raise a clear NotImplementedError.

Dispatch is exercised with ``config_flag=False`` and a minimal cfg so the
file/config pipeline is skipped and the branch is reached directly. The
trailing ``save_cfg`` is patched for the *reachable* handlers because the
minimal dict lacks the ``Analysis`` attribute it expects; the stub branches
raise before ``save_cfg`` is reached.
"""

from unittest import mock

import pytest

from assetutilities.engine import engine


# --- Genuine stubs: must fail loudly with NotImplementedError ---------------


@pytest.mark.parametrize(
    "basename",
    ["gitpython", "text_analytics", "csv_utilities"],
)
def test_stub_basename_raises_not_implemented(basename):
    with pytest.raises(NotImplementedError) as exc:
        engine(cfg={"basename": basename}, config_flag=False)
    # Message names the basename and gives guidance (not a silent no-op).
    assert basename in str(exc.value)
    assert "stub" in str(exc.value).lower()


# --- Previously-unreachable handlers: must now be reached --------------------


def test_read_pdf_handler_is_reachable():
    """read_pdf now has a dispatch branch and reaches ReadPDF.read_pdf."""
    with mock.patch(
        "assetutilities.modules.pdf_utilities.read_pdf.ReadPDF.read_pdf",
        return_value="SENTINEL",
    ) as m, mock.patch(
        "assetutilities.engine.app_manager.save_cfg",
        side_effect=lambda cfg_base: cfg_base,
    ):
        result = engine(cfg={"basename": "read_pdf"}, config_flag=False)
    assert m.called
    assert result["result"] == "SENTINEL"


def test_edit_pdf_handler_is_reachable():
    """edit_pdf now has a dispatch branch and reaches EditPDF.edit_pdf."""
    with mock.patch(
        "assetutilities.modules.pdf_utilities.edit_pdf.EditPDF.edit_pdf",
        return_value=None,
    ) as m, mock.patch(
        "assetutilities.engine.app_manager.save_cfg",
        side_effect=lambda cfg_base: cfg_base,
    ):
        engine(cfg={"basename": "edit_pdf"}, config_flag=False)
    assert m.called


# --- Unknown basename: generic failure mode preserved ------------------------


def test_unknown_basename_still_raises():
    with pytest.raises(Exception) as exc:
        engine(cfg={"basename": "definitely_not_a_basename"}, config_flag=False)
    # Not a NotImplementedError -- the generic "not found" path.
    assert not isinstance(exc.value, NotImplementedError)
    assert "not found" in str(exc.value)
