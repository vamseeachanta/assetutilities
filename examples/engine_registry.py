"""Run a custom text workflow through the engine, with outputs under --output."""

import argparse

from assetutilities.engine import engine
from assetutilities.engine_registry import EngineRunner, register_runner


@register_runner("uppercase_example")
class UppercaseRunner(EngineRunner):
    """Transform caller-supplied text; no engineering inputs or constants."""

    def run(self, cfg: dict) -> dict:
        cfg["answer"] = cfg["text"].upper()
        return cfg


def run_example(output_folder: str) -> dict:
    """Input 'alpha beta' becomes 'ALPHA BETA' by uppercasing each letter."""
    return engine(
        cfg={
            "basename": "uppercase_example",
            "text": "alpha beta",
            "default": {
                "log_level": "INFO",
                "config": {"overwrite": {"output": True}},
            },
        },
        embed=True,
        root_folder=output_folder,
        log_to_file=False,
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, help="Directory for saved config")
    args = parser.parse_args()
    print(run_example(args.output)["answer"])
