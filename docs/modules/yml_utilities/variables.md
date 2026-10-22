# YAML configuration variables

Configuration loading resolves native YAML aliases and quoted Jinja placeholders.
Use aliases for a scalar or an entire block in one YAML document, and placeholders
for strings assembled from the final merged configuration. The normal application
configuration path now performs the same substitution as the standalone helper.

## Revision history

| Revision | Date | Change and reason |
| --- | --- | --- |
| A | 2026-10-19 | Document loading, merge order and a worked example so variable definitions can be reused consistently. |
| B | 2026-10-22 | Handle mixed YAML keys, add literal loading for comparisons, and clarify single-pass rendering and container limits. |

## Loading and merge order

```python
from assetutilities.common.yml_utilities import ymlInput

cfg = ymlInput("docs/modules/yml_utilities/examples/variables.yml")
assert cfg["output"] == "results/sample.csv"
assert cfg["placeholder_tests"]["method"] == "placeholder"
```

`WorkingWithYAML().ymlInput(defaultYml, updateYml=None, *, resolve_placeholders=True)`
and the module-level `ymlInput` wrapper parse YAML safely, merge the optional
update, and by default resolve placeholders against that final mapping.
Multi-document inputs are combined before substitution. Anchors are scoped to
their YAML document, not shared across files.

This default changes existing callers of these shared loaders immediately:
expressions such as `$10^{{3}}$` are rendered, and Jinja `{# ... #}` comments are
removed. For documents that contain literal template syntax, pass
`resolve_placeholders=False`; YAML document and update merging still apply.
The key-analysis and all three YAML comparison helpers always use this
parsing-only mode, so comparisons distinguish templates from rendered literals.

The application configuration path merges packaged defaults, custom YAML and
argument overrides before rendering. Embedded configuration renders the supplied
mapping before constructing filenames. Both paths therefore resolve labels before
using them in output names. A copy is returned; rendering does not mutate the
input tree or packaged defaults.

`resolve_placeholders(data, context=None)` is available for consumers that already
have a parsed configuration. It uses the input mapping as its context by default;
a supplied context replaces it. `WorkingWithYAML.process_placeholders` remains an
alias for this helper. Consumers should call it once, after their own final merge.

## Worked example: inputs, method and answer

The runnable [example input](examples/variables.yml) defines a scalar anchor
`&label sample` and a block anchor `&target` containing `folder: results`.
`data.groups` reuses these nodes with `*label` and `*target`.

Its placeholder input is:

```yaml
output: "{{ block.folder }}/{{ define }}.csv"
placeholder_tests:
  method: "{{ test_variables.method }}"
  library: "{{ meta.library }}"
```

The method is text substitution after YAML parsing and merging. Reading the input
by hand gives `block.folder = results`, `define = sample`,
`test_variables.method = placeholder` and `meta.library = assetutilities`.
Concatenating `results`, `/`, `sample` and `.csv` gives the answer:

```yaml
data:
  groups:
    - label: sample
      target:
        folder: results
output: results/sample.csv
placeholder_tests:
  method: placeholder
  library: assetutilities
```

To exercise the standard engine path, copy the example to a working output
folder, then run `engine(inputfile="variables.yml", root_folder=".")` from that
folder after importing `engine` from `assetutilities.engine`. This writes the
normal application configuration output in that folder.

No engineering equation, coefficient or acceptance threshold is involved.
Expected test values follow the substitutions written out above, independently
of the resolver implementation.

## Supported behavior and limits

- Quote placeholders so YAML parses them as strings. Dotted and bracket lookup,
  placeholders inside lists, and placeholders embedded in longer strings work.
  For keys that collide with mapping methods, use bracket lookup, such as
  `{{ settings['items'] }}`.
- Rendered values remain strings. Existing numbers, booleans and nulls keep their
  YAML types. Output text is never reparsed as YAML; punctuation and trailing
  newlines remain text. Mapping keys are not templated.
- Only string root keys enter the Jinja context. Integer, boolean and other
  non-string keys remain in the returned mapping without preventing string-key
  substitution. A nested non-string key can be referenced through bracket lookup.
- Rendering uses sandboxed Jinja with strict undefined lookup. An undefined,
  malformed, type-incompatible or sandbox-blocked template retains its original
  text. Rejected templates other than missing references produce a generic warning
  without including configuration values.
  Missing references do not constitute validation failures; callers needing
  required fields must validate those fields separately.
- Resolution is a single pass against the original merged context. For example,
  if `a` contains `{{ b }}` and `copy` contains `{{ a }}`, `copy` becomes the text
  `{{ b }}`. Chained references and dependency ordering are not evaluated.
- To retain a literal template, use Jinja escaping, for example
  `"{% raw %}{{ label }}{% endraw %}"`. Do not render the returned tree again.
- YAML aliases retain shared and recursive container references. The graph is
  copied, not flattened.
- Traversed mappings become plain dictionaries, including nested `AttributeDict`,
  `OrderedDict` and custom mappings supplied to embedded configuration. Lists are
  traversed; tuples and other container types remain unchanged and their contents
  are not rendered. Consumers that require those types should prepare their own
  supported configuration tree before loading.
- The placeholder diagnostic reports the supplied value without rendering again.
  Direct users of that diagnostic should resolve their configuration first.
- Configuration files should remain trusted inputs: sandboxing blocks Python
  internals but does not enforce execution time or memory limits.
- The separate `assetutilities.common.ymlInput` module, the UTF-8 reader and
  library-data readers retain their parsing-only behavior. The rendering loaders
  are in `assetutilities.common.yml_utilities`. The engine's `config_flag=False`
  path with an in-memory mapping explicitly bypasses configuration processing;
  call `resolve_placeholders` first if that path needs substitution.
- Other template runtime errors, such as division by zero, propagate to the
  caller; the literal fallback does not cover every exception.

## Sources and checks

- [YAML 1.2.2 specification (2021), section 3.2.2.2, Anchors and Aliases](https://yaml.org/spec/1.2.2/#3222-anchors-and-aliases),
  and [section 7.1, Alias Nodes](https://yaml.org/spec/1.2.2/#71-alias-nodes).
- [Jinja 3.1 template documentation, Variables](https://jinja.palletsprojects.com/en/stable/templates/#variables)
  and [Escaping](https://jinja.palletsprojects.com/en/stable/templates/#escaping).
- [Jinja 3.1 API documentation](https://jinja.palletsprojects.com/en/stable/api/),
  `StrictUndefined` and `keep_trailing_newline`;
  [sandbox documentation](https://jinja.palletsprojects.com/en/stable/sandbox/).

`tests/unit/test_yaml_config_variables.py` checks this example, final merge
precedence, single-pass escaping, scalar types, newlines, sandbox behavior and
recursive aliases. The existing variable-helper and safe-loading tests cover
native single variables, blocks, and rejection of Python object YAML tags.
Both original issue examples are loaded through the shared loader; the second
example quotes its placeholder so it is valid YAML.

Existing consumers of the shared loaders receive the rendering default when
upgrading. Reviewing their literal-template inputs or opting out is separate
adoption work; this change does not rewrite consumer configurations.
