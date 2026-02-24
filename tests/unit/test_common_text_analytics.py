# ABOUTME: Tests for common/text_analytics.py — TextAnalytics stub class.
# ABOUTME: Covers router and get_subset_files nominal paths.

import pytest

from assetutilities.common.text_analytics import TextAnalytics


class TestTextAnalyticsInit:
    """TextAnalytics can be instantiated without arguments."""

    def test_init_returns_instance(self):
        # Act
        ta = TextAnalytics()

        # Assert
        assert isinstance(ta, TextAnalytics)


class TestTextAnalyticsRouter:
    """TextAnalytics.router delegates to get_subset_files (no-op stub)."""

    def test_router_returns_none(self):
        # Arrange
        ta = TextAnalytics()
        cfg = {}

        # Act
        result = ta.router(cfg)

        # Assert — stub implementation returns None
        assert result is None

    def test_router_does_not_raise(self):
        # Arrange
        ta = TextAnalytics()
        cfg = {"text_analytics": {"flag": True}}

        # Act / Assert — should not raise
        ta.router(cfg)


class TestTextAnalyticsGetSubsetFiles:
    """TextAnalytics.get_subset_files is a no-op stub — coverage only."""

    def test_get_subset_files_returns_none(self):
        # Arrange
        ta = TextAnalytics()
        cfg = {}

        # Act
        result = ta.get_subset_files(cfg)

        # Assert — stub returns None
        assert result is None

    def test_get_subset_files_accepts_any_cfg(self):
        # Arrange
        ta = TextAnalytics()
        cfg = {"arbitrary": "data", "nested": {"key": 42}}

        # Act / Assert — should not raise regardless of cfg contents
        ta.get_subset_files(cfg)
