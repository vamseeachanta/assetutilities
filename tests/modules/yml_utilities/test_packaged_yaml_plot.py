"""A supplied dimensionless curve can be plotted without repository fixtures."""

import os
from pathlib import Path
import shutil
import subprocess
import sys


def test_plot_uses_packaged_template_without_repository_tests(tmp_path):
    """Independent example: x=(0,1,2), y=(0*0,1*1,2*2)=(0,1,4).

    A copy of the installed package layout contains no tests directory. Both
    renderers must produce nonempty outputs using only shipped resources.
    """
    import assetutilities

    package_dir = Path(assetutilities.__file__).parent
    installed = tmp_path / "installed"
    shutil.copytree(
        package_dir,
        installed / "assetutilities",
        ignore=shutil.ignore_patterns("__pycache__"),
    )
    env = os.environ.copy()
    env["PYTHONPATH"] = str(installed)
    for name in ("GIT_DIR", "GIT_WORK_TREE", "GIT_COMMON_DIR"):
        env.pop(name, None)
    command = """
from pathlib import Path
from assetutilities.common.visualization.xy_plot_from_arrays import plot_xy_from_arrays
for engine in ('matplotlib', 'plotly'):
    output = plot_xy_from_arrays(
        [0, 1, 2], [0, 1, 4], '.', file_name=engine,
        title='Synthetic curve', xlabel='x', ylabel='y', plt_engine=engine,
    )
    assert Path(output).is_file()
    assert Path(output).stat().st_size > 0
"""
    result = subprocess.run(
        [sys.executable, "-c", command],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert (tmp_path / "Plot" / "matplotlib.png").read_bytes().startswith(b"\x89PNG")
    assert "<html>" in (tmp_path / "Plot" / "plotly.html").read_text(encoding="utf-8")


def test_worked_example_splits_and_plots_literal_curve(tmp_path):
    """Hand calculation: 0*0=0, 1*1=1, 2*2=4, 3*3=9.

    There are two collection keys (curve and coordinates), hence two section
    files; the label scalar is omitted. Plotting does not recalculate values.
    """
    from ruamel.yaml import YAML

    root = Path(__file__).resolve().parents[3]
    script = root / "examples" / "yaml_split_plot" / "split_and_plot.py"
    source = script.with_name("input.yml")
    env = os.environ.copy()
    env["PYTHONPATH"] = str(root / "src")
    for name in ("GIT_DIR", "GIT_WORK_TREE", "GIT_COMMON_DIR"):
        env.pop(name, None)
    result = subprocess.run(
        [sys.executable, str(script), str(source), str(tmp_path)],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    files = sorted((tmp_path / "sections").glob("*.yml"))
    assert [path.name for path in files] == ["input_coordinates.yml", "input_curve.yml"]
    assert YAML(typ="safe").load(files[0]) == {
        "coordinates": [[0, 0], [1, 1], [2, 4], [3, 9]]
    }
    assert YAML(typ="safe").load(files[1]) == {
        "curve": {"x": [0, 1, 2, 3], "y": [0, 1, 4, 9]}
    }
    assert "- [2, 4]" in files[0].read_text(encoding="utf-8-sig")
    assert (tmp_path / "Plot" / "curve.png").read_bytes().startswith(b"\x89PNG")
