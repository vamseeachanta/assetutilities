import os
import re
from pathlib import Path

from loguru import logger
from ruamel.yaml import YAML as ruamelYAML

# from ruamel.yaml.comments import CommentedMap

ruamel_yaml = ruamelYAML()
ruamel_yaml.preserve_quotes = True  # Keeps quotes if present
ruamel_yaml.allow_duplicate_keys = True  # Allows duplicate keys if required
ruamel_yaml.indent(mapping=2, sequence=4, offset=2)


def save_yml(data, output_file_path, shape_output=False):
    """Round-trip dump a mapping to a YAML file, preserving comments/formatting.

    This is the single, reusable ruamel round-trip writer for the library. It is
    used by the YAML-split feature and by ``saveData.saveDataYaml`` ("ruamel" /
    "round_trip_dump" modes) so all round-trip saves share one implementation.

    Args:
        data: A (Commented)Mapping or plain dict to dump.
        output_file_path: Destination path (parent dirs are created as needed).
        shape_output: When True, post-processes nested 2-element lists into the
            compact ``- [a, b]`` flow form (matches the repo's shaped output).

    Returns:
        The ``output_file_path`` that was written.
    """
    output_dir = os.path.dirname(output_file_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    with open(output_file_path, "w", encoding="utf-8-sig") as f:
        ruamel_yaml.dump(data, f)

    if shape_output:
        with open(output_file_path, encoding="utf-8-sig") as f:
            content = f.read()
        modified_content = re.sub(
            r"-\s+-\s+([^\n]+)\n\s+-\s+([^\n]+)", r"- [\1, \2]", content
        )
        with open(output_file_path, "w", encoding="utf-8-sig") as f:
            f.write(modified_content)

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
    os.makedirs(output_dir, exist_ok=True)
    file_name_stem = Path(input_file).stem

    handler = RuamelYAML()
    cleaned_yaml, data = handler.load_clean_yaml_file(input_file)
    primary_key_info = handler.get_primary_key_single_line_info(cleaned_yaml)

    output_file_name_array = []
    for key in data.keys():
        if single_line_keys_skipped and primary_key_info.get(key, False):
            continue

        output_file_name = f"{file_name_stem}_{key}.yml"
        output_file_path = os.path.join(output_dir, output_file_name)
        save_yml({key: data[key]}, output_file_path, shape_output=shape_output)
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
        """Map each top-level key -> True if it is a single-line scalar value.

        A key is "single line" when it has inline content after the colon and the
        following line is neither indented (a continuation) nor a blank separator.
        """
        lines = cleaned_yaml.splitlines()
        primary_key_info = {}

        for i, line in enumerate(lines):
            key_match = re.match(r"^([^:]+):", line)
            if key_match:
                current_key = key_match.group(1).strip()
                value_part = line[key_match.end() :].strip()

                # Single-line if there is inline content after the colon.
                is_single_line = bool(value_part)

                # Look ahead: an indented or blank next line means a block value.
                if is_single_line and i + 1 < len(lines):
                    next_line = lines[i + 1]
                    if next_line and (next_line[0].isspace() or not next_line.strip()):
                        is_single_line = False

                primary_key_info[current_key] = is_single_line

        return primary_key_info

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

            cleaned_yaml = self.clean_yaml_file(yaml_content)
            cleaned_yaml = self.extract_data_after_document_start(cleaned_yaml)

            data = ruamel_yaml.load(cleaned_yaml)

        return cleaned_yaml, data

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
