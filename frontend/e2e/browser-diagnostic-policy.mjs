const REDACTED =
  "[REDACTED]";

const NORMALIZED_TIMESTAMP =
  "[TIMESTAMP]";

const NORMALIZED_LOCAL_PATH =
  "[LOCAL_PATH]";

const SENSITIVE_KEY_PATTERN =
  [
    "access_token",
    "api_key",
    "apikey",
    "authorization",
    "client_secret",
    "cookie",
    "id_token",
    "password",
    "refresh_token",
    "secret",
    "session",
    "signature",
    "token",
    "x-api-key"
  ].join("|");

const EXPECTED_WARNING_PATTERNS = [
  /download the react devtools/i,
  /third-party cookie/i
];

function redactSensitivePairs(
  value
) {
  const quotedPairPattern =
    new RegExp(
      `(["']?(?:${SENSITIVE_KEY_PATTERN})["']?\\s*[:=]\\s*["']?)([^"',\\s;&]+)`,
      "gi"
    );

  const queryPairPattern =
    new RegExp(
      `([?&](?:${SENSITIVE_KEY_PATTERN})=)([^&#\\s]+)`,
      "gi"
    );

  return value
    .replace(
      quotedPairPattern,
      `$1${REDACTED}`
    )
    .replace(
      queryPairPattern,
      `$1${REDACTED}`
    );
}

function redactAuthorizationValues(
  value
) {
  return value
    .replace(
      /\bBearer\s+[A-Za-z0-9._~+/\-=]+/gi,
      `Bearer ${REDACTED}`
    )
    .replace(
      /\bBasic\s+[A-Za-z0-9+/=]+/gi,
      `Basic ${REDACTED}`
    )
    .replace(
      /\beyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\b/g,
      REDACTED
    );
}

function normalizeVolatileValues(
  value
) {
  return value
    .replace(
      /\b\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z\b/g,
      NORMALIZED_TIMESTAMP
    )
    .replace(
      /\b[A-Za-z]:\\(?:[^\\\r\n:*?"<>|]+\\)*[^\\\r\n:*?"<>|]*/g,
      NORMALIZED_LOCAL_PATH
    )
    .replace(
      /file:\/\/\/[A-Za-z]:\/[^\s)"']+/gi,
      NORMALIZED_LOCAL_PATH
    );
}

export function redactSensitiveText(
  input
) {
  if (
    input === null
    || input === undefined
  ) {
    return "";
  }

  let value =
    String(input);

  value =
    redactAuthorizationValues(
      value
    );

  value =
    redactSensitivePairs(
      value
    );

  value =
    normalizeVolatileValues(
      value
    );

  return value;
}

function sanitizeLocation(
  location
) {
  if (
    !location
  ) {
    return undefined;
  }

  return {
    url:
      location.url
        ? redactSensitiveText(
            location.url
          )
        : undefined,
    lineNumber:
      Number.isInteger(
        location.lineNumber
      )
        ? location.lineNumber
        : undefined,
    columnNumber:
      Number.isInteger(
        location.columnNumber
      )
        ? location.columnNumber
        : undefined
  };
}

export function sanitizeDiagnostic(
  diagnostic,
  eventIndex
) {
  return {
    event_index:
      eventIndex,
    source:
      diagnostic.source,
    level:
      diagnostic.level,
    message:
      redactSensitiveText(
        diagnostic.message
      ),
    location:
      sanitizeLocation(
        diagnostic.location
      ),
    stack:
      diagnostic.stack
        ? redactSensitiveText(
            diagnostic.stack
          )
        : undefined
  };
}

export function isExpectedWarning(
  message
) {
  return EXPECTED_WARNING_PATTERNS.some(
    (pattern) =>
      pattern.test(
        message
      )
  );
}

export function evaluateDiagnosticPolicy(
  diagnostics
) {
  const expectedWarnings = [];
  const unexpectedWarnings = [];
  const unexpectedErrors = [];
  const pageErrors = [];

  for (
    const diagnostic
    of diagnostics
  ) {
    if (
      diagnostic.source
      === "pageerror"
    ) {
      pageErrors.push(
        diagnostic
      );

      continue;
    }

    if (
      diagnostic.level
      === "error"
    ) {
      unexpectedErrors.push(
        diagnostic
      );

      continue;
    }

    if (
      diagnostic.level
      === "warning"
    ) {
      if (
        isExpectedWarning(
          diagnostic.message
        )
      ) {
        expectedWarnings.push(
          diagnostic
        );
      } else {
        unexpectedWarnings.push(
          diagnostic
        );
      }
    }
  }

  return {
    expected_warnings:
      expectedWarnings.length,
    unexpected_warnings:
      unexpectedWarnings.length,
    unexpected_errors:
      unexpectedErrors.length,
    page_errors:
      pageErrors.length,
    release_blocking:
      unexpectedErrors.length > 0
      || pageErrors.length > 0,
    expected_warning_events:
      expectedWarnings,
    unexpected_warning_events:
      unexpectedWarnings,
    unexpected_error_events:
      unexpectedErrors,
    page_error_events:
      pageErrors
  };
}
