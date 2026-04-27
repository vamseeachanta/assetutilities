---
purpose: Shared engineering utilities — project config, unit conversions, calculations, CLI tools
entry_points: [src/assetutilities/engine.py, src/assetutilities/calculation.py, src/assetutilities/cli/]
test_command: uv run python -m pytest tests
depends_on: []
maturity: stable
---
# assetutilities

Contract: ../AGENTS.md | Source: src/assetutilities/
Key modules: engine.py, calculation.py, calculations/, base_configs/, common/, devtools/
Canonical routing: docs/README.md, docs/maps/assetutilities-operator-map.md, docs/registry/module-routing.yaml, MODULE_STRUCTURE.md
Hygiene gate: bash scripts/hygiene/check-source-hygiene.sh
