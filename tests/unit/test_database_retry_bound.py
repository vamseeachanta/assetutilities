# ABOUTME: Regression tests for the bounded db retry decorator (issue #80).
# ABOUTME: The retry must terminate after a declared attempt budget, never recurse unbounded.

import pytest

try:
    from assetutilities.common.database import Database
except ModuleNotFoundError as exc:  # pragma: no cover - env-dependent
    pytest.skip(
        f"assetutilities.common optional dependency missing: {exc}",
        allow_module_level=True,
    )


def _always_failing(budget):
    """Build a class whose decorated method always raises, counting its calls.

    The attempt budget is injected rather than hardcoded so the tests assert the
    decorator honours the declared DB_RETRY_MAX_ATTEMPTS attribute, not some
    constant baked into the decorator body.
    """

    class Probe:
        DB_RETRY_MAX_ATTEMPTS = budget

        def __init__(self):
            self.calls = 0

        @Database.db_retry_decorator
        def operation(self):
            self.calls += 1
            raise RuntimeError("persistent failure")

    return Probe()


class TestRetryIsBounded:
    def test_attempt_count_equals_declared_budget_of_two(self):
        probe = _always_failing(2)
        with pytest.raises(RuntimeError):
            probe.operation()
        assert probe.calls == 2

    def test_attempt_count_equals_declared_budget_of_seven(self):
        probe = _always_failing(7)
        with pytest.raises(RuntimeError):
            probe.operation()
        assert probe.calls == 7

    def test_persistent_failure_raises_the_original_error_not_recursionerror(self):
        probe = _always_failing(3)
        with pytest.raises(RuntimeError) as excinfo:
            probe.operation()
        assert str(excinfo.value) == "persistent failure"

    def test_default_budget_is_a_finite_positive_integer(self):
        # The value itself is a policy choice, not a derived quantity; what the
        # security fix requires is that it exists and is finite.
        assert Database.DB_RETRY_MAX_ATTEMPTS > 0


class TestRetryStillSucceeds:
    def test_operation_succeeding_on_second_attempt_returns_its_value(self):
        class Probe:
            DB_RETRY_MAX_ATTEMPTS = 5

            def __init__(self):
                self.calls = 0

            @Database.db_retry_decorator
            def operation(self):
                self.calls += 1
                if self.calls < 2:
                    raise RuntimeError("transient failure")
                return "settled"

        assert Probe().operation() == "settled"

    def test_operation_succeeding_immediately_is_called_exactly_once(self):
        class Probe:
            DB_RETRY_MAX_ATTEMPTS = 5

            def __init__(self):
                self.calls = 0

            @Database.db_retry_decorator
            def operation(self):
                self.calls += 1
                return "ok"

        probe = Probe()
        probe.operation()
        assert probe.calls == 1
