# ABOUTME: DAG representation of quantity lineage from CalculationAuditLog.
# ABOUTME: Builds a directed graph of inputs->steps->outputs for traceability.

from __future__ import annotations

from typing import Any

from assetutilities.units.traceability import CalculationAuditLog


class LineageGraph:
    """Directed acyclic graph of unit-tracked quantity lineage.

    Nodes represent inputs and outputs; edges represent the computation
    steps that connect them.
    """

    def __init__(self) -> None:
        self._nodes: list[dict[str, Any]] = []
        self._edges: list[dict[str, str]] = []

    @classmethod
    def from_audit_log(cls, audit_log: CalculationAuditLog) -> LineageGraph:
        """Build a lineage graph from a CalculationAuditLog.

        Input quantities become input nodes, output quantities become output
        nodes, and computation steps generate edges from every input to every
        output (since the flat step list does not encode specific dependencies).
        """
        graph = cls()

        for name, tq in audit_log._inputs.items():
            graph._nodes.append(
                {
                    "name": name,
                    "value": tq.magnitude,
                    "unit": str(tq.units),
                    "role": "input",
                }
            )

        for name, tq in audit_log._outputs.items():
            graph._nodes.append(
                {
                    "name": name,
                    "value": tq.magnitude,
                    "unit": str(tq.units),
                    "role": "output",
                }
            )

        for step in audit_log._steps:
            for inp_name in audit_log._inputs:
                for out_name in audit_log._outputs:
                    graph._edges.append(
                        {
                            "source": inp_name,
                            "target": out_name,
                            "operation": step.description,
                        }
                    )

        return graph

    @property
    def nodes(self) -> list[dict[str, Any]]:
        """List of node dicts with name, value, unit, role."""
        return list(self._nodes)

    @property
    def edges(self) -> list[dict[str, str]]:
        """List of edge dicts with source, target, operation."""
        return list(self._edges)

    def to_dict(self) -> dict[str, Any]:
        """Serialize graph to a JSON-compatible dict."""
        return {
            "nodes": self.nodes,
            "edges": self.edges,
        }

    def to_dot(self) -> str:
        """Export graph in Graphviz DOT format."""
        lines = ["digraph lineage {"]
        lines.append("  rankdir=LR;")

        for node in self._nodes:
            shape = "ellipse" if node["role"] == "input" else "box"
            label = f'{node["name"]}\\n{node["value"]} {node["unit"]}'
            lines.append(f'  "{node["name"]}" [label="{label}", shape={shape}];')

        seen_edges: set[tuple[str, str]] = set()
        for edge in self._edges:
            key = (edge["source"], edge["target"])
            if key not in seen_edges:
                seen_edges.add(key)
                lines.append(
                    f'  "{edge["source"]}" -> "{edge["target"]}" '
                    f'[label="{edge["operation"]}"];'
                )

        lines.append("}")
        return "\n".join(lines)

    def to_svg(self) -> str:
        """Render the lineage graph as an SVG string.

        Requires the ``graphviz`` Python package and a Graphviz system
        installation.  Raises ``ImportError`` if graphviz is not available.
        """
        try:
            import graphviz as gv
        except ImportError:
            raise ImportError(
                "The 'graphviz' package is required for SVG rendering. "
                "Install it with: pip install graphviz"
            )

        dot = gv.Digraph("lineage", format="svg")
        dot.attr(rankdir="LR")

        for node in self._nodes:
            shape = "ellipse" if node["role"] == "input" else "box"
            label = f'{node["name"]}\n{node["value"]} {node["unit"]}'
            dot.node(node["name"], label=label, shape=shape)

        seen: set[tuple[str, str]] = set()
        for edge in self._edges:
            key = (edge["source"], edge["target"])
            if key not in seen:
                seen.add(key)
                dot.edge(edge["source"], edge["target"],
                         label=edge["operation"])

        return dot.pipe(encoding="utf-8")

    def to_html(self) -> str:
        """Render the lineage graph as a standalone HTML page.

        Uses an HTML table layout that works without any external
        dependencies.  Shows inputs, computation steps, and outputs
        with their unit metadata.
        """
        lines = [
            "<!DOCTYPE html>",
            "<html><head><meta charset='utf-8'>",
            "<title>Unit Lineage Graph</title>",
            "<style>",
            "  body { font-family: sans-serif; margin: 2em; }",
            "  table { border-collapse: collapse; margin: 1em 0; }",
            "  th, td { border: 1px solid #ccc; padding: 8px 12px; "
            "text-align: left; }",
            "  th { background: #f5f5f5; }",
            "  .input { color: #2563eb; }",
            "  .output { color: #16a34a; font-weight: bold; }",
            "</style>",
            "</head><body>",
            "<h1>Unit Lineage Graph</h1>",
        ]

        # Nodes table
        lines.append("<h2>Quantities</h2>")
        lines.append("<table><tr><th>Role</th><th>Name</th>"
                      "<th>Value</th><th>Unit</th></tr>")
        for node in self._nodes:
            css = "input" if node["role"] == "input" else "output"
            role_label = node["role"].capitalize()
            lines.append(
                f"<tr class='{css}'><td>{role_label}</td>"
                f"<td>{node['name']}</td>"
                f"<td>{node['value']}</td>"
                f"<td>{node['unit']}</td></tr>"
            )
        lines.append("</table>")

        # Edges table
        if self._edges:
            seen: set[tuple[str, str]] = set()
            lines.append("<h2>Computation Steps</h2>")
            lines.append("<table><tr><th>From</th><th>To</th>"
                          "<th>Operation</th></tr>")
            for edge in self._edges:
                key = (edge["source"], edge["target"])
                if key not in seen:
                    seen.add(key)
                    lines.append(
                        f"<tr><td>{edge['source']}</td>"
                        f"<td>{edge['target']}</td>"
                        f"<td>{edge['operation']}</td></tr>"
                    )
            lines.append("</table>")

        lines.append("</body></html>")
        return "\n".join(lines)
