# ABOUTME: Tests for engine.engine() dispatch fixes from issue #91.
# ABOUTME: PDF handlers and implemented CSV, text and read-only Git routers.

"""Engine reachability regressions; real workflow outputs are tested separately."""

from unittest import mock

import pytest

from assetutilities.engine import engine


@pytest.mark.parametrize(
    "basename, target",
    [
        ("csv_utilities", "assetutilities.engine.CSVUtilitiesRouter.router"),
        ("text_analytics", "assetutilities.engine.TextAnalytics.router"),
        (
            "gitpython",
            "assetutilities.modules.git_utilities.git_utilities.GitUtilities.router",
        ),
    ],
)
def test_implemented_handler_is_reachable(basename, target):
    with (
        mock.patch(target, side_effect=lambda cfg: {**cfg, "handled": True}),
        mock.patch(
            "assetutilities.engine.app_manager.save_cfg",
            side_effect=lambda cfg_base: cfg_base,
        ),
    ):
        assert engine(cfg={"basename": basename}, config_flag=False)["handled"] is True


# --- Previously-unreachable handlers: must now be reached --------------------


def test_read_pdf_handler_is_reachable():
    """read_pdf now has a dispatch branch and reaches ReadPDF.read_pdf."""
    with (
        mock.patch(
            "assetutilities.modules.pdf_utilities.read_pdf.ReadPDF.read_pdf",
            return_value="SENTINEL",
        ) as m,
        mock.patch(
            "assetutilities.engine.app_manager.save_cfg",
            side_effect=lambda cfg_base: cfg_base,
        ),
    ):
        result = engine(cfg={"basename": "read_pdf"}, config_flag=False)
    assert m.called
    assert result["result"] == "SENTINEL"


def test_edit_pdf_handler_is_reachable():
    """edit_pdf now has a dispatch branch and reaches EditPDF.edit_pdf."""
    with (
        mock.patch(
            "assetutilities.modules.pdf_utilities.edit_pdf.EditPDF.edit_pdf",
            return_value=None,
        ) as m,
        mock.patch(
            "assetutilities.engine.app_manager.save_cfg",
            side_effect=lambda cfg_base: cfg_base,
        ),
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
