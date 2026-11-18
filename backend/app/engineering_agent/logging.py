from __future__ import annotations

import json
import logging
import os
import sys
from contextvars import ContextVar
from datetime import datetime, timezone
from typing import TextIO
from uuid import uuid4


REQUEST_ID_CONTEXT: ContextVar[str] = ContextVar(
    "engineering_agent_request_id",
    default="-",
)

LOGGER_NAME = "engineering_agent"


class RequestContextFilter(logging.Filter):
    """Attach request and application context to log records."""

    def __init__(
        self,
        *,
        application: str,
        environment: str,
    ) -> None:
        super().__init__()
        self.application = application
        self.environment = environment

    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = REQUEST_ID_CONTEXT.get()
        record.application = self.application
        record.environment = self.environment

        # Import lazily to keep logging independent of tracing setup.
        from backend.app.engineering_agent.tracing import (
            get_trace_context,
        )

        trace_context = get_trace_context()

        if trace_context is not None:
            record.trace_id = trace_context.trace_id
            record.span_id = trace_context.span_id
            record.trace_flags = trace_context.trace_flags

            if trace_context.parent_span_id is not None:
                record.parent_span_id = (
                    trace_context.parent_span_id
                )

        return True


class JsonLogFormatter(logging.Formatter):
    """Render operational logs as one JSON object per line."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, object] = {
            "timestamp": datetime.fromtimestamp(
                record.created,
                tz=timezone.utc,
            ).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "application": getattr(
                record,
                "application",
                "engineering-agent",
            ),
            "environment": getattr(
                record,
                "environment",
                "unknown",
            ),
            "request_id": getattr(
                record,
                "request_id",
                "-",
            ),
            "message": record.getMessage(),
        }

        payload["service"] = str(
            getattr(record, "service", "engineering-agent-api")
        )

        event = getattr(record, "event", None)
        if event is not None:
            payload["event"] = str(event)

        # Include distributed trace context when available.
        for field in (
            "trace_id",
            "span_id",
            "parent_span_id",
            "trace_flags",
        ):
            value = getattr(record, field, None)
            if value is not None:
                payload[field] = value

        # Serialize only explicitly approved operational metadata.
        for field in (
            "http_method",
            "http_path",
            "http_status",
            "duration_ms",
            "operation_id",
            "workflow_id",
            "dispatch_cycle_id",
            "dispatch_performed",
            "candidate_count",
            "scanned_count",
            "claimed_count",
            "candidate_limit",
            "claim_limit",
        ):
            value = getattr(record, field, None)
            if value is not None:
                payload[field] = value

        if record.exc_info:
            payload["exception"] = self.formatException(
                record.exc_info
            )

        return json.dumps(
            payload,
            ensure_ascii=False,
            default=str,
        )


def configure_logging(
    *,
    application: str = "engineering-agent",
    environment: str | None = None,
    stream: TextIO | None = None,
) -> logging.Logger:
    """Configure the dedicated Engineering Agent logger.

    This deliberately does not modify the root logger.
    """

    resolved_environment = (
        environment
        or os.environ.get(
            "ENGINEERING_AGENT_ENVIRONMENT",
            "development",
        )
    )

    logger = logging.getLogger(LOGGER_NAME)
    logger.setLevel(logging.INFO)
    logger.propagate = False

    formatter = JsonLogFormatter()
    context_filter = RequestContextFilter(
        application=application,
        environment=resolved_environment,
    )

    handler = next(
        (
            candidate
            for candidate in logger.handlers
            if getattr(
                candidate,
                "_engineering_agent_handler",
                False,
            )
        ),
        None,
    )

    if handler is None:
        handler = logging.StreamHandler(
            stream if stream is not None else sys.stderr
        )
        setattr(
            handler,
            "_engineering_agent_handler",
            True,
        )
        logger.addHandler(handler)

    if stream is not None:
        handler.setStream(stream)

    handler.setLevel(logging.INFO)
    handler.setFormatter(formatter)

    # Replace only this handler's context filter.
    for existing_filter in list(handler.filters):
        if isinstance(existing_filter, RequestContextFilter):
            handler.removeFilter(existing_filter)

    handler.addFilter(context_filter)

    return logger


def new_request_id() -> str:
    return str(uuid4())


def set_request_id(request_id: str):
    return REQUEST_ID_CONTEXT.set(request_id)


def reset_request_id(token) -> None:
    REQUEST_ID_CONTEXT.reset(token)


def get_request_id() -> str:
    return REQUEST_ID_CONTEXT.get()