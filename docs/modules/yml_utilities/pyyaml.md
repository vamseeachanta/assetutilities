# PyYaml

PyYAML is a Python library that provides a set of tools for parsing YAML files.

## PyYAML dumping

Yaml.dump() function provides several parameters to customize the output.


```yaml
data: object  # Data to serialize
default_flow_style: bool | None  # False for block style, True for inline flow style
sort_keys: bool  # Sort keys alphabetically in the output
indent: int  # Number of indentation spaces
allow_unicode: bool  # Encode non-ASCII characters as Unicode
width: int  # Max line width for better readability
explicit_start: bool  # Add `---` at the beginning of the YAML document
explicit_end: bool  # Add `...` at the end of the YAML document
dumper: DumperType  # Custom dumper for advanced configurations
```


## Dumper Types

| **Dumper Type** | **Description** |
|-----------------|------------------|
| `yaml.Dumper`    | Default dumper, commonly used. |
| `yaml.SafeDumper`| Safer option, recommended for untrusted data. Prevents executing arbitrary Python objects. |
| `yaml.CDumper`   | A faster C-based implementation, suitable for improved performance. |
| `yaml.CSafeDumper`| Faster and safer C-based dumper, combining speed and security. |

---

## Example Usage with Dumper Types

```python
import yaml

data = {'message': 'Hello, World!', 'status': True}

# Using SafeDumper for better security
yaml_str = yaml.dump(data, Dumper=yaml.SafeDumper)
print(yaml_str)
```


**Note:** PyYAML is not suitable for well-formatting YAML file data ; `ruamel.yaml` is best for it's advanced level of handling complex yml files without even explicitly including some conditions.

- Documentation is written in : ![alt text](ruamel_yaml.md)