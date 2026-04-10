# ABOUTME: String parsing and manipulation utilities.
# ABOUTME: Extracted from common/data.py FromString class.
from __future__ import annotations

from typing import Any, Optional


class FromString:
    def using_regex(self, ref_text: str, string: str) -> Optional[str]:
        import re

        result = re.findall(ref_text, string, re.IGNORECASE)
        if len(result) > 0:
            return result[0]
        return None

    def convert_fraction_to_float(self, frac_str: str) -> float:
        try:
            return float(frac_str)
        except ValueError:
            num, denom = frac_str.split("/")
            try:
                leading, num = num.split(" ")
                whole = float(leading)
            except ValueError:
                whole = 0
            frac = float(num) / float(denom)
            return whole - frac if whole < 0 else whole + frac

    def remove_strings(self, text: Optional[str], string_array: list[str]) -> Optional[str]:
        for string_index in range(0, len(string_array)):
            string_to_be_removed = string_array[string_index]
            if text is not None:
                text = self.remove_string(text, string_to_be_removed)
        return text

    def remove_string(self, text: str, string_to_be_removed: str) -> str:
        new_string = text.replace(string_to_be_removed, "")
        return new_string

    def get_value_by_delimiter(self, cfg: dict[str, Any]) -> Any:

        if cfg["delimiter"] == " ":
            result = cfg["text"].split()[cfg["column"] - 1]
            if cfg["data_type"] == "float":
                result = float(result)
        else:
            delimiter = cfg["delimiter"]
            result = cfg["text"].split(delimiter)[cfg["column"] - 1]
            if cfg["data_type"] == "float":
                result = float(result)

        return result

    def remove_next_line_values(self, text: str) -> str:
        return text.replace("\n", "")
