"""Order-preserving comparison of two lists of document identifiers."""

from pathlib import Path

import yaml


class TextAnalytics:
    def router(self, cfg):
        return self.get_subset_files(cfg)

    def get_subset_files(self, cfg):
        data = cfg["data"]
        for key in ("set1", "set2"):
            if not isinstance(data[key], list) or not all(
                isinstance(value, str) for value in data[key]
            ):
                raise ValueError(f"data.{key} must be a list of strings")
        first = list(dict.fromkeys(data["set1"]))
        second = list(dict.fromkeys(data["set2"]))
        first_set, second_set = set(first), set(second)
        summary = {
            "common": [value for value in first if value in second_set],
            "only_in_set1": [value for value in first if value not in second_set],
            "only_in_set2": [value for value in second if value not in first_set],
        }
        summary["counts"] = {key: len(values) for key, values in summary.items()}
        summary["input_sizes"] = {key: len(data[key]) for key in ("set1", "set2")}
        folder = Path(cfg["Analysis"]["result_folder"])
        folder.mkdir(parents=True, exist_ok=True)
        output = folder / "text_analytics_comparison.yml"
        output.write_text(yaml.safe_dump(summary, sort_keys=False), encoding="utf-8")
        cfg["text_analytics"] = {"summary": summary, "output_file": str(output)}
        return cfg
