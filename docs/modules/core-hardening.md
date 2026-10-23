# Workflow core

The engine selects explicit handlers, loads configuration without Python object
construction, resolves optional mapping placeholders, and sends native and
standard-library log messages through one output pipeline. These changes address
the dispatch, YAML and logging parts of #120.

## Revision history

| Revision | Date | Change and reason |
|---|---|---|
| Initial | 2026-10-20 | Document explicit dispatch, YAML boundaries and one logging pipeline so consumers can reproduce the supported behavior. |
| 1 | 2026-10-22 | Correct compatibility claims and describe migration steps for logging, YAML placeholders and engine imports. |

## Handler registry

`assetutilities.engine_registry.registry.names()` lists implemented handlers.
The config's `basename` (or `meta.basename`) selects a registered name. Both
`yaml_utilities` and `yml_utilities` select the YAML handler. Optional workflow
dependencies are imported only when that handler runs, and each class-based
handler gets a fresh instance.

Trusted Python callers can register a callable without editing the engine:

```python
from assetutilities.engine_registry import registry

def summarize(cfg):
    cfg["summary"] = "complete"
    return cfg

registry.register("summarize", summarize, aliases=("summary",))
```

A handler accepts a configuration mapping and returns either a mutable mapping
or `None` after changing it in place. Duplicate names and invalid return types
raise exceptions. Config files cannot supply import paths or executable code.
The PDF reader's return value is stored under `result`, as before.

The unimplemented `gitpython`, `csv_utilities` and `text_analytics` names are
excluded from the registry. Calling them still raises `NotImplementedError`
with a specific diagnostic. Unknown names raise `ValueError` before the engine
creates output folders. Existing runnable workflow rows remain unchanged.

The module-level `de` and `fm` instances and several incidental workflow-class
re-exports have been removed from `assetutilities.engine`. Downstream callers
must import classes from their implementation modules and construct their own
instances. For example, import `DataExploration` from
`assetutilities.modules.data_exploration.data_exploration` and `FileManagement`
from `assetutilities.common.file_management`. The public `engine` entry point
remains available.

## YAML contract

Configuration loaders use PyYAML's safe constructors. `yml_read_stream` validates
the whole stream before merging mappings in document order: later scalar/list
values replace earlier values, nested mappings merge, and empty documents are
ignored. A malformed document or nonstandard tag raises an exception; a valid
prefix cannot be returned as a successful partial configuration.

The reusable ruamel split module validates standard YAML tags with `safe_load`
before round-trip loading to preserve comments and quotes. Split keys must be
filename components; spaces, Unicode and integer keys are supported. Keys
containing either path separator or `..` raise `ValueError`. Keys producing
the same filename are rejected before any split file is written. Output paths use
forward slashes, and output text uses UTF-8 with LF line endings and no BOM.
Custom tags need a separately
designed and tested constructor policy; they are not accepted by this surface.

Native anchors and aliases work during parsing. Quoted placeholders can be
enabled for engine payloads with:

```yaml
yaml_options:
  resolve_placeholders: true
name: example
label: "prefix_{{ name }}"
```

The resulting label is `prefix_example`. Direct loader callers can use
`WorkingWithYAML().ymlInput(path, placeholders=True)` after update-file merging.
The default leaves placeholders unchanged.

Resolution makes one pass against the original mapping and substitutes scalar
values by dotted key lookup. Undefined references stay literal. Mapping keys
such as `items` work; Python attributes, calls, expressions and template control
blocks are not evaluated. This narrows the previous general Jinja rendering
helper to the documented placeholder syntax: filters and non-scalar
substitutions also remain literal. Migrate templates that need those features
by computing their values before passing the mapping to the engine. Missing
or null `yaml_options` leaves placeholder resolution disabled. Chained placeholders
are not expanded recursively. Cyclic aliases raise an exception during resolution.

Engine payload resolution occurs after configuration preparation and before
dispatch. Basename selection, output paths and file-management preparation
therefore require literal values. YAML plotting retains its source key chains,
so extraction can be repeated without rewriting the input configuration.

## Worked example: inputs, method and answer

Run from the repository root:

```bash
uv run python -m assetutilities examples/workflows/core_hardening/input.yml
```

The example supplies synthetic `x` values `[0, 1, 2]` and `y` values `[0, 1, 4]`
in `series.yml`. The independent arithmetic is `0*0=0`, `1*1=1`, `2*2=4`.
These are assigned demonstration data, with no empirical coefficient or
engineering acceptance limit. The method safely reads `series.x` and `series.y`,
copies the arrays into the existing XY plotting template, and replaces the
quoted title placeholder with `Synthetic square series`.

The answer is a plot through `(0, 0)`, `(1, 1)` and `(2, 4)` in
`results/Plot/input.png`, a resolved `results/input.yml`, and a human-readable
`logs/input.log`. The tests copy inputs to temporary directories and independently
assert the literal coordinates, resolved title, saved plot and completion log.
`root_folder` redirects data and output roots together; place relative data
files under that root when using the override.

## Logging

Both `set_logging(cfg)` and `setup_logging(cfg)` configure the same pipeline.
Legacy standard-library records flow into loguru; no reverse propagation sink
is installed. Each emission appears once per destination. The run-log path and
overwrite behavior are retained. The following compatibility changes require
migration:

- `set_logging` now writes human-readable text instead of loguru JSON records.
  Consumers that parsed JSON must accept the text format or configure a separate
  caller-managed loguru sink with `serialize=True` after setup.
- `setup_logging` no longer forwards native loguru records to named stdlib
  handlers. Capture native records with a loguru sink; handlers such as pytest's
  `caplog` no longer receive them automatically. Stdlib-originated records still
  flow into loguru. Installing bridges in both directions can create a loop.
- Both entry points now require stdlib-recognized levels, such as `DEBUG`,
  `INFO`, `WARNING`, `ERROR` and `CRITICAL`. Configurations using loguru-only
  `TRACE` or `SUCCESS` must select a stdlib level instead.

`Analysis.log_to_file: false` creates no log directory. Reconfiguration closes
the previous run's sinks. Exception-local variable inspection is disabled;
applications must still avoid putting confidential data in log messages.

See [the logging guide](../logging_loguru_migration.md) for integration details.

## Sources and remaining work

- [PyYAML documentation, safe constructors](https://pyyaml.org/wiki/PyYAMLDocumentation#loading-yaml), accessed 2026-10-20: standard-tag loading and stream parsing.
- [YAML 1.2.2, 2021, section 3.2.2.2](https://yaml.org/spec/1.2.2/#3222-anchors-and-aliases): native anchor and alias semantics.
- [Loguru migration guide](https://loguru.readthedocs.io/en/stable/resources/migration.html), accessed 2026-10-20: standard logging integration and disabling exception-local diagnostics.
- Existing dispatch targets and compatibility tests supply the software behavior
  baseline. No standards-derived numerical constants are introduced.

Standalone implementations and runnable examples for the excluded legacy names,
PDF extraction improvements, self-contained HTML plotting reports and broad
clean-code work remain separate child-issue work. This change does not claim
that every child of #120 is complete. Existing database and CLI security tests
are rerun to check that the earlier remediation remains intact.
