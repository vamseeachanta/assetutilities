# YAML Variables and placeholders:

This document demonstrates three common YAML usage patterns in Python-based config systems:

- Single Variable Access
- Nested Block Access
- Jinja2 Templated Placeholders

---

## 1. YAML Single Variable

### 📘 Description

A simple scalar value in YAML that can be directly accessed in Python.

**config.yml :**

```yaml
meta:
  basename: yaml_utilities
  library: assetutilities

define: &label fsts_l015_hwl_125km3_l100_sb

data:
    input_format: csv
    groups:
      -
        label: *label
        target:
          template: collated\template_WLNG_FSTs_LNGC.xlsx
```

**Python Test Logic**

```python
label = cfg['data']['groups'][0]['label']
- fsts_l015_hwl_125km3_l100_sb

```

## 2. YAML Nested Block Access
### 📘 Description
Defines a dictionary block (object) inside YAML with multiple nested keys.

**config.yml :**

```yaml
meta:
  basename: yaml_utilities
  library: assetutilities

define: &output_config
  template: collated/template_block_template.xlsx
  filename: collated/output_block_file.xlsx

data:
    input_format: csv
    groups:
      -
        target: *output_config
```

**Python Test Logic**

```python

target_block = cfg['data']['groups'][0]['target'] - output_config
block_nested_value = target_block['template'] - collated/template_block_template.xlsx

```

## 3. YAML Jinja2 Placeholders

### 📘 Description

A Jinja2 template placeholder in YAML that can be rendered with Python.
**config.yml :**

```yaml
meta:
  basename: yaml_utilities
  library: assetutilities

test_variables:
  flag: True
  method: placeholder

placeholder_tests:
  method: "{{ test_variables.method }}"
  library: "{{ meta.library }}"
```

**Python Test Logic**

```python

cfg = self.process_placeholders(cfg, cfg)

method = cfg['placeholder_tests']['method']
logger.debug("yml key placeholder is reusable:", method)
```
