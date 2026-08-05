export type DiagnosticLocation = {
  url?: string;
  lineNumber?: number;
  columnNumber?: number;
};

export type PolicyDiagnostic = {
  event_index?: number;
  source:
    | "console"
    | "pageerror";
  level:
    | "warning"
    | "error";
  message: string;
  location?: DiagnosticLocation;
  stack?: string;
};

export type DiagnosticPolicyResult = {
  expected_warnings: number;
  unexpected_warnings: number;
  unexpected_errors: number;
  page_errors: number;
  release_blocking: boolean;
  expected_warning_events:
    PolicyDiagnostic[];
  unexpected_warning_events:
    PolicyDiagnostic[];
  unexpected_error_events:
    PolicyDiagnostic[];
  page_error_events:
    PolicyDiagnostic[];
};

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
  value: string
): string {
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
  value: string
): string {
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
  value: string
): string {
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
  input: unknown
): string {
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

  return normalizeVolatileValues(
    value
  );
}

function sanitizeLocation(
  location:
    DiagnosticLocation
    | undefined
): DiagnosticLocation | undefined {
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
  diagnostic:
    PolicyDiagnostic,
  eventIndex: number
): PolicyDiagnostic {
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
  message: string
): boolean {
  return EXPECTED_WARNING_PATTERNS.some(
    (pattern) =>
      pattern.test(
        message
      )
  );
}

const EXPECTED_HTTP_STATUSES_BY_TEST_TITLE:
  Readonly<Record<string, readonly number[]>> = {
    "shows a safe failure when required audit data is unavailable": [
      503
    ],
    "keeps required audit data usable during optional-service degradation": [
      503
    ],
    "rejects an unauthorized checkpoint and recovers on retry": [
      403
    ],
    "does not expose protected checkpoint data after authorization failure": [
      403
    ]
  };

export type ExpectedHttpDiagnosticPartition = {
  enforced_diagnostics:
    PolicyDiagnostic[];
  expected_http_error_events:
    PolicyDiagnostic[];
};

export function extractHttpStatus(
  message: string
): number | undefined {
  const match =
    message.match(
      /status of\s+(\d{3})\b/i
    );

  if (
    !match
  ) {
    return undefined;
  }

  const status =
    Number(match[1]);

  return Number.isInteger(
    status
  )
    ? status
    : undefined;
}

export function partitionExpectedHttpDiagnostics(
  diagnostics:
    PolicyDiagnostic[],
  testTitle: string
): ExpectedHttpDiagnosticPartition {
  const allowedStatuses =
    new Set(
      EXPECTED_HTTP_STATUSES_BY_TEST_TITLE[
        testTitle
      ] ?? []
    );

  const enforcedDiagnostics:
    PolicyDiagnostic[] = [];

  const expectedHttpErrors:
    PolicyDiagnostic[] = [];

  for (
    const diagnostic
    of diagnostics
  ) {
    const status =
      extractHttpStatus(
        diagnostic.message
      );

    const expected =
      diagnostic.source === "console"
      && diagnostic.level === "error"
      && status !== undefined
      && allowedStatuses.has(
        status
      )
      && /failed to load resource/i.test(
        diagnostic.message
      );

    if (
      expected
    ) {
      expectedHttpErrors.push(
        diagnostic
      );
    } else {
      enforcedDiagnostics.push(
        diagnostic
      );
    }
  }

  return {
    enforced_diagnostics:
      enforcedDiagnostics,
    expected_http_error_events:
      expectedHttpErrors
  };
}

export function evaluateDiagnosticPolicy(
  diagnostics:
    PolicyDiagnostic[]
): DiagnosticPolicyResult {
  const expectedWarnings:
    PolicyDiagnostic[] = [];

  const unexpectedWarnings:
    PolicyDiagnostic[] = [];

  const unexpectedErrors:
    PolicyDiagnostic[] = [];

  const pageErrors:
    PolicyDiagnostic[] = [];

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
