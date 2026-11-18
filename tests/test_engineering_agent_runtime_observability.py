import pytest

from backend.app.engineering_agent.tracing import (
    TraceContext,
    child_trace_context,
    get_trace_context,
    set_trace_context,
    reset_trace_context,
)


def test_child_trace_context_creates_root_when_no_parent_exists():
    assert get_trace_context() is None

    with child_trace_context() as child:
        assert len(child.trace_id) == 32
        assert len(child.span_id) == 16
        assert child.parent_span_id is None
        assert get_trace_context() == child

    assert get_trace_context() is None


def test_child_trace_context_inherits_trace_and_links_parent_span():
    parent = TraceContext(
        trace_id="a" * 32,
        span_id="b" * 16,
        trace_flags="01",
    )
    token = set_trace_context(parent)

    try:
        with child_trace_context() as child:
            assert child.trace_id == parent.trace_id
            assert child.span_id != parent.span_id
            assert child.parent_span_id == parent.span_id
            assert child.trace_flags == parent.trace_flags
            assert get_trace_context() == child

        assert get_trace_context() == parent
    finally:
        reset_trace_context(token)


def test_nested_child_spans_preserve_parent_chain():
    parent = TraceContext(
        trace_id="c" * 32,
        span_id="d" * 16,
        trace_flags="01",
    )
    token = set_trace_context(parent)

    try:
        with child_trace_context() as first_child:
            with child_trace_context() as second_child:
                assert second_child.trace_id == parent.trace_id
                assert second_child.parent_span_id == first_child.span_id
                assert second_child.span_id != first_child.span_id

            assert get_trace_context() == first_child

        assert get_trace_context() == parent
    finally:
        reset_trace_context(token)


def test_child_trace_context_restores_parent_after_exception():
    parent = TraceContext(
        trace_id="e" * 32,
        span_id="f" * 16,
        trace_flags="00",
    )
    token = set_trace_context(parent)

    try:
        with pytest.raises(RuntimeError, match="operation failed"):
            with child_trace_context():
                raise RuntimeError("operation failed")

        assert get_trace_context() == parent
    finally:
        reset_trace_context(token)