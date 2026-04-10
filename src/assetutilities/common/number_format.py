# ABOUTME: Number formatting utilities for scientific and engineering notation.
# ABOUTME: Extracted from common/data.py NumberFormat class.
from __future__ import annotations

from typing import Any


class NumberFormat:
    def __init__(self) -> None:
        pass

    def format_number(self, number: Any, format_string: str) -> str:
        return format_string.format(number)

    def eformat(f: Any, prec: int, exp_digits: int) -> str:
        s = "%.*e" % (prec, f)
        mantissa, exp = s.split("e")
        return "%se%0*d" % (mantissa, exp_digits, int(exp))
