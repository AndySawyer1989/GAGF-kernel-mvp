from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
import re
from contextvars import ContextVar, Token
from dataclasses import dataclass
from uuid import uuid4


_TRACEPARENT_PATTERN = re.compile(
    r"^00-([0-9a-fA-F]{32})-([0-9a-fA-F]{16})-([0-9a-fA-F]{2})$"
)


@dataclass(frozen=True, slots=True)
class TraceContext:
    """W3C Trace Context for one server-side request span."""

    trace_id: str
    span_id: str
    trace_flags: str = "00"
    parent_span_id: str | None = None

    def to_traceparent(self) -> str:
        """Return the W3C version 00 traceparent representation."""

        return (
            f"00-{self.trace_id}-{self.span_id}-{self.trace_flags}"
        )


TRACE_CONTEXT: ContextVar[TraceContext | None] = ContextVar(
    "engineering_agent_trace_context",
    default=None,
)


def new_trace_context(
    traceparent: str | None = None,
) -> TraceContext:
    """Create a server span, continuing a valid incoming trace when possible.

    Invalid or unsupported incoming headers are treated as absent.
    They never prevent the application request from proceeding.
    """

    if traceparent:
        match = _TRACEPARENT_PATTERN.fullmatch(traceparent.strip())

        if match is not None:
            trace_id, parent_span_id, trace_flags = match.groups()

            trace_id = trace_id.lower()
            parent_span_id = parent_span_id.lower()
            trace_flags = trace_flags.lower()

            if (
                trace_id != "0" * 32
                and parent_span_id != "0" * 16
            ):
                return TraceContext(
                    trace_id=trace_id,
                    span_id=uuid4().hex[:16],
                    trace_flags=trace_flags,
                    parent_span_id=parent_span_id,
                )

    return TraceContext(
        trace_id=uuid4().hex,
        span_id=uuid4().hex[:16],
    )


def set_trace_context(
    context: TraceContext,
) -> Token[TraceContext | None]:
    return TRACE_CONTEXT.set(context)


def reset_trace_context(
    token: Token[TraceContext | None],
) -> None:
    TRACE_CONTEXT.reset(token)


def get_trace_context() -> TraceContext | None:
    return TRACE_CONTEXT.get()


@contextmanager
def child_trace_context() -> Iterator[TraceContext]:
    """Create a child span and restore the previous context on exit."""
    parent = get_trace_context()

    if parent is None:
        child = new_trace_context()
    else:
        child = TraceContext(
            trace_id=parent.trace_id,
            span_id=uuid4().hex[:16],
            trace_flags=parent.trace_flags,
            parent_span_id=parent.span_id,
        )

    token = set_trace_context(child)
    try:
        yield child
    finally:
        reset_trace_context(token)
