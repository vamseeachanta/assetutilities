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
