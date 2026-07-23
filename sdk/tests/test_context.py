from agentops_local import context
from agentops_local.config import Config, set_config


def setup_function():
    set_config(Config(task="default_task", session_id="s0", agent_id="a0"))


def test_falls_back_to_config_defaults():
    assert context.current_task() == "default_task"
    assert context.current_session() == "s0"
    assert context.current_agent() == "a0"


def test_nested_task_overrides_resolve_innermost():
    with context.task("outer"):
        assert context.current_task() == "outer"
        with context.task("inner"):
            assert context.current_task() == "inner"
        assert context.current_task() == "outer"
    assert context.current_task() == "default_task"  # restored on exit


def test_session_and_agent_overrides():
    with context.session("run-1"), context.agent("worker-9"):
        assert context.current_session() == "run-1"
        assert context.current_agent() == "worker-9"
    assert context.current_session() == "s0"
    assert context.current_agent() == "a0"
