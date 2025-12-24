# assetutilities - Repository Skills

> Repository-specific Claude Code skills for Python data utilities and document processing.
>
> Location: `assetutilities/.claude/skills/`

## Overview

This collection provides **3 specialized skills** for the assetutilities library covering data visualization, PDF document processing, and DataFrame management. These skills are automatically activated when Claude Code determines they're relevant to the current task.

## Available Skills

| Skill | Description |
|-------|-------------|
| [plotly-visualization](plotly-visualization/SKILL.md) | Generate interactive Plotly and Matplotlib visualizations from DataFrames |
| [pdf-utilities](pdf-utilities/SKILL.md) | Read, extract, edit, and manipulate PDF documents with multiple library backends |
| [data-management](data-management/SKILL.md) | Comprehensive DataFrame loading, filtering, and transformation from Excel/CSV |

## Skill Categories

### Visualization

- **plotly-visualization**: Interactive charts (line, scatter, polar, bar), timelines, multi-series plots with Plotly and Matplotlib

### Document Processing

- **pdf-utilities**: PDF table extraction (tabula, camelot), page manipulation, fillable forms, annotations

### Data Pipeline

- **data-management**: Excel/CSV reading, DataFrame filtering, transformations, data validation

## Usage

### Automatic Activation

Skills activate automatically based on their description:

```
User: "Create an interactive line plot from this DataFrame"
Claude: [Activates plotly-visualization skill]

User: "Extract tables from this PDF document"
Claude: [Activates pdf-utilities skill]

User: "Load data from Excel and filter by column values"
Claude: [Activates data-management skill]
```

### Manual Reference

Reference skills directly in prompts:

```
"Using the plotly-visualization skill, create a timeline from the data"
"Apply the pdf-utilities skill to extract pages 5-10"
"Use the data-management skill to transform the DataFrame"
```

## Directory Structure

```
assetutilities/.claude/skills/
├── README.md                    # This file
├── plotly-visualization/
│   └── SKILL.md
├── pdf-utilities/
│   └── SKILL.md
└── data-management/
    └── SKILL.md
```

## Integration with Global Skills

These repository-specific skills complement the global skills in `~/.claude/skills/`:

- **Global**: General development, document handling, reporting
- **Repository-specific**: assetutilities library-specific data processing

## Related Documentation

- [assetutilities Product Mission](../../.agent-os/product/mission.md)
- [assetutilities Tech Stack](../../.agent-os/product/tech-stack.md)
- [Visualization Module](../../src/assetutilities/common/visualizations.py)
- [PDF Utilities Module](../../src/assetutilities/modules/pdf_utilities/)
- [Data Management Module](../../src/assetutilities/common/data_management.py)
- [Workspace Hub Skills](../../../.claude/skills/README.md)

---

*Repository-specific skills for assetutilities Python data utilities library*
