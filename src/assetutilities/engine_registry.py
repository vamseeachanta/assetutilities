"""Explicit workflow registration, following common.reportgen.writers.

Registration is performed by trusted Python code, never by importing a class
path supplied in YAML. Register extensions at application startup.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable
from inspect import isabstract


class EngineRunner(ABC):
    """A no-argument runner constructed for each engine dispatch."""

    @abstractmethod
    def run(self, cfg: dict) -> dict:
        """Process the prepared configuration and return it (or a replacement)."""


class RunnerRegistry:
    """Map exact basenames to concrete runners without silent replacement."""

    def __init__(self) -> None:
        self._runners: dict[str, type[EngineRunner]] = {}

    def register(
        self, *names: str
    ) -> Callable[[type[EngineRunner]], type[EngineRunner]]:
        """Decorate a runner with one or more names; reject conflicts atomically."""
        if not names or any(
            not isinstance(name, str) or not name.strip() for name in names
        ):
            raise ValueError("Runner names must be non-empty strings")
        if len(set(names)) != len(names):
            raise ValueError("Runner aliases must be distinct")

        def register_class(runner: type[EngineRunner]) -> type[EngineRunner]:
            if (
                not isinstance(runner, type)
                or not issubclass(runner, EngineRunner)
                or isabstract(runner)
                or not callable(runner.run)
            ):
                raise TypeError("Runner must be a concrete EngineRunner subclass")
            for name in names:
                if name in self._runners:
                    raise ValueError(f"Runner {name!r} is already registered")
            self._runners.update(dict.fromkeys(names, runner))
            return runner

        return register_class

    def get(self, name: str) -> type[EngineRunner] | None:
        """Return a runner class, or None so the engine can use legacy dispatch."""
        return self._runners.get(name)


runner_registry = RunnerRegistry()
register_runner = runner_registry.register


@register_runner("read_pdf")
class ReadPDFRunner(EngineRunner):
    def run(self, cfg: dict) -> dict:
        # Preserve the engine's lazy optional dependency and result placement.
        from assetutilities.modules.pdf_utilities.read_pdf import ReadPDF

        cfg["result"] = ReadPDF().read_pdf(cfg)
        return cfg


@register_runner("edit_pdf")
class EditPDFRunner(EngineRunner):
    def run(self, cfg: dict) -> dict:
        from assetutilities.modules.pdf_utilities.edit_pdf import EditPDF

        EditPDF().edit_pdf(cfg)
        return cfg


@register_runner("zip_utilities")
class ZipUtilitiesRunner(EngineRunner):
    def run(self, cfg: dict) -> dict:
        from assetutilities.modules.zip_utilities.zip_utilities import ZipUtilities

        return ZipUtilities().router(cfg)
