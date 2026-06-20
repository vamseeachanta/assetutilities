# ABOUTME: Thin X-Y plot helper that renders two arrays via the repo's XY template.
# ABOUTME: Reuses template_xy_line_input.yml + VisualizationComponents.visualization_router.
"""Render an X-Y plot from two plain arrays using the existing visualization template.

This is intentionally thin: rather than re-deriving the (many) matplotlib/plotly
settings, it loads the canonical XY template that already ships with the test
suite (``tests/modules/visualization/template_xy_line_input.yml``), injects the
caller's ``x``/``y`` arrays, output location and labels, then hands the resulting
cfg to :class:`VisualizationComponents`. This keeps a single source of truth for
plot styling and matches how other plot paths build their cfg.
"""

import copy
import os

from assetutilities.common.update_deep import AttributeDict
from assetutilities.common.visualization_components import VisualizationComponents

# Canonical XY line template bundled with the test suite. Resolved relative to the
# repository root so the helper works from an installed package or a checkout.
_REPO_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "..")
)
_TEMPLATE_PATH = os.path.join(
    _REPO_ROOT,
    "tests",
    "modules",
    "visualization",
    "template_xy_line_input.yml",
)


def _load_template():
    from assetutilities.common.yml_utilities import WorkingWithYAML

    wwyaml = WorkingWithYAML()
    return wwyaml.ymlInput(_TEMPLATE_PATH, updateYml=None)


def plot_xy_from_arrays(
    x,
    y,
    output_dir,
    file_name="xy_plot",
    title=None,
    xlabel=None,
    ylabel=None,
    plt_engine="matplotlib",
    extensions=None,
    template_path=None,
):
    """Plot two arrays (``x`` vs ``y``) using the repo's XY visualization template.

    Args:
        x: Sequence of x values.
        y: Sequence of y values (same length as ``x``).
        output_dir: Directory under which a ``Plot/`` folder is created for output.
        file_name: Base name of the saved plot file (extension added per engine).
        title, xlabel, ylabel: Optional label overrides for the template.
        plt_engine: "matplotlib" (PNG) or "plotly" (HTML).
        extensions: Optional list of save extensions (defaults per engine).
        template_path: Optional override for the base template YAML.

    Returns:
        The full path of the (first) plot file written.
    """
    if len(x) != len(y):
        raise ValueError("x and y must have the same length")

    # Load template (allow override).
    if template_path is not None:
        from assetutilities.common.yml_utilities import WorkingWithYAML

        base_cfg = WorkingWithYAML().ymlInput(template_path, updateYml=None)
    else:
        base_cfg = _load_template()
    base_cfg = copy.deepcopy(base_cfg)

    if extensions is None:
        extensions = [".html"] if plt_engine == "plotly" else [".png"]

    # Inject the two arrays as a single input group.
    base_cfg["data"] = {
        "type": "input",
        "groups": [{"x": [list(x)], "y": [list(y)]}],
    }
    base_cfg.setdefault("master_settings", {"groups": {}})

    settings = base_cfg["settings"]
    settings["type"] = "xy"
    settings["plt_engine"] = plt_engine
    settings["file_name"] = file_name
    settings["plt_save_extensions"] = extensions
    if title is not None:
        settings["title"] = title
    if xlabel is not None:
        settings["xlabel"] = xlabel
    if ylabel is not None:
        settings["ylabel"] = ylabel
    # Reset legend labels so they are auto-derived for the injected series.
    settings.setdefault("legend", {"flag": True, "label": [], "loc": "best"})
    settings["legend"]["label"] = []

    # The visualization layer reads result_folder via attribute access.
    plot_folder = os.path.join(output_dir, "Plot")
    os.makedirs(plot_folder, exist_ok=True)
    base_cfg["Analysis"] = {"result_folder": output_dir, "file_name": file_name}

    cfg = AttributeDict(base_cfg)
    VisualizationComponents(cfg).visualization_router(cfg)

    return os.path.join(plot_folder, file_name + extensions[0])
