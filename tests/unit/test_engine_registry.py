"""Registry contracts; expected identities and calls follow explicit fixtures."""

import pytest

from assetutilities.engine_registry import EngineRunner, RunnerRegistry


class EchoRunner(EngineRunner):
    def run(self, cfg):
        return cfg


def test_register_and_resolve_aliases():
    registry = RunnerRegistry()
    assert registry.register("echo", "echo_alias")(EchoRunner) is EchoRunner
    assert registry.get("echo") is EchoRunner
    assert registry.get("echo_alias") is EchoRunner
    assert registry.get("unknown") is None


def test_registries_are_independent():
    first, second = RunnerRegistry(), RunnerRegistry()
    first.register("echo")(EchoRunner)
    assert second.get("echo") is None


def test_duplicate_registration_is_atomic():
    registry = RunnerRegistry()
    registry.register("echo")(EchoRunner)
    with pytest.raises(ValueError, match="already registered"):
        registry.register("new_alias", "echo")(EchoRunner)
    assert registry.get("new_alias") is None
    assert registry.get("echo") is EchoRunner


@pytest.mark.parametrize("names", [(), ("",), (" ",), (None,), ("echo", "echo")])
def test_invalid_names_do_not_register(names):
    registry = RunnerRegistry()
    with pytest.raises(ValueError):
        registry.register(*names)(EchoRunner)
    assert registry.get("echo") is None


@pytest.mark.parametrize("runner", [object, EchoRunner(), EngineRunner, None])
def test_invalid_runner_is_rejected(runner):
    registry = RunnerRegistry()
    with pytest.raises(TypeError):
        registry.register("invalid")(runner)
    assert registry.get("invalid") is None


def test_noncallable_run_is_rejected():
    class BrokenRunner(EngineRunner):
        run = None

    with pytest.raises(TypeError):
        RunnerRegistry().register("broken")(BrokenRunner)
