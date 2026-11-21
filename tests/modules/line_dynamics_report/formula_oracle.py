"""Independent, restricted formula interpreter for report verification only.

This evaluates the extracted formula text, not the calculation implementation.
It supports only the constructs encountered here and never calls eval/exec.
It supplies a formula-consistency check, not an Excel cached-value oracle.
"""

import ast
import math
import operator

from openpyxl.formula.tokenizer import Tokenizer
from openpyxl.utils.cell import get_column_letter, range_boundaries


class FormulaOracle:
    def __init__(self, payload):
        self.workbook_name = payload.get("workbook_name", "excel_to_image.xlsx")
        self.sheet = payload["formulas"][0]["sheet"]
        self.formulas = {(x["sheet"], x["cell"]): x["formula"] for x in payload["formulas"]}
        self.values = {(x["sheet"], x["cell"]): x["value"] for x in payload["inputs"]}
        self.redacted = {(x["sheet"], x["cell"]) for x in payload["inputs"] if x.get("redacted")}

    def value(self, address, sheet=None):
        sheet = sheet or self.sheet
        key = (sheet, address)
        if key in self.redacted:
            raise ValueError("Identifying input is redacted")
        if key in self.values:
            return self.values[key]
        expression = []
        for token in Tokenizer(self.formulas[key]).items:
            if token.type == "OPERAND" and token.subtype == "RANGE":
                expression.append(f"REF({token.value!r})")
            elif token.type == "FUNC" and token.subtype == "OPEN":
                expression.append(token.value.replace("_xlfn.", ""))
            elif token.type == "OPERAND" and token.subtype == "TEXT":
                expression.append(repr(token.value[1:-1].replace('""', '"')))
            elif token.type == "OPERATOR-INFIX" and token.value == "&":
                expression.append("+")
            else:
                expression.append(token.value)
        result = self.visit(ast.parse("".join(expression), mode="eval").body)
        self.values[key] = 0 if result is None else result
        return self.values[key]

    def reference(self, reference):
        if "!" in reference:
            sheet, reference = reference.rsplit("!", 1)
            sheet = sheet.strip("'")
        else:
            sheet = self.sheet
        if ":" not in reference:
            return self.value(reference.replace("$", ""), sheet)
        left, top, right, bottom = range_boundaries(reference)
        return [
            self.value(f"{get_column_letter(c)}{r}", sheet)
            for r in range(top, bottom + 1) for c in range(left, right + 1)
        ]

    def visit(self, node):
        if isinstance(node, ast.Constant):
            return node.value
        if isinstance(node, ast.BinOp):
            operations = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul}
            return operations[type(node.op)](self.visit(node.left), self.visit(node.right))
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
            return -self.visit(node.operand)
        if isinstance(node, ast.Compare):
            assert len(node.ops) == 1
            operations = {ast.Gt: operator.gt, ast.Lt: operator.lt}
            return operations[type(node.ops[0])](self.visit(node.left), self.visit(node.comparators[0]))
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            args = [self.visit(arg) for arg in node.args]
            name = node.func.id
            if name == "REF":
                return self.reference(*args)
            if name in {"MAX", "MIN"}:
                numbers = [x for x in args[0] if isinstance(x, (int, float))]
                return (max(numbers) if name == "MAX" else min(numbers)) if numbers else 0
            if name == "CELL":
                assert args == ["filename"]
                return f"[{self.workbook_name}]" + self.sheet
            functions = {
                "INT": lambda x: math.floor(float(x)),
                "LEFT": lambda text, count: text[:count],
                "RIGHT": lambda text, count: text[-count:] if count else "",
                "TEXTAFTER": lambda text, delimiter: text.split(delimiter, 1)[1],
                "IF": lambda condition, yes, no: yes if condition else no,
                "LEN": len,
                "FIND": lambda needle, text: text.index(needle) + 1,
            }
            return functions[name](*args)
        raise ValueError(f"Unsupported formula syntax: {type(node).__name__}")
