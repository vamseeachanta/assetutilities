"""Split supplied YAML sections and plot their dimensionless example curve.

The input defines y = x*x: 0*0=0, 1*1=1, 2*2=4, 3*3=9. No engineering
constant or acceptance limit is used. Outputs belong in a supplied directory.
"""

import argparse
from pathlib import Path

from ruamel.yaml import YAML

from assetutilities.common.visualization.xy_plot_from_arrays import plot_xy_from_arrays
from assetutilities.modules.yml_utilities import split_yaml_file_by_primary_key


def run_example(input_file, output_dir):
    """Return section paths and a plot of the supplied arrays, without a solver."""
    data = YAML(typ="safe").load(Path(input_file))
    curve = data["curve"]
    sections = split_yaml_file_by_primary_key(
        input_file, Path(output_dir) / "sections", shape_output=True
    )
    plot = plot_xy_from_arrays(
        curve["x"],
        curve["y"],
        str(output_dir),
        file_name="curve",
        title="Synthetic square curve",
        xlabel="x (dimensionless)",
        ylabel="y (dimensionless)",
    )
    return sections, plot


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input_file", type=Path)
    parser.add_argument("output_dir", type=Path)
    args = parser.parse_args()
    sections, plot = run_example(args.input_file, args.output_dir)
    for section in sections:
        print(Path(section["data"]).name)
    print(Path(plot).name)


if __name__ == "__main__":
    main()
