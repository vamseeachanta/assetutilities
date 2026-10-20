import os
import re
from collections.abc import Mapping
from io import StringIO
from pathlib import Path

from loguru import logger
from ruamel.yaml import YAML as ruamelYAML
from ruamel.yaml.comments import CommentedSeq
from ruamel.yaml.scalarstring import FoldedScalarString, LiteralScalarString


def _new_yaml():
    """Keep parser state local, including after a rejected document."""
    yaml = ruamelYAML()
    yaml.preserve_quotes = True
    # YAML 1.2.2 (2021), section 3.2.1.1: mapping keys must be unique.
    yaml.allow_duplicate_keys = False
    # Formatting follows ruamel's documented block-sequence indentation example.
    # Source: https://yaml.dev/doc/ruamel.yaml/detail/#Indentation_of_block_sequences
    yaml.indent(mapping=2, sequence=4, offset=2)
    return yaml


def _single_line_scalar(value):
    return not isinstance(
        value, (Mapping, list, LiteralScalarString, FoldedScalarString)
    ) and not (isinstance(value, str) and "\n" in value)


def _split_destinations(keys, input_file, output_dir):
    """Validate the complete output set before creating directories or files."""
    destinations = []
    seen = set()
    root = Path(output_dir).resolve()
    for key in keys:
        if (
            not isinstance(key, str)
            or not key.strip()
            or key.endswith((".", " "))
            or re.search(r'[<>:"/\\|?*\x00-\x1f]', key)
        ):
            raise ValueError("Primary keys must be portable filename components")
        filename = f"{Path(input_file).stem}_{key}.yml"
        destination = Path(output_dir) / filename
        if (
            filename.casefold() in seen
            or destination.is_symlink()
            or destination.resolve().parent != root
        ):
            raise ValueError(
                "Split destinations must be distinct and inside output_dir"
            )
        seen.add(filename.casefold())
        destinations.append((key, str(destination)))
    return destinations


def _shape_scalar_pairs(data, seen=None, is_row=False):
    """Set collection style rather than rewriting emitted scalar text.

    YAML 1.2.2 (2021), section 7.4.1 defines flow sequences. The pair length
    is the existing shaping API's formatting choice, not an engineering limit.
    """
    if seen is None:
        seen = set()
    if id(data) in seen:
        return
    seen.add(id(data))
    if isinstance(data, Mapping):
        for value in data.values():
            _shape_scalar_pairs(value, seen)
    elif isinstance(data, CommentedSeq):
        if (
            is_row
            and len(data) == 2
            and all(
                not isinstance(
                    value, (Mapping, list, LiteralScalarString, FoldedScalarString)
                )
                for value in data
            )
        ):
            data.fa.set_flow_style()
        for value in data:
            _shape_scalar_pairs(value, seen, is_row=True)


def save_yml(data, output_file_path, shape_output=False):
    """Round-trip dump a mapping to a YAML file, preserving comments/formatting.

    This is the single, reusable ruamel round-trip writer for the library. It is
    used by the YAML-split feature and by ``saveData.saveDataYaml`` ("ruamel" /
    "round_trip_dump" modes) so all round-trip saves share one implementation.

    Args:
        data: A (Commented)Mapping or plain dict to dump.
        output_file_path: Destination path (parent dirs are created as needed).
        shape_output: When True, writes nested two-scalar rows in compact
            ``- [a, b]`` flow form without changing values or the input object.

    Returns:
        The ``output_file_path`` that was written.
    """
    if shape_output:
        # Materialize round-trip nodes for plain dictionaries too. Parsing this
        # private copy preserves comments and avoids mutating caller-owned data.
        buffer = StringIO()
        _new_yaml().dump(data, buffer)
        data = _new_yaml().load(buffer.getvalue())
        _shape_scalar_pairs(data)

    output_dir = os.path.dirname(output_file_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    with open(output_file_path, "w", encoding="utf-8-sig") as f:
        _new_yaml().dump(data, f)

    return output_file_path


def split_yaml_file_by_primary_key(
    input_file, output_dir, shape_output=False, single_line_keys_skipped=True
):
    """Split a YAML file into one file per top-level (primary) key.

    Each output file is written via :func:`save_yml` so comments/formatting are
    preserved through a ruamel round-trip. Single-line scalar primary keys are
    skipped by default (the split targets block/mapping/sequence sections), which
    matches the existing engine behaviour.

    Args:
        input_file: Path to the multi-section YAML file to split.
        output_dir: Directory to write the per-key files into (created if absent).
        shape_output: Forwarded to :func:`save_yml` for compact list shaping.
        single_line_keys_skipped: When True, scalar single-line primary keys are
            not emitted as their own file.

    Returns:
        List of dicts ``[{"data": <output_file_path>}, ...]`` (one per emitted key).
    """
    handler = RuamelYAML()
    _, data = handler.load_clean_yaml_file(input_file)
    keys = [
        key
        for key, value in data.items()
        if not single_line_keys_skipped or not _single_line_scalar(value)
    ]
    destinations = _split_destinations(keys, input_file, output_dir)

    output_file_name_array = []
    for key, output_file_path in destinations:
        # Copy the round-trip mapping to retain root key quotes and comments.
        section = data.copy()
        for other_key in data:
            if other_key != key:
                del section[other_key]
        save_yml(section, output_file_path, shape_output=shape_output)
        output_file_name_array.append({"data": output_file_path})

    logger.debug(
        f"Split {input_file} into {len(output_file_name_array)} file(s) by primary key"
    )
    return output_file_name_array


class RuamelYAML:
    """
    ruamel yaml module for handling YAML files.
    This class mainly divides YAML files by primary keys.
    """

    def __init__(self):
        pass

    def router(self, cfg):
        if "yml_analysis" in cfg and cfg["yml_analysis"]["divide"]["flag"]:
            self.divide_yaml_files(cfg)
        else:
            raise NotImplementedError("No divide method specified")

        return cfg

    def divide_yaml_files(self, cfg) -> None:
        """
        Iterate through yml files
        """
        yml_files = cfg["file_management"]["input_files"]["yml"]
        cfg[cfg["basename"]] = {"divide": {"groups": []}}
        for file_name in yml_files:
            cfg_divide = cfg["yml_analysis"]["divide"]
            if cfg_divide["by"] == "primary_key":
                logger.debug("Splitting primary keys data START...")
                output_file_name_array = self.divide_yaml_file_by_primary_keys(
                    cfg, file_name
                )
                cfg[cfg["basename"]]["divide"]["groups"].append(output_file_name_array)
            else:
                raise Exception("No divide by method specified")

    def get_primary_key_single_line_info(self, cleaned_yaml):
        """Classify parsed values, including quoted keys and flow collections.

        YAML 1.2.2 (2021), sections 7.4 and 8.1, distinguishes collections
        from scalars independently of whether their spelling occupies one line.
        """
        data = _new_yaml().load(cleaned_yaml)
        if not isinstance(data, Mapping):
            raise ValueError("YAML splitting requires a top-level mapping")
        return {key: _single_line_scalar(value) for key, value in data.items()}

    def divide_yaml_file_by_primary_keys(self, cfg, file_name):
        """Engine entry point — delegates to the reusable module-level splitter.

        Backward compatible: returns the same ``[{"data": path}, ...]`` structure
        and honours ``cfg["yml_analysis"]["shape_output"]["flag"]``.
        """
        result_folder = cfg["Analysis"]["result_folder"]
        shape_output = cfg["yml_analysis"]["shape_output"]["flag"]

        output_file_name_array = split_yaml_file_by_primary_key(
            file_name, result_folder, shape_output=shape_output
        )

        logger.debug("Splitting primary keys data FINISH...")
        return output_file_name_array

    def load_clean_yaml_file(self, file_name):
        with open(file_name, encoding="utf-8-sig") as file:
            yaml_content = file.read()

            # Parse the original document: percent signs, blank lines and '---'
            # inside scalars are data (YAML 1.2.2, sections 6.8, 7.3 and 8.1).
            data = _new_yaml().load(yaml_content)

        if not isinstance(data, Mapping):
            raise ValueError("YAML splitting requires a top-level mapping")

        return yaml_content, data

    def clean_yaml_line(self, line):
        """
        Cleans a single line of YAML by removing invalid tokens or characters.
        """
        if "%" in line:
            line = re.sub(
                r"(\s*[^:]+:\s*)%([^%]+)%", r'\1"\2"', line
            )  # Wrap %...% in quotes
        return line

    def clean_yaml_file(self, yaml_content):
        """
        Cleans the entire YAML content by removing invalid lines and tokens.
        """
        cleaned_lines = []
        for line in yaml_content.splitlines():
            cleaned_line = self.clean_yaml_line(line)
            if cleaned_line:
                cleaned_lines.append(cleaned_line)
        return "\n".join(cleaned_lines)

    def extract_data_after_document_start(self, yaml_content):
        """
        Extracts the YAML content after the document start symbol (---).
        """
        # Split the content by the document start symbol
        parts = yaml_content.split("---", 1)
        if len(parts) > 1:
            return parts[1].strip()  # Return the content after '---'
        return yaml_content
