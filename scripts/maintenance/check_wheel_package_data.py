#!/usr/bin/env python3
"""Guard for assetutilities#88: ensure base_configs/**/*.yml ship in the built wheel.

The per-basename engine configs (loaded at runtime via ``pkgutil.get_data`` in
common/ApplicationManager.py) live under ``src/assetutilities/base_configs/``, which is
NOT a Python package. ``setuptools.packages.find`` therefore ignores them, and they vanish
from the wheel unless declared as package-data. When that happens every workflow breaks the
moment assetutilities is installed from a wheel (it only "works" from a source checkout).

This guard builds/inspects the wheel and fails loudly if the config tree is absent, so the
regression cannot silently reappear.

Usage: python scripts/maintenance/check_wheel_package_data.py <dist_dir>
"""
import sys
import zipfile
from pathlib import Path


def main(dist_dir: str) -> int:
    wheels = sorted(Path(dist_dir).glob("*.whl"))
    if not wheels:
        print(f"ERROR: no wheel found in {dist_dir!r}", file=sys.stderr)
        return 1
    wheel = wheels[-1]
    with zipfile.ZipFile(wheel) as z:
        ymls = [
            n
            for n in z.namelist()
            if n.startswith("assetutilities/base_configs/") and n.endswith(".yml")
        ]
    if not ymls:
        print(
            f"ERROR: {wheel.name} ships 0 base_configs/**/*.yml — package data is missing. "
            f"Check [tool.setuptools.package-data] in pyproject.toml (assetutilities#88).",
            file=sys.stderr,
        )
        return 1
    print(f"OK: {wheel.name} ships {len(ymls)} base_configs/**/*.yml files.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "dist"))
