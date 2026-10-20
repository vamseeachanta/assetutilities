# Hardware consolidation readiness

Assess the hardware checklist in issue #36 from supplied functional observations
and explicit capacity, display, networking and KVM targets. The result identifies
failed tests and missing evidence. It does not configure devices or establish
that physical setup is complete.

## Revision history

| Revision | Date | Change and reason |
|---|---|---|
| Initial | 2026-10-20 | Add evidence assessment and a worked example so incomplete setup remains visible. |

## Scope and basis

The [existing issue plan](../plans/2026-05-05-issue-36-consolidate-hardware.md)
routes physical installation and access administration to operations. This
utility supplies a reusable assessment of the same checklist, with no system
commands, device probes, network connections or configuration writes.

The implementation covers three slices:

1. Validate observations and targets; distinguish passing, failing and
   unevaluated checklist areas.
2. Evaluate graphics, local audio, SMB storage, displays, graphical remote
   access, meeting audio, wired networking and KVM operation.
3. Provide a JSON command, a Python API and the synthetic worked example below.

Acceptance targets are supplied by the caller. There are no vendor ratings,
engineering coefficients, unit conversions or default numerical acceptance
limits. Counts, elapsed seconds and byte capacities are nonnegative integers
by definition; minimum targets must be positive. An outage allowance may be zero.
Boolean observations accept only JSON `true` or `false`; a number is not a
substitute for a functional test result. Missing fields are unknown, and `null`
is invalid. Unknown fields are rejected so a spelling error cannot hide evidence.

The command's JSON handling follows the [Python 3.11 JSON documentation](https://docs.python.org/3.11/library/json.html),
sections “Standard Compliance and Interoperability”, “Infinite and NaN Number
Values” and “Repeated Names Within an Object”. Duplicate names and non-finite
numbers are rejected rather than accepting the decoder's permissive defaults.

## Input contract

The root object has optional `requirements` and `observations` objects. Omitted
areas and fields remain unevaluated. All accepted fields appear in this table;
requirements exist only for areas with numerical comparisons.

| Area | Fields inside `observations.<area>` | Fields inside `requirements.<area>` |
|---|---|---|
| `graphics` | `functional`: successful graphics workload | none |
| `audio` | `playback`: successful local playback | none |
| `shared_storage` | `capacity_bytes`: usable capacity of the shared filesystem; `smb_access`: intended access tested from an authorized client | `minimum_capacity_bytes` |
| `displays` | `simultaneous_count`: displays functioning at the same time | `minimum_count` |
| `remote_access` | `login`: authorized remote login succeeds; `graphical_session`: intended graphical application session succeeds | none |
| `meeting_audio` | `capture`, `playback`: microphone and output work in the intended meeting application | none |
| `wired_network` | `link`: wired connection works; `observation_seconds`: monitored duration; `outages`: outages in that duration | `minimum_observation_seconds`, `maximum_outages` |
| `kvm` | `switched_computers`: computers successfully switched; `keyboard`, `mouse`, `video`: each works across every counted computer | `minimum_computers` |

Use observations from the same setup and test period. A device being installed
or enumerated is insufficient evidence of successful operation. Remote access
requires an actual graphical-session test; an available display server alone
does not demonstrate an application connection. Meeting audio assesses the
intended application regardless of the sound interface used. Test intended SMB
operations with the intended permissions; a listed share alone does not prove
access. Retain private test records separately; this input accepts no identity,
address, credential, location or free-text fields.

## Method and results

Each true functional observation passes its criterion; false fails it. Capacities,
display counts and switched-computer counts pass when the observation is at least
the supplied minimum. Network outages pass when the observed count is at most
the supplied allowance. A shorter monitoring period than the supplied minimum
is insufficient evidence. These comparisons are the input contract, not limits
derived from a hardware standard.

A checklist area is `FAIL` if any evaluated criterion fails. Otherwise it is
`NOT_EVALUATED` if a field is missing or the monitoring period is too short;
otherwise it is `PASS`. The overall status uses the same precedence across all
areas. Exceeding the outage allowance already establishes failure even if the
monitoring period is short; a short period without a failed criterion cannot
establish a pass.

The output contains `status` and an ordered `checks` list. Each check contains
its `id`, `status`, and lists of field names under `failed`, `missing` and
`insufficient`. Both the observation and its target are listed when both are
absent. A failed criterion and missing evidence can coexist. Input values and
file locations are not included in the report or input-error diagnostics.

## Command and Python API

From a source checkout, with Python available:

```bash
PYTHONPATH=src python -m assetutilities.cli.hardware_readiness examples/hardware_readiness/observations.json
```

The same module works from an installed package. The input is read without
modification, and the report is written only to standard output. Exit codes are
part of this command's protocol: `0` for `PASS`, `1` for `FAIL`, and `2` for
`NOT_EVALUATED` or invalid input. Invalid input emits a diagnostic on standard
error and no JSON report.

```python
import json
from pathlib import Path

from assetutilities.cli.hardware_readiness import assess_readiness

document = json.loads(
    Path("examples/hardware_readiness/observations.json").read_text(encoding="utf-8")
)
report = assess_readiness(document)
assert report["status"] == "FAIL"
```

The API does not mutate its input. It raises `TypeError` for incorrect types and
`ValueError` for invalid values or unknown fields. An empty object is valid and
leaves every area `NOT_EVALUATED`.

## Worked example: inputs, method and answer

All numbers in [the example](../../examples/hardware_readiness/observations.json)
are synthetic inputs for demonstrating comparisons, not hardware specifications
or recommended acceptance limits. The deliberately small byte counts avoid
suggesting a real storage requirement. The independent hand calculation below
is also the test oracle in `tests/unit/test_hardware_readiness.py`.

| Area | Inputs and hand calculation | Answer |
|---|---|---|
| Graphics | Functional observation is true | `PASS` |
| Audio | Playback is true | `PASS` |
| Shared storage | 1200 bytes is at least the supplied 1000 bytes; SMB access is true | `PASS` |
| Displays | 2 simultaneously working displays meets the supplied count of 2 | `PASS` |
| Remote access | Login is true; graphical-session evidence is absent | `NOT_EVALUATED` |
| Meeting audio | Capture and playback are true | `PASS` |
| Wired network | Link is true; 3600 seconds meets the supplied 3600 seconds; 2 outages exceeds the supplied allowance of 1 | `FAIL` |
| KVM | 3 switched computers meets the supplied count of 3; keyboard, mouse and video are true | `PASS` |

Answer: six areas pass, one fails and one is unevaluated. The overall result is
`FAIL`, and the command exits with code `1`. The next steps are to investigate
the observed outages, repeat monitoring for the selected observation period,
and record a graphical remote-session test. A readiness pass will require all
criteria to pass with complete evidence.

## Known limits and later work

Physical installation, SMB permissions, access administration, display cabling,
audio selection and network repair remain operational tasks. No such task is
marked complete by this utility. Actual hardware has not been tested here.
There is no automatic collection, evidence authentication, freshness check,
performance qualification or guarantee that a supplied observation is truthful.
In particular, a graphics functional check does not establish workload-specific
performance, and a wired link alone does not establish network reliability.
Protocol-specific remote setup and USB interface selection remain outside the
assessment. Automated collection can be considered separately once its access
scope and private-data handling are established.
