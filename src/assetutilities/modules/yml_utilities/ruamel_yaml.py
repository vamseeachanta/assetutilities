from ruamel.yaml import YAML as ruamelYAML


ruamel_yaml = ruamelYAML()
ruamel_yaml.preserve_quotes = True  # Keeps quotes if present 
ruamel_yaml.allow_duplicate_keys = True  # Allows duplicate keys if required
ruamel_yaml.indent(mapping=2, sequence=4, offset=2) 


class RuemelYAML:
    """
    A wrapper around the ruamel.yaml library to provide a consistent interface for YAML operations.
    """

    def __init__(self):
        self.yaml = ruamel_yaml

    def load(self, stream):
        return self.yaml.load(stream)

    def dump(self, data, stream=None, **kwargs):
        return self.yaml.dump(data, stream, **kwargs)

    def save_to_file(self, data, output_file_path, **kwargs):
        with open(output_file_path, "w", encoding='utf-8-sig') as f:
            ruamel_yaml.dump(data, f, **kwargs)

