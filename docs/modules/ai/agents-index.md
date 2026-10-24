# Offline agent configuration workflow

This workflow addresses the reusable configuration and prompt portions of
[issue 30](https://github.com/vamseeachanta/assetutilities/issues/30).
It validates existing definitions, renders prompts and emits portable bundles.
It does not invoke an assistant, execute agent tasks, retrieve references or
install configuration in another repository. A rendered prompt is text for
review, not evidence that the described task has been performed.

## Existing assets and coverage

| Source relative to this directory | Purpose and current use |
|---|---|
| `_agents/multi_agent.yaml` | Preliminary decision, programming, DevOps, physics, finance and retrieval roles; consumed by the example below |
| `_agents/agent_python_programmer.yaml` | Detailed programming role and principles; accepted by the loader |
| `_agents/agent_devops_engineer.yaml` | Detailed CI/CD role; accepted as data, with task metadata preserved |
| `_agents/agent_decision_making.yaml` | Decision role; accepted by the loader |
| `_agents/prompt_templates.yaml` | Existing empty placeholder; use `examples/agent_prompt.yaml` for the executable example |
| `_agents/prompts.md`, `_agents/rules.md`, `_agents/alt-rules.md`, `_agents/requirements.md` | Historical prose references; not loaded as runtime instructions |

Table: Historical definitions and their offline consumers.

The source implementation is `src/assetutilities/agent_os/agent_config.py`.
Existing `src/assetutilities/agent_os/commands/`, `integration/`, `cli/` and
`cross_repo/` provide separate Agent OS facilities. The portable workflow does
not call their installers or fixed-repository distribution code. This inventory
describes this checkout only; downstream adoption is not established.

## Data contract

A catalog is either a nonempty YAML list of agent mappings or a mapping with
only the `agents` key containing that list. Each agent has a unique `name`
matching `[a-z][a-z0-9_]*` and a non-blank `role` string or nonempty list of
non-blank strings. Optional `principles` is a nonempty list of non-blank strings.
Other fields are preserved as opaque JSON-compatible metadata. This is not full
validation of legacy tasks: for example, null task parameters in the DevOps
definition are not executable specifications.

Duplicate mapping keys, duplicate agent names, unsafe YAML tags, recursive
structures, non-string mapping keys, timestamps and non-finite numbers are
rejected. Dates intended as metadata must be quoted strings. YAML merge keys
are unsupported. Strings and mapping keys must be encodable as UTF-8;
unpaired surrogates are rejected in catalogs and prompt requests, including
direct Python API arguments. Use reviewed local configuration; the parser is not a
resource-isolation boundary for arbitrary large or adversarial documents.

A prompt request has exactly `agent`, `template` and `inputs`. Templates use
`$name` or `${name}` placeholders and `$$` for a literal dollar. Templates must
be non-blank. Inputs must provide exactly the placeholders present, with
non-blank string values. Missing and unused inputs are errors. Substitution is
literal and occurs once; values are not evaluated as expressions, paths, shell
commands or nested templates.

`validate`, `render` and `bundle` write UTF-8 results with LF line endings to
stdout, including when redirected. Invalid configuration produces a diagnostic
on stderr and a nonzero exit status. No output files are created by the module.
Bundles preserve agent ordering and metadata, sort
mapping keys, and use JSON so other libraries can consume them without a
provider-specific dependency. Review bundle contents before transferring them.

## Worked example: regression prompt

Use an environment with this package and its declared PyYAML dependency
installed. From a source checkout, expose `src` through `PYTHONPATH` in the
current shell. The following commands then run without network access:

```console
python -m assetutilities.agent_os.agent_config validate docs/modules/ai/_agents/multi_agent.yaml
python -m assetutilities.agent_os.agent_config render docs/modules/ai/_agents/multi_agent.yaml examples/agent_prompt.yaml
python -m assetutilities.agent_os.agent_config bundle docs/modules/ai/_agents/multi_agent.yaml
```

Input: `examples/agent_prompt.yaml` selects `python_programmer`, supplies a task
and its failure evidence, and requests a regression test before a fix.

Method: the selected role and principles are read from the catalog; the two
placeholders are replaced by the supplied literal strings. No numerical
equations, engineering coefficients or acceptance limits are involved.

Expected answer from `render`:

```text
# python_programmer

Role: Writes code in Python

Principles:
- clean code
- DRY
- keep it simple stupid
- etc.

Task: Reject an empty configuration.
Evidence: An empty mapping currently reaches the parser.
First write a failing regression test, then propose the smallest fix.
```

The legacy principles are deliberately retained verbatim, including `etc.`;
the renderer does not silently improve or reinterpret source instructions.
`tests/agent_os/test_agent_config.py` independently spells out this answer
and the substitution method instead of computing its oracle with the renderer.

Python callers can use `load_agents(path)`, `parse_agents(text)`,
`render_prompt(agents, agent_name, template, inputs)` and `bundle_agents(agents)`.
The invariant `parse_agents(bundle_agents(agents)) == agents` is tested.
No assistant credentials or installed editor extension are required.

## Remaining issue scope

- Existing role definitions now have a tested offline consumer. Physics and
  finance definitions remain preliminary; domain capability is not established.
- Parameterized regression prompts and portable bundle production are provided.
  Continual improvement still requires reviewed failure evidence and tests.
- Live Copilot integration, automatic repository installation and verified use
  in other libraries remain follow-up work. Manual transfer of reviewed output
  does not establish those capabilities.
- The earlier `docs/plans/2026-05-05-issue-30-ai-agents-config.md` proposed a
  supersession decision. This implementation does not close or retitle the issue
  or assert that the broader ecosystem has been verified.

Sources: the issue requirements, the existing `_agents/*.yaml` definitions,
and the explicit contract and hand-substituted example above. Historical
reference strings in the agent files are metadata, not verified engineering
citations. No source-derived numerical values are introduced.
