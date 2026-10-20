# Process readiness assessment

The process register makes declared role coverage, procedures, handoffs and
measurement criteria reviewable for the sales, process and productivity areas
named in issue #37. It evaluates supplied records and identifies missing inputs.
It does not establish organizational scalability or authenticate evidence.

## Revision history

| Revision | Date | What changed and why |
|---|---|---|
| A | 2026-10-20 | Added a role-based register, explicit evidence checks and a worked example so process gaps can be reviewed without publishing personnel details. |

## Scope and sources

Issue #37 supplies the three area names but no deliverables, numerical limits,
linked issues, equations or acceptance criteria. The existing repository plan
recommends handling business decisions privately. This utility provides a generic
record and assessment contract; it does not implement sales strategy, choose
staffing levels or assign individuals.

This document defines the software contract, including the distinct backup-role
rule. Those checks are not attributed to an external management standard.
No engineering equation, productivity coefficient or recommended business target
is embedded. All metric targets and their source references are required inputs
for evaluation. Procedure, observation and policy references are declarations:
the utility does not open them, verify their contents, check their age or decide
whether a policy is appropriate.

## Run the assessment

From a checkout with the package installed:

```sh
python -m assetutilities.devtools.process_readiness examples/devtools/process-readiness.json
```

Without an installation, set `PYTHONPATH=src` before that command. The module
uses only the Python standard library. It reads the input and writes JSON to
standard output; it does not edit input files or create reports on disk.

The Python API is:

```python
from pathlib import Path
from assetutilities.devtools.process_readiness import assess, load_register

report = assess(load_register(Path("examples/devtools/process-readiness.json")))
```

Exit codes are part of this contract: `0` for `PASS`, `1` for an assessment
containing `FAIL` or `NOT_EVALUATED`, and `2` for unreadable or invalid input.
Malformed input produces no JSON report. Input errors omit file paths and input
values from diagnostics.

## Input contract

The root object requires `roles` and a nonempty `processes` array. Unknown fields
are rejected at every object level to expose spelling mistakes. JSON duplicate
keys, non-finite numbers, boolean measurements and numeric strings are rejected.
Identifiers and supplied references must be nonempty text. Omit optional text,
values and criteria or use `null` when evidence is unknown. For metrics, omit
the field or supply an empty array. Blank strings are malformed input.

| Field | Contract |
|---|---|
| `roles` | Unique role labels. May be empty when assignments are unknown. |
| `processes[].id` | Unique process identifier within the register. |
| `processes[].area` | `sales`, `process` or `productivity`, following issue #37. |
| `accountable_role` | Optional role registered in `roles`. |
| `backup_role` | Optional registered role distinct from the accountable role. |
| `procedure_ref` | Optional reference to the procedure for this process. |
| `handoff_ref` | Optional reference to evidence defining or recording the handoff. |
| `metrics` | Optional array of measurements; use an empty array when unknown. |
| `metrics[].id` | Unique metric identifier within this process. |
| `metrics[].unit` | Required unit applying to both the observed value and target. |
| `metrics[].value` | Optional finite number; zero and signed values are allowed. |
| `metrics[].evidence_ref` | Optional observation reference, including its applicable period. |
| `metrics[].criterion` | Optional object requiring `operator` and finite `target`. |
| `criterion.operator` | `at_most` or `at_least`; equality passes. |
| `criterion.source_ref` | Optional criterion document, revision and section reference. Evaluation requires it. |

An unknown assigned role is invalid input, rather than evidence of coverage.
Separate role labels do not establish that separate individuals are available.
Choose metrics with consistent definitions and comparable observation periods.
Units are declared, not converted or checked for physical equivalence.
Supply an already calculated measurement if a domain calculation is needed.

## Method and interpretation

Each process receives checks for accountability, backup, procedure, handoff and
each declared metric. Without metrics it receives a `measurement` finding.
An omitted area receives an `area_coverage` finding, so omitting an area cannot
produce an overall pass.

| Check | PASS | FAIL | NOT_EVALUATED |
|---|---|---|---|
| Accountability | Registered role declared | Invalid assignments reject input | Role absent |
| Backup | Distinct registered role declared | Same role declared twice | Either role absent |
| Procedure or handoff | Reference declared | No content judgment is made | Reference absent |
| Metric | Supplied inequality holds | Supplied inequality does not hold | Value, evidence, criterion or source absent |
| Area coverage | Covered by process checks | No content judgment is made | Area has no process |

For measurement criteria the operations are direct comparisons:
`value <= target` for `at_most`, and `value >= target` for `at_least`.
Their source is the caller's `criterion.source_ref`; there are no default limits,
normalization factors, weighted scores or productivity projections.

`FAIL` takes precedence over `NOT_EVALUATED`, then `PASS`. The summary counts
findings, not people or performance scores. Every non-pass finding includes a
concrete next action. Reports preserve input order and include supplied metric
values, units and references. Assessment does not modify the input.

A `PASS` means the declared fields and comparisons meet this software contract.
It does not certify evidence quality, personnel capacity, financial performance,
compliance, improved productivity or readiness for organizational growth.

## Worked example: synthetic policy A (2026)

The input is [process-readiness.json](../../../examples/devtools/process-readiness.json).
All records, observations and policy references are synthetic, supplied solely
to demonstrate the contract. They are not measurements from previous work.

The synthetic **Elapsed effort** policy explicitly chooses a maximum of
**8 hours per accepted item**. The synthetic **Review output** policy explicitly
chooses a minimum of **2 accepted items per review**. These illustrative targets
are defined here, not taken from a publication or recommended for operational use.

The hand calculations and expected answers are:

| Process | Supplied observation | Supplied target and method | Answer |
|---|---|---|---|
| Request intake | 6 hours per accepted item | At most 8: `6 <= 8` | PASS |
| Procedure review | 3 accepted items per review | At least 2: `3 >= 2` | PASS |
| Improvement review | 8 hours per accepted item | At most 8: `8 <= 8` | PASS |

All processes also declare distinct registered accountable and backup roles,
procedure references and handoff references. By enumeration, each process has
five passing checks: accountability, backup, procedure, handoff and its metric.
Three processes therefore give **15 PASS, 0 FAIL, 0 NOT_EVALUATED** and overall
`PASS`.

Change the intake observation to **9**: `9 <= 8` is false, so its metric and the
overall assessment become `FAIL`. Remove its criterion source instead: the metric
and overall assessment become `NOT_EVALUATED`. These expectations are written
independently in `tests/modules/devtools/test_process_readiness.py`.

## Later work

The maintainers must define actual sales procedures, role assignments,
observations and acceptance policies before applying the tool operationally.
Evidence authentication, calendar capacity, forecasting, integrations and
business-specific calculations are outside this contract. Keep sensitive
registers and their output in an appropriate private destination; this example
contains only role labels and synthetic data.
