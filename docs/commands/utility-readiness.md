# Utility readiness checklist

The readiness tool records explicit onboarding observations for issue #42 and
reports the next exercise for each incomplete item. Command discovery is an
optional, separate observation. The assessment neither installs software nor
executes applications, changes repositories or contacts external services.

## Revision history

| Revision | Date | Change and reason |
|---|---|---|
| Initial | 2026-10-20 | Add evidence assessment, discovery and a worked example so missing setup evidence remains visible. |

## Scope and sources

The checklist is derived from issue #42 and its existing repository plan. It
covers repository and contribution access, Git and the daily workflow, CAD and
editor tools, Blender access, audio and meetings, and Python environment and
practice tasks. The daily workflow is tracked separately in issue #19; environment
management is discussed in issue #32. This tool does not implement their broader
automation requirements.

The original issue's completed boxes are historical observations. They are not
imported as evidence about the environment being assessed. The earlier issue plan
recommends administrative closure; this implementation provides a reusable
assessment without changing that plan or closing the issue.

- Python Software Foundation, *Python 3.14 Library Reference* (accessed 2026-10-20),
  [`shutil.which`](https://docs.python.org/3.14/library/shutil.html#shutil.which):
  executable discovery uses `PATH` and Windows `PATHEXT`.
- Blender Foundation, *System Requirements for Blender* (accessed 2026-10-20),
  [requirements](https://www.blender.org/download/requirements/): compatibility
  depends on the operating system, graphics support and Blender version.

No numerical engineering equations, coefficients, hardware limits or readiness
percentages are used. Version-specific compatibility must be checked against the
applicable vendor documentation and recorded as input; no minimum is inferred.

## Inputs and method

Generate an evidence template in a private working folder:

```bash
python -m assetutilities.devtools.readiness --template > readiness-private.json
```

Each key accepts an observation with `ready` equal to `true`, `false` or `null`.
An evaluated observation requires a nonblank `basis`, such as a reference to a
dated functional exercise retained privately. Missing keys are unknown. Unknown
keys, duplicate JSON keys, invalid types and missing evidence bases are errors.

```json
{
  "git": {
    "ready": true,
    "basis": "A local practice commit succeeded."
  }
}
```

| Input observation | Check result | Meaning |
|---|---|---|
| `true` with a basis | `READY` | The operator attests that the exercise succeeded. |
| `false` with a basis | `ACTION_REQUIRED` | The operator records a failed or incomplete exercise. |
| `null` or omitted | `NOT_EVALUATED` | Evidence has not established the result. |

Overall readiness is the conjunction of all checklist requirements: any failed
check gives `ACTION_REQUIRED`; otherwise any unknown gives `NOT_EVALUATED`;
otherwise the result is `READY`. These rules are application definitions, tested
against explicit Boolean truth tables rather than values from the implementation.

```bash
python -m assetutilities.devtools.readiness --input readiness-private.json
python -m assetutilities.devtools.readiness --input readiness-private.json --discover
python -m assetutilities.devtools.readiness --input readiness-private.json --require-ready
```

The default command exits successfully when a valid report is produced, including
an incomplete assessment. `--require-ready` instead returns a nonzero status for
an incomplete assessment. Invalid input uses the argument parser's error status.
`--template` cannot be combined with discovery or a readiness gate.

Discovery adds a `commands_on_path` object containing Boolean observations only.
It looks for common command aliases for Git, Python, conda, FreeCAD, Blender,
VS Code and Notepad++. It does not execute them. An absent alias does not prove
that an application is uninstalled: GUI installations and shell functions may
not appear on `PATH`. Presence does not establish a version, working environment,
licence, hardware compatibility or access rights. Discovery never changes an
assessment status. AutoCAD is assessed manually and is never probed.

## Worked example: inputs, method and answer

The synthetic input is [readiness.json](../../examples/devtools/readiness.json):
Git has a successful practice observation; the daily workflow has not been
rehearsed; Blender access is unknown; all other observations are omitted.

```bash
python -m assetutilities.devtools.readiness --input examples/devtools/readiness.json
```

By the truth table, Git is `READY`, the daily workflow is `ACTION_REQUIRED`, and
Blender access and every omitted item are `NOT_EVALUATED`. The failed daily
workflow determines the overall answer: `ACTION_REQUIRED`. The next step is to
agree and rehearse the daily Git workflow described in issue #19, then supply
the remaining evidence. The example test asserts these results independently.

## Functional exercises and known limits

- Confirm authorized repository clone and contribution access without publishing
  repository locations or credentials in a readiness record.
- Install and exercise the required applications through approved procedures.
  Record licence readiness manually where applicable.
- For Blender, demonstrate either a compatible local installation or authorized
  remote access with a sample task. No remote connection is attempted by the tool.
- Test earphones and microphone in a call, join a meeting, and demonstrate
  independent scheduling. The original issue requests four independently
  scheduled meetings; that historical target is not imposed as a new numeric rule.
- Activate the intended Python environment, complete a neutral exercise, and
  obtain the next task from the maintainer. No task is invented by this tool.

The report omits evidence bases and installation paths; retain the source JSON
privately for traceability and re-assess when the environment or requirements
change. No evidence freshness is inferred. The operator remains responsible for
the truth and applicability of observations. A `READY` report attests only to
the supplied exercises; it does not certify software, hardware or permissions.

Later work consists of the actual installations, access arrangements, functional
exercises and daily-workflow automation. Those actions are outside this package's
read-only assessment and cannot be established from command presence alone.
