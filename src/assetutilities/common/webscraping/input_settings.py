"""Resolve scraper defaults without changing the caller's configuration."""

from collections.abc import Mapping
from copy import deepcopy


def iter_input_items(cfg):
    """Overlay legacy defaults, explicit defaults, then each input item.

    ``settings_master`` is the packaged legacy spelling; ``input_settings``
    is the spelling consumed by the scrapers. Both remain accepted. Overlay
    semantics match Python's dictionary update (Language Reference, 3.9,
    Dictionary displays); an item replaces a whole value at the same key.
    """
    defaults = {}
    for key in ("settings_master", "input_settings"):
        settings = cfg.get(key, {})
        if not isinstance(settings, Mapping):
            raise ValueError(f"{key} must be a mapping")
        defaults.update(settings)
    items = cfg["input"]
    if not isinstance(items, list) or any(
        not isinstance(item, Mapping) for item in items
    ):
        raise ValueError("input must be a list of mappings")
    for item in items:
        yield deepcopy({**defaults, **item})
