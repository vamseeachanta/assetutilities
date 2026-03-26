## 📂 File Management Filters (Scenarios) for getting input files

The following filters can be configured under `file_management` to control which files are selected:

1. **contains**
   - Includes files that contain all specified substrings in their name.

2. **not_contains**
   - Excludes files that contain any of the specified substrings.

**Example usage :**

```yaml
filters:
    contains: [QA_items]
    not_contains: [QA_values_changed]

✔️ Matches: wwyaml_SZ_trim_QA_items.yaml
❌ Skips: wwyaml_SZ_trim_QA_values_changed.yaml

```

3. **regex**
   - Includes files whose names match any of the given regular expressions.
```yaml
filters:
  regex: '^[a-z]{2}_[0-9]{4}_.*$'  # 2 letters + _ + 4 digits + _ + anything
    
✔️ Matches: us_2024_items.yaml
❌ Skips: india_weather_report.yaml
```          

4. **min_size_kb / max_size_kb**
   - Filters files based on their size (in kilobytes).

```yaml
filters:
  min_size_kb: 10       
  max_size_kb: 40 

✔️ Matches: wwyaml_SZ_trim_items.yaml - 15kb
✔️ Matches: wwyaml_SZ_trim.yaml - 30 kb
❌ Skips: wwyaml_SZ_trim_QA_values.yaml - 8kb
❌ Skips: wwyaml_SZ_trim_QA_changed.yaml - 50kb

```
## 📊  Comparison table of filters ( best to least preferred )

| Rank | Filter           | Purpose                                     | Preference Reason                                      |
|------|------------------|---------------------------------------------|--------------------------------------------------------|
| 1️⃣  | contains and not_contains         | mostly cover all file names   | Most readable, predictable, and intuitive              |                |
| 2️⃣  | min_size_kb / max_size_kb | useful when same names exists      | Ensures data completeness or avoids oversized files    |
| 3️⃣  | regex             | Advanced pattern matching             | Powerful but harder to maintain 


> ✅ `contains` + `not_contains` are enough in most cases for getting files. 


**Run tests for better understanding :**

- `tests\modules\file_management\test_file_management.py`

**Note: Code can be inspected in :** 

- `src\assetutilities\common\file_management.py`