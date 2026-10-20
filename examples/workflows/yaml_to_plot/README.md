# YAML plotting

The example extracts arrays from a YAML document and writes an interactive HTML
plot with its JavaScript embedded. It requires no network connection to generate
or view the Cartesian line chart.

## Summary

The chosen dimensionless inputs are slope 2, intercept 1 and x values 0, 1, 2.
The plotted answer is the three points (0, 1), (1, 3), (2, 5). This is synthetic
example data, not a physical response or an engineering acceptance check.

## Revision history

| Revision | Date | Change and reason |
|---|---|---|
| Initial | 2026-10-19 | Add a neutral worked example for the registered YAML plotting workflow. |

## Inputs, method and answer

`data/linear_response.yml` supplies the arrays. The example defines y = 2*x + 1;
the slope and intercept are arbitrary required inputs to this hand calculation,
not constants supplied by the library. Substitution gives:

| x | Hand calculation | y |
|---|---|---|
| 0 | 2*0 + 1 | 1 |
| 1 | 2*1 + 1 | 3 |
| 2 | 2*2 + 1 | 5 |

`input.yml` selects the arrays with `[response, samples, 0, x]` and
`[response, samples, 0, y]`. The zero selects the first sequence element.
The workflow loads these values and plots them unchanged; it performs no fit,
interpolation or engineering calculation. The extraction and engine tests assert
these independently calculated coordinates.

Run from the repository root in an environment with the package installed:

```bash
uv run python -m assetutilities examples/workflows/yaml_to_plot/input.yml
```

The report is `results/Plot/input.html` beside the input file. The configuration
dump and logs are generated outputs and are excluded from version control.

## Report options and limits

`settings.plt_engine: plotly` and `settings.plt_save_extensions: [".html"]`
select HTML. Existing matplotlib configurations retain their current behavior.
`plot_yml_data.report.provenance: true` adds package version, generation time in
UTC, source basenames and the escaped original input YAML. The original is reread
because extraction replaces key-chain mappings with arrays in the live config.
An in-memory configuration has no input file to echo. Missing or malformed input
and missing HTML are handled without preventing use of the generated plot.

The echo includes the full supplied YAML. Only enable it for input text suitable
for distribution with the report. Metadata uses basenames; paths or other private
text explicitly supplied inside the input remain part of its echo. This is
provenance, not a reproducible digest or an engineering verdict. Dynamic map
layers, remote image URLs and other user-supplied external resources are outside
this Cartesian example's offline guarantee. No browser rendering check is made.

Plotly's [write_html API documentation](https://plotly.com/python-api-reference/generated/plotly.io.write_html.html)
(accessed 2026-10-19, `include_plotlyjs` parameter) specifies that `True` embeds
the JavaScript for offline use. Inline bundles contain dormant URL strings, so
tests check actual script/link resources rather than searching every string in
the bundle. The standards examples and both existing HTML writers use this mode.
