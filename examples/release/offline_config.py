"""Run the documented defaults-overlay example without contacting a service."""

import json

from assetutilities.common.webscraping.input_settings import iter_input_items


def example():
    inputs = {
        "settings_master": {"url": "https://example.invalid/default", "save_csv": True},
        "input_settings": {"output_dir": "results"},
        "input": [{"label": "sample", "url": "https://example.invalid/sample"}],
    }
    return list(iter_input_items(inputs))


if __name__ == "__main__":
    print(json.dumps(example(), indent=2))
