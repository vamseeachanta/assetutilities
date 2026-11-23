"""Check a v-prefixed release tag against static project metadata.

Requires Python 3.11 or later for tomllib; this does not change the package's
runtime Python requirement. The exact v-prefix convention is repository policy.
Metadata basis: PyPA pyproject.toml specification, name/version section,
online edition retrieved 2026-10-20. See docs/sub_release/pypi.md for sources.
"""

import argparse
import sys
from pathlib import Path

import tomllib


def validate(project: Path, tag: str, output: Path) -> str:
    """Reject inconsistent metadata and stale outputs without changing files."""
    try:
        with (project / "pyproject.toml").open("rb") as stream:
            metadata = tomllib.load(stream)["project"]
        version = metadata.get("version")
        if (
            not isinstance(version, str)
            or not version.strip()
            or "version" in metadata.get("dynamic", [])
        ):
            raise ValueError("a static, nonempty project.version is required")
    except (OSError, KeyError, TypeError, AttributeError, ValueError) as error:
        raise ValueError("cannot read a static project.version") from error
    if tag != f"v{version}":
        raise ValueError("release tag must equal v followed by project.version")
    if output.exists() and (not output.is_dir() or any(output.iterdir())):
        raise ValueError(
            "output must be a new or empty directory; retain old artifacts"
        )
    return version


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project", type=Path)
    parser.add_argument("tag")
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    try:
        version = validate(args.project, args.tag, args.output)
    except (OSError, ValueError) as error:
        print(f"Release validation failed: {error}", file=sys.stderr)
        return 1
    print(f"Validated release {version}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
