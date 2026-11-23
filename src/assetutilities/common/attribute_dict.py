# ABOUTME: Dictionary subclasses that support attribute-style access.
# ABOUTME: Extracted from common/data.py AttributeDict and objdict classes.
from __future__ import annotations

from typing import Any


class AttributeDict(dict):  # type: ignore[type-arg]
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.__dict__ = self


class objdict(dict):
    # TODO Test this attribute dictionary method
    def __getattr__(self, name: str) -> Any:
        if name in self:
            return self[name]
        else:
            raise AttributeError("No such attribute: " + name)

    def __setattr__(self, name: str, value: Any) -> None:
        self[name] = value

    def __delattr__(self, name: str) -> None:
        if name in self:
            del self[name]
        else:
            raise AttributeError("No such attribute: " + name)
