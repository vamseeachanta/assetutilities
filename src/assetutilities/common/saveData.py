import json
from collections import OrderedDict

import yaml
from yaml import SafeDumper

noalias_dumper = yaml.dumper.SafeDumper
noalias_dumper.ignore_aliases = lambda self, data: True


def saveDataJson(data, fileName):
    with open(fileName + ".json", "w") as f:
        json.dump(data, f)


class OrderedDumper(SafeDumper):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        def represent_dict_order(self, data):
            return self.represent_mapping(
                    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, data.items()
                )
        self.add_representer(OrderedDict, represent_dict_order)


def dump_ordered_yaml(ordered_data, output_filename, Dumper=yaml.Dumper):
    class OrderedDumper(Dumper):
        pass

    class UnsortableList(list):
        def sort(self, *args, **kwargs):
            pass

    class UnsortableOrderedDict(OrderedDict):
        def items(self, *args, **kwargs):
            return UnsortableList(OrderedDict.items(self, *args, **kwargs))

    OrderedDumper.add_representer(
        UnsortableOrderedDict, yaml.representer.SafeRepresenter.represent_dict
    )
    with open(output_filename, "w") as f:
        yaml.dump(ordered_data, f, Dumper=OrderedDumper)


def dump_ordered(dictionary):
    """
    Dump ordered dictionary
    """
    yaml.add_representer(
        OrderedDict,
        lambda dumper, data: dumper.represent_mapping(
            "tag:yaml.org,2002:map", data.items()
        ),
    )

    return yaml.dump(dictionary)


def saveDataYaml(data, fileName, default_flow_style=False):
    #     setup_yaml()
    if default_flow_style is None:
        with open(fileName + ".yml", "w") as f:
            yaml.dump(data, f)
    elif default_flow_style == "NonAlias":
        with open(fileName + ".yml", "w") as f:
            yaml.dump(data, f, Dumper=noalias_dumper)
    elif default_flow_style == "OrderedDumper":
        with open(fileName + ".yml", "w") as f:
            yaml.dump(data, f, Dumper=OrderedDumper)
    elif default_flow_style in ("ruamel", "round_trip_dump"):
        # Round-trip (comment/format preserving) dump via the shared ruamel helper.
        # Previously these branches referenced an unimported ``ruamel`` symbol and
        # raised NameError; they now delegate to the canonical ruamel utility so the
        # YAML-split feature and these save paths share one round-trip implementation.
        from assetutilities.modules.yml_utilities.ruamel_yaml import save_yml

        save_yml(data, fileName + ".yml")
    else:
        with open(fileName + ".yml", "w") as f:
            yaml.dump(data, f, default_flow_style=default_flow_style)


def saveDataFrame(df, fileName):
    df.to_csv("results\\catenary\\" + fileName + ".csv")


def setup_yaml():
    """https://stackoverflow.com/a/8661021"""
    def represent_dict_order(self, data):
        return self.represent_mapping(
            "tag:yaml.org,2002:map", data.items()
        )
    yaml.add_representer(OrderedDict, represent_dict_order)
