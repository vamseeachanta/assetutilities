# PyYaml

PyYAML is a Python library that provides a set of tools for parsing YAML files.


#### while loading yml file encountered below error 


❗[ERROR] Exception has occurred: ScannerError ✖
yaml.scanner.ScannerError: while scanning for the next token found character '%' that cannot start any token❗


**code fix :**

```python
with open(file_name, "r", encoding='utf-8-sig') as file:
    yaml_content = file.read()
    
    # Clean the YAML content
    cleaned_yaml = self.clean_yaml_file(yaml_content)
    
    data = yaml.load(cleaned_yml)

def clean_yaml_file(self,yaml_content):
    """
    Cleans the entire YAML content by removing invalid lines and tokens.
    """
    cleaned_lines = []
    for line in yaml_content.splitlines():
        cleaned_line = self.clean_yaml_line(line)
        if cleaned_line:
            cleaned_lines.append(cleaned_line)
    return '\n'.join(cleaned_lines)

def clean_yaml_line(self,line):
    """
    Cleans a single line of YAML by removing invalid tokens or characters.
    """
    if '%' in line:
        line = re.sub(r'(\s*[^:]+:\s*)%([^%]+)%', r'\1"\2"', line)  # Wrap %...% in quotes
    return line
```

## PyYAML dump

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

---

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

---


> **Note:** PyYAML is not suitable for well-formatting YAML file data ; `ruamel.yaml` is best for it's advanced level of handling complex yml files without even explicitly including some conditions.

---

## PyYAML vs ruamel.yaml 

| Feature                     | PyYAML                   | ruamel.yaml |
|-----------------------------|:------------------------:|:------------:|
| Precise Indentation        | ❌                        | ✅          |
| Maintains Key Order        | ✅ (with `sort_keys=False`) | ✅        |
| Preserve comments            | ❌                        | ✅        |
| Controls Quoting Style      | ❌                        | ✅         |

---

### ruamel.yml

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


## References

- <https://pyyaml.org/wiki/PyYAMLDocumentation>
- <https://yaml.dev/doc/ruamel.yaml/>







