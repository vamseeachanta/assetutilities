"""Explicit, lazy workflow dispatch selected by a config's basename.

Only trusted Python code can register handlers. Config values select names;
they cannot provide import paths, classes or expressions to execute.
"""

from __future__ import annotations

from collections.abc import Callable, MutableMapping
from dataclasses import dataclass
from importlib import import_module


class HandlerRegistry:
    """Register callables accepting a cfg and returning a mapping or None."""

    def __init__(self):
        self._handlers = {}

    def register(self, name: str, handler: Callable, *, aliases: tuple = ()) -> None:
        names = (name, *aliases)
        if not callable(handler):
            raise TypeError("Workflow handler must be callable")
        if any(not isinstance(item, str) or not item for item in names):
            raise ValueError("Workflow names must be nonempty strings")
        if len(set(names)) != len(names) or any(
            item in self._handlers for item in names
        ):
            raise ValueError("Workflow name or alias already registered")
        self._handlers.update(dict.fromkeys(names, handler))

    def names(self) -> tuple:
        """Return supported names, excluding unimplemented legacy workflows."""
        return tuple(self._handlers)

    def resolve(self, name: str) -> Callable:
        if name in self._handlers:
            return self._handlers[name]
        if name in {"gitpython", "text_analytics", "csv_utilities"}:
            raise NotImplementedError(
                f"basename '{name}' is a stub and is excluded from the handler registry"
            )
        raise ValueError(f"Analysis for basename: {name} not found. ... FAIL")

    def dispatch(self, name: str, cfg: MutableMapping) -> MutableMapping:
        result = self.resolve(name)(cfg)
        if result is None:
            return cfg
        if not isinstance(result, MutableMapping):
            raise TypeError(f"Workflow '{name}' must return a mapping or None")
        return result


@dataclass(frozen=True)
class _LazyHandler:
    module: str
    attribute: str
    method: str | None = None
    result_key: str | None = None
    return_cfg: bool = False

    def __call__(self, cfg):
        target = getattr(import_module(self.module), self.attribute)
        if self.method is not None:
            target = getattr(target(), self.method)
        result = target(cfg)
        if self.result_key is not None:
            cfg[self.result_key] = result
            return cfg
        return cfg if self.return_cfg else result


registry = HandlerRegistry()

# This allowlist preserves the implemented branches of the previous engine.
# Optional dependencies are imported only when their workflow is dispatched.
_BUILTINS = {
    "excel_utilities": _LazyHandler(
        "assetutilities.modules.excel_utilities.excel_utilities",
        "ExcelUtilities",
        "excel_utility_router",
    ),
    "visualization": _LazyHandler(
        "assetutilities.common.visualization_components",
        "VisualizationComponents",
        "visualization_router",
        return_cfg=True,
    ),
    "file_management": _LazyHandler(
        "assetutilities.common.file_management",
        "FileManagement",
        "router",
        return_cfg=True,
    ),
    "file_edit": _LazyHandler(
        "assetutilities.common.file_edit", "FileEdit", "router", return_cfg=True
    ),
    "read_pdf": _LazyHandler(
        "assetutilities.modules.pdf_utilities.read_pdf",
        "ReadPDF",
        "read_pdf",
        "result",
    ),
    "edit_pdf": _LazyHandler(
        "assetutilities.modules.pdf_utilities.edit_pdf",
        "EditPDF",
        "edit_pdf",
        return_cfg=True,
    ),
    "word_utilities": _LazyHandler(
        "assetutilities.common.word_utilities",
        "WordUtilities",
        "router",
        return_cfg=True,
    ),
    "data_exploration": _LazyHandler(
        "assetutilities.modules.data_exploration.data_exploration",
        "DataExploration",
        "router",
    ),
    "web_scraping": _LazyHandler(
        "assetutilities.common.webscraping.web_scraping",
        "WebScraping",
        "router",
    ),
    "download_data": _LazyHandler(
        "assetutilities.common.download_data.dwnld_from_zipurl",
        "DownloadDataFromURL",
        "router",
    ),
    "yaml_utilities": _LazyHandler(
        "assetutilities.common.yml_utilities",
        "WorkingWithYAML",
        "router",
    ),
    "reportgen": _LazyHandler(
        "assetutilities.common.reportgen.reportgen", "run", return_cfg=True
    ),
    "zip_utilities": _LazyHandler(
        "assetutilities.modules.zip_utilities.zip_utilities",
        "ZipUtilities",
        "router",
    ),
}
for _name, _handler in _BUILTINS.items():
    registry.register(
        _name, _handler, aliases=("yml_utilities",) if _name == "yaml_utilities" else ()
    )
