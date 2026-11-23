# Tech-Debt / Clean-Code Consistency Audit

> Advisory audit for issue [#41](https://github.com/vamseeachanta/assetutilities/issues/41).
> Audits `src/assetutilities/` against the repo's own standard in
> [`docs/clean_code.md`](./clean_code.md). **This is an advisory document only — it
> contains no code changes.** Every `file:line` below was grep/`sed`-confirmed against
> the working tree at audit time (branch `feat/autorun-2026-06-19`). Line numbers drift
> as the code evolves; re-grep before acting.

## How this maps to `docs/clean_code.md`

The repo standard is short and intent-led. The clauses this audit leans on:

- **"Consistent frequently used words for messages and logging"** — Tests `PASS`/`FAIL`,
  Process `START`/`STOP` (clean_code.md lines 29–31).
- **"Lint … Utilize AI to fix it for new code; for legacy code ensure tests exist first"**
  (lines 37–39) — bare `except:`, dead code, unused branches are classic lint findings.
- **"All Function … lines 10-20 lines (black?)"** (lines 40–44) — function-length budget.
- **"Code should be commented such that documentation is left to AI"** (lines 20–25) —
  consistency that lets AI extend the code "faster, seamless" (the stated Objective, line 1).

Beyond the literal text, the Objective ("consistent code will help AI add new code…faster")
is the lens: the findings below are the inconsistencies that most slow safe AI-assisted edits.

## Prioritized findings

Severity key: **High** = correctness/safety hazard or actively misleading; **Med** =
maintainability/consistency drag; **Low** = cosmetic / localized.

### Theme A — Error handling: bare `except:` (silent swallowing)

The single largest consistency issue. **32 bare `except:` clauses in non-test library code**
(`grep -rn "except:" --include="*.py" | grep -v tests/ | wc -l` → 32). Bare except catches
`SystemExit`/`KeyboardInterrupt`, hides the real error, and defeats lint — directly contrary
to the "Lint … fix it" clause and to AI-extensibility (the next editor cannot see what failed).

| Sev | Rule (clean_code.md) | file:line | Issue | Suggested fix |
|-----|----------------------|-----------|-------|----------------|
| High | Lint / error clarity (37–39) | `common/database.py:165,195,434,461,1074` | 5 bare `except:` in the DB layer; failures are swallowed or paired with `sys.exit()` | Catch specific exceptions; log with context; re-raise or return error dict |
| High | Lint / error clarity (37–39) | `modules/excel_utilities/excel_utilities.py:245,514,546,586,607,673,682` | 7 bare `except:` in formula/range evaluation; wrong results pass silently | Narrow to `except (KeyError, ValueError, openpyxl…)`; log the cell/formula |
| Med | Lint / error clarity (37–39) | `common/visualizations.py:340,413,419,694` ; `common/writers.py:73,94,99` ; `common/transform.py:33,244` ; `common/visualization.py:170,189` ; `common/yml_utilities.py:202` ; `common/ymlInput.py:18` ; `common/ApplicationManager.py:153` ; `common/readers/data_reader.py:250` ; `devtools/organize_structure.py:133,140,272` ; `devtools/propagate_commands.py:261` ; `modules/data_exploration/data_exploration.py:196` | Remaining 20 bare `except:` across the library | Same: narrow + log; several are `except: pass` (full silent swallow) |

### Theme B — `sys.exit()` inside library code

Library/router code calls `sys.exit()`, which kills the host process of any caller (a notebook,
a test, another tool). Library code should raise, not exit. This also breaks the standard's
desire for predictable, AI-composable functions.

| Sev | Rule | file:line | Issue | Suggested fix |
|-----|------|-----------|-------|----------------|
| High | Function returns / composability (40–42) | `common/database.py:295,1100` | `sys.exit()` on a failed Access connection / undefined data | Raise an exception or return a `{"status": "FAIL", …}` dict |
| High | Function returns / composability (40–42) | `common/ApplicationManager.py:188` | `sys.exit()` inside config setup | Raise `ValueError`/custom exception |
| High | Function returns / composability (40–42) | `common/visualizations.py:176` | `sys.exit()` mid-plot on a datetime-axis warning | Raise or return; do not exit |

### Theme C — Dead / unreachable code

| Sev | Rule | file:line | Issue | Suggested fix |
|-----|------|-----------|-------|----------------|
| Med | Lint / consistency (37–39) | `common/reportgen/doris_writers.py` (whole module) | Module is **never imported** anywhere; the `reportgen` basename routes to `reportgen.py` (`engine.py:126`), not `doris_writers`. File header is two `#todo` lines (`doris_writers.py:12-13`). Confirmed dead in #29/#91 work | Delete the module, or wire it in and add a test |
| Med | Unreachable code (37–39) | `common/database.py:296` ; `common/database.py:1099` ; `common/ApplicationManager.py:189` (region) ; `common/visualizations.py` (after :176) | `print(...)` placed **after** `sys.exit()` — unreachable. (e.g. `database.py:295` `sys.exit()` then `:296` `print("Access file connection failed")`) | Remove the dead print; move the message *before* the raise/exit |
| Low | Stub clarity (already handled by #91) | `engine.py:71-82` (`gitpython`), `engine.py:95-104` (`text_analytics`) | These are **not** dead imports — #91 replaced them with explicit `NotImplementedError`. No top-of-file `import git` / GitPython dependency exists (grep-confirmed clean). Listed here only to record that the previously-suspected "dead gitpython import" is already resolved | No action; keep as loud stubs |

### Theme D — Hardcoded absolute / user-specific paths

User-machine paths embedded as defaults make functions non-portable and unrunnable for anyone
else — the opposite of "consistent code [that helps] add new code seamlessly."

| Sev | Rule | file:line | Issue | Suggested fix |
|-----|------|-----------|-------|----------------|
| High | Consistency / portability (1, 32–35) | `common/file_ops.py:15,18,40,41` | Defaults `K:\0173 KM Extreme\…`, `C:\Users\kylem\Desktop\…` | Move to config/YAML; require caller to pass paths |
| High | Consistency / portability | `common/database.py:269,286` | DSN string hardcodes `C:\Users\achantv\…\2018_Atlas_Update.accdb` | Externalize to config |
| Med | Consistency / portability | `common/visualizations.py:898` | Hardcoded `C:\Users\achantv\…\TimeLine.csv` | Externalize |
| Med | Consistency / portability | `common/visualization/picture_manipulation.py:12,37-40,49` | Hardcoded `/Users/saiachanta/…` image paths | Parameterize; move demo to an example/test fixture |
| Low | Consistency / portability | `modules/pdf_utilities/pdf_comments.py:102` | Hardcoded `C:/Users/ss7a2365/Desktop/Comments.pdf` in `__main__` demo | Move to example or guard behind args |

### Theme E — Logging vs `print()` and message-word consistency

The standard explicitly asks for consistent message vocabulary (`PASS`/`FAIL`, `START`/`STOP`)
and "consistent … logging". The library mixes `print()` and `logging` and uses ad-hoc wording.

| Sev | Rule | file:line | Issue | Suggested fix |
|-----|------|-----------|-------|----------------|
| Med | Consistent logging (29–35) | `common/database.py` (45 `print(` vs 20 `logging.` calls) | Diagnostics split between `print` and `logging` in one module | Standardize on `logging`; remove `print` from library paths |
| Med | Consistent logging | `common/` (90 `print(` across the package incl. ApplicationManager, writers, transform, yml_utilities, visualizations, word_utilities, readers) | Library emits to stdout instead of a logger | Route through `logging` (config already exists in `common/set_logging.py`) |
| Low | Consistent message words (29–31) | repo-wide (only 6 `SUCCESS/FAILURE/Started/Stopped…` literals found) | Status words are inconsistent / mostly absent vs the prescribed `PASS`/`FAIL`, `START`/`STOP` | Adopt the 4-letter convention in status messages |
| Low | Logging best-practice | `common/`, `modules/` (29 `logging.<level>(f"…")` f-string calls) | Eager-formatted f-strings in logging calls | Prefer `logging.info("%s", val)` lazy formatting |

### Theme F — Function length ("10-20 lines")

The standard sets a 10–20 line budget per function ("black?"). Several functions are an order
of magnitude over and concentrate risk/complexity.

| Sev | Rule | file:line | Issue | Suggested fix |
|-----|------|-----------|-------|----------------|
| Med | Function length (40–44) | `modules/excel_utilities/excel_utilities.py:408` `_export_range_as_image_openpyxl` (~285 lines, 7 params) | Far over budget; also holds several bare excepts | Decompose; reduce parameter count via a config object |
| Med | Function length | `common/database.py:109` `enable_connection_and_cursor` (~189 lines) | Over budget; contains bare excepts + `sys.exit()` | Split connection / cursor / error handling |
| Low | Function length | `common/visualizations.py:93` `from_df_columns` (~125 lines); `common/visualizations.py:373` `add_title_and_axis_labels` (~97 lines); `modules/excel_utilities/excel_utilities.py:303` `_evaluate_simple_formula` (~105 lines); `common/database.py:585` `get_timeline_statistics` (~82 lines) | Over the 10–20 line guidance | Extract helpers |

## Quick wins (low risk, high consistency payoff)

1. **Delete `common/reportgen/doris_writers.py`** — confirmed unreachable (no importer); removes dead code outright. (Theme C)
2. **Remove the unreachable `print(...)` lines after `sys.exit()`** at `database.py:296`, `database.py:1099`, `ApplicationManager.py:189`, `visualizations.py` (post-:176). Pure cleanup, no behavior change. (Theme C)
3. **Replace the 4 `sys.exit()` calls in library code** (`database.py:295,1100`, `ApplicationManager.py:188`, `visualizations.py:176`) with `raise`. Small, high-value safety fix. (Theme B)
4. **Move the move-the-needle hardcoded paths in `file_ops.py:15,18,40,41` and `database.py:269,286`** into config defaults so the functions become runnable by anyone. (Theme D)
5. **Sweep bare `except:` → `except Exception as e:` + log** file-by-file (per the standard's "basename by basename" refactor approach, line 19), starting with the two hottest files: `excel_utilities.py` (7) and `database.py` (5). Ensure tests exist first per clean_code.md line 39. (Theme A)

## Suggested sequencing

Per clean_code.md line 19 ("refactoring … basename by basename") and line 39 ("for legacy code,
ensure tests exist before using AI to fix"): land the **quick wins 1–3** first (mechanical, low-risk),
then tackle **Theme A bare-excepts** one module at a time behind tests, then **Theme D config
externalization**, leaving **Theme F decomposition** for last as it is the highest-churn.

## Method / reproducibility

All counts and line numbers were produced with `grep -rn`/`sed` over `src/assetutilities/`
(test files excluded via `grep -v tests/`) on branch `feat/autorun-2026-06-19`. No code was
executed or modified. Key commands: bare-except `grep -rn "except:" --include="*.py"`;
`sys.exit` `grep -rn "sys.exit("`; hardcoded paths `grep -rEn "['\"][A-Z]:\\\\|/home/|/Users/"`;
function length via an `awk` def-to-def span heuristic.
