## ruamel.yml

ruamel is very powerful and advanced parsing library for complex yml files.

Since PyYAML does not provide fine-grained control over indentation ,
This library allows you to maintain the exact structure and indentation from the original YAML file.

```python
pip install ruamel.yaml
```

```python
from ruamel.yaml import YAML

yaml = YAML()
yaml.preserve_quotes = True  # Keeps quotes if present
yaml.indent(mapping=2, sequence=4, offset=2)  # Ensures correct indentation

# Read the original YAML file
with open("main.yml", "r") as file:
    data = yaml.load(file)

# Save it back to a new file while preserving formatting
result_folder = cfg['Analysis']['result_folder']
output_file_name = "output.yml"
output_file_path = os.path.join(result_folder, output_file_name)
with open(output_file_path, "w") as file:
    yaml.dump(data, file)
```

## PyYAML vs ruamel.yaml 

| Feature                     | PyYAML                   | ruamel.yaml |
|-----------------------------|:------------------------:|:------------:|
| Precise Indentation        | ❌                        | ✅          |
| Maintains Key Order        | ✅ (with `sort_keys=False`) | ✅        |
| Preserve comments            | ❌                        | ✅        |
| Controls Quoting Style      | ❌                        | ✅         |



## References

- <https://pyyaml.org/wiki/PyYAMLDocumentation>
- <https://yaml.dev/doc/ruamel.yaml/>