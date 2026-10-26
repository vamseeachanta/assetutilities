from __future__ import annotations

# Standard library imports
import importlib.util

# import logging
import os
import pkgutil
import re
from collections.abc import Mapping, MutableMapping
from copy import deepcopy
from pathlib import Path
from typing import Any

# Third party imports
import yaml  # type: ignore[import-untyped]
import yaml.composer  # type: ignore[import-untyped]
from deepdiff import DeepDiff
from loguru import logger

# Reader imports
from assetutilities.common.data import ReadData
from assetutilities.common.saveData import saveDataYaml
from assetutilities.common.utilities import (
    get_common_name_from_2_filenames,
    is_file_valid_func,
)
from assetutilities.common.visualization.visualization_templates_matplotlib import (
    VisualizationTemplates,
)
from assetutilities.modules.yml_utilities.ruamel_yaml import RuamelYAML

# from assetutilities.engine import engine as aus_engine

viz_templates = VisualizationTemplates()

read_data = ReadData()
ruamel_yaml_utilities = RuamelYAML()


def represent_none(self: Any, _: Any) -> Any:
    return self.represent_scalar("tag:yaml.org,2002:null", "~")


yaml.add_representer(type(None), represent_none)


def ymlInput(
    defaultYml: str, updateYml: str | None = None, *, placeholders: bool = False
) -> dict[str, Any]:
    return WorkingWithYAML().ymlInput(defaultYml, updateYml, placeholders=placeholders)


def update_deep(
    d: MutableMapping[str, Any], u: Mapping[str, Any]
) -> MutableMapping[str, Any]:
    return WorkingWithYAML().update_deep(d, u)


def resolve_placeholders(data: Any, context: Mapping[str, Any] | None = None) -> Any:
    """Copy a tree, replacing scalar ``{{ dotted.mapping.key }}`` references.

    Resolution is a single pass against the original context. Missing keys,
    expressions, functions, attributes and template control blocks stay literal.
    Mapping keys take precedence even when named ``items`` or ``values``.
    Native YAML anchors/aliases are handled by the safe loader before this step.
    """
    if context is None:
        context = data if isinstance(data, Mapping) else {}
    pattern = re.compile(
        r"{{\s*([A-Za-z][A-Za-z0-9_]*(?:\.[A-Za-z][A-Za-z0-9_]*)*)\s*}}"
    )
    active = set()

    def substitute(match):
        value = context
        for key in match.group(1).split("."):
            if not isinstance(value, Mapping) or key not in value:
                return match.group(0)
            value = value[key]
        if value is None or type(value) in (str, int, float, bool):
            return str(value)
        return match.group(0)

    def walk(value):
        if isinstance(value, str):
            if "{%" in value or "{#" in value:
                return value
            return pattern.sub(substitute, value)
        if isinstance(value, (Mapping, list)):
            identity = id(value)
            if identity in active:
                raise ValueError(
                    "Cyclic YAML aliases cannot be resolved as placeholders"
                )
            active.add(identity)
            try:
                if isinstance(value, Mapping):
                    return {key: walk(item) for key, item in value.items()}
                return [walk(item) for item in value]
            finally:
                active.remove(identity)
        return value

    return walk(data)


def resolve_config_placeholders(cfg: dict[str, Any]) -> dict[str, Any]:
    """Opt in with ``yaml_options.resolve_placeholders: true`` in a config.

    Mutate the top-level mapping to preserve AttributeDict and caller identity.
    Select the basename before substitution; placeholders cannot choose code.
    """
    options = cfg.get("yaml_options")
    if options is None:
        options = {}
    if options.get("resolve_placeholders", False):
        resolved = resolve_placeholders(cfg)
        cfg.clear()
        cfg.update(resolved)
    return cfg


class WorkingWithYAML:
    """
    yaml utilities module for handling YAML files.

    """

    def __init__(self) -> None:
        pass

    def router(self, cfg: dict[str, Any]) -> dict[str, Any]:
        if (
            "yml_analysis" in cfg
            and cfg["yml_analysis"]["divide"]["technique"] == "ruamel_yml"
        ):
            ruamel_yaml_utilities.router(cfg)
        elif "plot_yml_data" in cfg and cfg["plot_yml_data"]["flag"]:
            cfg = self.get_plotting_data(cfg)
            cfg = self.plot_yml_data(cfg)
        elif "test_variables" in cfg and cfg["test_variables"]["flag"]:
            self.test_variables(cfg)

        return cfg

    def get_plotting_data(self, cfg: dict[str, Any]) -> dict[str, Any]:
        groups_key_chain = cfg["data"]["groups_key_chain"]
        groups = deepcopy(groups_key_chain)
        for group_idx, group in enumerate(groups_key_chain):
            for x_list_idx, x_list in enumerate(group["x"]):
                x_list_values = self.get_data_from_file_keychain(cfg, x_list)
                groups[group_idx]["x"][x_list_idx] = x_list_values
            for y_list_idx, y_list in enumerate(group["y"]):
                y_list_values = self.get_data_from_file_keychain(cfg, y_list)
                groups[group_idx]["y"][y_list_idx] = y_list_values

        cfg["data"]["groups"] = groups.copy()

        return cfg

    def get_data_from_file_keychain(
        self, cfg: dict[str, Any], file_keychain: dict[str, Any]
    ) -> Any:
        file_name = file_keychain["file_name"]
        key_chain = file_keychain["key_chain"]

        if not os.path.isfile(file_name):
            file_name = os.path.join(cfg["Analysis"]["analysis_root_folder"], file_name)
            if not os.path.isfile(file_name):
                raise FileNotFoundError(f"File {file_name} does not exist.")

        # file_name_dict = self.ymlInput(file_name)
        # cleaned_yaml, ruamel_data_dict = ruamel_yaml_utilities.load_clean_yaml_file(file_name)
        # safe_yaml = YAML(typ='safe')
        # ruamel_data_dict = safe_yaml.load(cleaned_yaml)

        data = self.load_yml_with_utf_8_sig(file_name)

        for key in key_chain:
            data = data[key].copy() if isinstance(data, dict) else data[int(key)]

        return data

    def plot_yml_data(self, cfg: dict[str, Any]) -> dict[str, Any]:
        from assetutilities.engine import engine as au_engine

        plot_yml = viz_templates.get_xy_line_input(cfg["Analysis"].copy())
        plot_yml["settings"].update(cfg["settings"].copy())

        file_name = os.path.join(
            cfg["Analysis"]["result_plot_folder"], cfg["Analysis"]["file_name"]
        )
        plot_yml["settings"]["file_name"] = file_name

        plot_yml["data"] = cfg["data"].copy()

        au_engine(inputfile=None, cfg=plot_yml, config_flag=False)  # type: ignore[arg-type]
        return cfg

    def ymlInput(
        self,
        defaultYml: str,
        updateYml: str | None = None,
        *,
        placeholders: bool = False,
    ) -> dict[str, Any]:
        if not is_file_valid_func(defaultYml):
            raise FileNotFoundError("Not valid file. Please check the file path.")

        cfg: dict[str, Any]
        with open(defaultYml, encoding="utf-8") as ymlfile:
            try:
                cfg = yaml.safe_load(ymlfile)  # type: ignore[assignment]
            except yaml.composer.ComposerError as e:
                logger.error(f"YAML parsing error: {e}")
                cfg = self.yml_read_stream(defaultYml)

        if updateYml is not None:
            #  Update values file
            try:
                with open(updateYml, encoding="utf-8") as ymlfile:
                    cfgUpdateValues = yaml.safe_load(ymlfile)
                #  Convert to logs
                # logger.info(cfgUpdateValues)
                cfg = update_deep(cfg, cfgUpdateValues)  # type: ignore[assignment]
            except (
                OSError,
                yaml.YAMLError,
                TypeError,
                ValueError,
                AttributeError,
            ) as e:
                # Surface the cause; this handler previously discarded it
                # entirely (issue #80). Fallback behaviour is unchanged.
                logger.info(
                    "Update Input file could not be loaded successfully. Running program default values"
                )
                logger.info(f"Error is : {e}")

        if placeholders:
            cfg = resolve_placeholders(cfg)
        return cfg

    def yml_read_stream(self, yaml_file_name: str) -> dict[str, Any]:
        # PyYAML documentation, "safe_load_all": only standard YAML tags.
        # Validate the complete stream before merging; a late parse/tag error
        # must not return a partially accepted configuration.
        with open(yaml_file_name, encoding="utf-8") as ymlfile:
            documents = list(yaml.safe_load_all(ymlfile))
        stream_dict: dict[str, Any] = {}
        for document in documents:
            if document is None:
                continue
            if not isinstance(document, Mapping):
                raise TypeError("Each YAML configuration document must be a mapping")
            stream_dict = update_deep(stream_dict, document)
        return stream_dict

    def update_deep(
        self, d: MutableMapping[str, Any], u: Mapping[str, Any]
    ) -> MutableMapping[str, Any]:
        for k, v in u.items():
            # this condition handles the problem
            if not isinstance(d, Mapping):
                d = u
            elif isinstance(v, Mapping):
                r = update_deep(d.get(k, {}), v)
                d[k] = r
            else:
                d[k] = v

        return d

    def load_yml_with_utf_8_sig(self, file_name: str) -> Any:
        with open(file_name, encoding="utf-8") as stream:
            return yaml.safe_load(stream)

    def analyze_yaml_keys(self, file_name: str) -> None:
        """
        Analyze Yaml file
        """
        file_name_content = ymlInput(file_name)
        logger.info(file_name_content.keys())

    def compare_yaml_root_keys(self, file_name1: str, file_name2: str) -> None:
        """
        Compare 2 yaml files
        """

        file_name1_content = ymlInput(file_name1)
        file_name2_content = ymlInput(file_name2)
        file_name1_keys = file_name1_content.keys()
        file_name2_keys = file_name2_content.keys()
        if file_name1_keys == file_name2_keys:
            logger.info("Yaml files have the same root keys")
        else:
            logger.info(f"The root keys for {file_name1}: {file_name1_keys}")
            logger.info(f"The root keys for {file_name2}: {file_name2_keys}")

    def compare_yaml_files_deepdiff(self, cfg: dict[str, Any]) -> None:
        """
        Compare 2 yaml files using DeepDiff
        """
        file_name1 = cfg["file_name1"]
        file_name2 = cfg["file_name2"]
        file_name1_content = ymlInput(file_name1)
        file_name2_content = ymlInput(file_name2)
        file_diff = DeepDiff(file_name1_content, file_name2_content, ignore_order=True)
        if file_diff == {}:  # if there is no difference
            logger.info("Yaml files are the same")
        else:
            # get file root directory
            file_directory = os.path.dirname(file_name1)
            uniquebasename = get_common_name_from_2_filenames(file_name1, file_name2)
            self.save_diff_files(file_diff, file_directory, uniquebasename)

    def compare_yaml_file_contents_deepdiff(self, cfg: dict[str, Any]) -> None:
        file_name1 = cfg["file_name1"]
        file_name2 = cfg["file_name2"]

        file_name1_content = read_data.key_chain(
            ymlInput(file_name1), *cfg["map_list"]["file_name1"]
        )
        file_name2_content = read_data.key_chain(
            ymlInput(file_name2), *cfg["map_list"]["file_name2"]
        )

        file_diff = DeepDiff(file_name1_content, file_name2_content, ignore_order=True)

        self.save_diff_files(file_diff, cfg)

    def save_diff_files(
        self,
        file_diff: dict[str, Any],
        cfg: dict[str, Any],
        deepdiff_save: bool = False,
    ) -> None:
        file_name1 = cfg["file_name1"]
        file_name2 = cfg["file_name2"]
        if file_diff == {}:  # if there is no difference
            logger.info("Yaml files are the same")
        else:
            # get file root directory
            file_directory = os.path.dirname(file_name1)
            uniquebasename = get_common_name_from_2_filenames(file_name1, file_name2)

            # save the entire diff file. A very messy and overwhelming file
            if deepdiff_save:
                saveDataYaml(
                    file_diff, f"{file_directory}/wwyaml_{uniquebasename}_deepdiff"
                )

            file_name = f"{file_directory}/wwyaml_{uniquebasename}_updated_values.yml"
            with open(file_name, "w", encoding="utf-8", newline="\n") as f:
                f.writelines(
                    f"{key}: {value['new_value']}\n"
                    for key, value in file_diff.get("values_changed", {}).items()
                )

            saveDataYaml(
                dict(file_diff), f"{file_directory}/wwyaml_{uniquebasename}_items"
            )

            saveDataYaml(
                dict(file_diff)["values_changed"],
                f"{file_directory}/wwyaml_{uniquebasename}_values_changed",
            )

            logger.info(
                "Yaml files are different. See wwyaml files saved in the current file directory"
            )

    def get_library_yaml_file(self, cfg: dict[str, Any]) -> Any:
        library_yaml_filename = cfg["filename"]
        library_name = cfg["library_name"]
        if os.path.isfile(library_yaml_filename):
            with open(library_yaml_filename, encoding="utf-8") as ymlfile:
                library_yaml = yaml.safe_load(ymlfile)
        else:
            data = pkgutil.get_data(library_name, cfg["filename"])
            library_yaml = yaml.safe_load(data)

        return library_yaml

    def get_library_filename(self, cfg: dict[str, Any]) -> str:
        filename_with_lib_path: Any = cfg["filename"]
        library_name = cfg["library_name"]
        if not os.path.isfile(cfg["filename"]):
            lib_spec = importlib.util.find_spec(library_name)
            if lib_spec is None or lib_spec.origin is None:
                raise ImportError(f"Library '{library_name}' not found")
            lib_path = Path(lib_spec.origin).parent
            filename_with_lib_path = os.path.join(lib_path, cfg["filename"])
            if not os.path.isfile(filename_with_lib_path):
                raise FileNotFoundError()

        return str(filename_with_lib_path)

    def get_library_filepath(
        self, cfg: dict[str, Any], src_relative_location_flag: bool = False
    ) -> str:
        filepath_with_lib_path: Any = cfg["filepath"]
        library_name = cfg["library_name"]
        if not os.path.isabs(filepath_with_lib_path) or not os.path.isdir(
            filepath_with_lib_path
        ):
            lib_spec = importlib.util.find_spec(library_name)
            if lib_spec is None or lib_spec.origin is None:
                raise ImportError(f"Library '{library_name}' not found")
            lib_path = Path(lib_spec.origin).parent
            if not src_relative_location_flag:
                lib_path = lib_path.parents[1]
            filepath_with_lib_path = os.path.join(lib_path, cfg["filepath"])
            if not os.path.isdir(filepath_with_lib_path):
                raise FileNotFoundError()

        return str(filepath_with_lib_path)

    def test_variables(self, cfg: dict[str, Any]) -> dict[str, Any]:
        if cfg["test_variables"]["method"] == "single":
            _flag, _label = self.test_single_variable(cfg)
        elif cfg["test_variables"]["method"] == "directive_block":
            _flag, _label = self.test_directive_block(cfg)
        elif cfg["test_variables"]["method"] == "placeholder":
            _flag, _label = self.test_variable_placeholder(cfg)

        return cfg

    def test_single_variable(self, cfg: dict[str, Any]) -> tuple[bool, Any]:
        try:
            label = cfg["data"]["groups"][0]["label"]
            logger.info("Label is reusable: {}", label)
            return True, label
        except KeyError as e:
            logger.error("Label cannot be accesible:", e)
            return False, None

    def test_directive_block(self, cfg: dict[str, Any]) -> tuple[bool, Any]:
        try:
            target_block = cfg["data"]["groups"][0]["target"]
            target_block["template"]
            logger.debug("block and it's nested value reusable:")
            return True, target_block
        except KeyError as e:
            logger.error("Directive block not accessible:", e)
            return False, None

    def test_variable_placeholder(self, cfg: dict[str, Any]) -> tuple[bool, Any]:
        cfg = self.process_placeholders(cfg, cfg)
        try:
            method = cfg["placeholder_tests"]["method"]
            logger.info("yml key placeholder is reusable: {}", method)
            return True, method
        except KeyError as e:
            logger.error("yml key cannot be accesible:", e)
            return False, None

    def process_placeholders(
        self, data: Any, context: dict[str, Any] | None = None
    ) -> Any:
        """Resolve ``{{ key }}`` placeholders in a config tree (backwards-compatible alias).

        Thin wrapper around :func:`resolve_placeholders`. Retained so existing
        callers (``test_variable_placeholder`` and downstream code) keep working.

        Args:
            data: The value/tree to resolve. Usually the full ``cfg`` dict.
            context: Mapping that placeholders are rendered against. When
                ``None`` and ``data`` is a mapping, ``data`` itself is used as
                the context (the common "self-referential" YAML case).

        Returns:
            A new structure with every resolvable placeholder substituted.
        """
        return resolve_placeholders(data, context)
