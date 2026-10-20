"""Check source, tag and distribution metadata before permitting publication.

Sources: Python Packaging User Guide, GitHub Actions publishing guide;
Core Metadata specification, Name and Version fields (2026 online edition).
This CI utility uses the Python 3.11 standard-library TOML reader.
"""

import argparse
import ast
import tarfile
import tomllib
import zipfile
from email.parser import BytesParser
from pathlib import Path


def validate_source(root: Path, tag: str | None = None) -> str:
    project = tomllib.loads((root / "pyproject.toml").read_text())["project"]
    version = project["version"]
    source = ast.parse((root / "src/assetutilities/__init__.py").read_text())
    versions = [
        ast.literal_eval(node.value)
        for node in source.body
        if isinstance(node, ast.Assign)
        and any(
            isinstance(target, ast.Name) and target.id == "__version__"
            for target in node.targets
        )
    ]
    if versions != [version]:
        raise ValueError("package __version__ must match project.version")
    if tag is not None and tag != f"v{version}":
        raise ValueError("release tag must equal v followed by project.version")
    return version


def _check_metadata(data: bytes, version: str) -> None:
    metadata = BytesParser().parsebytes(data)
    if metadata.get_all("Name") != ["assetutilities"] or metadata.get_all(
        "Version"
    ) != [version]:
        raise ValueError("distribution metadata must match project name and version")


def validate_distributions(directory: Path, version: str) -> None:
    wheels = list(directory.glob("*.whl"))
    sdists = list(directory.glob("*.tar.gz"))
    # The publishing guide builds one wheel and one sdist for a pure Python release.
    artifacts = [path for path in directory.iterdir() if path.name != ".gitignore"]
    if len(wheels) != 1 or len(sdists) != 1 or len(artifacts) != 2:
        raise ValueError("release requires exactly one wheel and one sdist")
    with zipfile.ZipFile(wheels[0]) as wheel:
        metadata = [
            name for name in wheel.namelist() if name.endswith(".dist-info/METADATA")
        ]
        if len(metadata) != 1:
            raise ValueError("wheel must have exactly one metadata file")
        _check_metadata(wheel.read(metadata[0]), version)
    with tarfile.open(sdists[0]) as archive:
        metadata = [
            member
            for member in archive.getmembers()
            if member.name.endswith("/PKG-INFO") and member.name.count("/") == 1
        ]
        if len(metadata) != 1 or not metadata[0].isfile():
            raise ValueError("sdist must have exactly one top-level metadata file")
        with archive.extractfile(metadata[0]) as stream:
            _check_metadata(stream.read(), version)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--tag")
    parser.add_argument("--dist", type=Path)
    args = parser.parse_args()
    version = validate_source(args.root, args.tag)
    if args.dist:
        validate_distributions(args.dist, version)
    print(f"Release metadata validated: {version}")


if __name__ == "__main__":
    main()
