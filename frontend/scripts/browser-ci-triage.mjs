export const TRIAGE_SCHEMA =
  "gagf.browser-ci-triage.v1";

export function escapeWorkflowCommand(
  value
) {
  return String(
    value ?? ""
  )
    .replaceAll(
      "%",
      "%25"
    )
    .replaceAll(
      "\r",
      "%0D"
    )
    .replaceAll(
      "\n",
      "%0A"
    );
}

export function annotationCommand(
  level,
  title,
  message
) {
  const supported =
    new Set([
      "error",
      "warning",
      "notice"
    ]);

  if (
    !supported.has(
      level
    )
  ) {
    throw new Error(
      `Unsupported annotation level: ${level}`
    );
  }

  return (
    `::${level} `
    + `title=${escapeWorkflowCommand(title)}::`
    + escapeWorkflowCommand(message)
  );
}

function finiteNumber(
  value,
  fallback = 0
) {
  const result =
    Number(value);

  return Number.isFinite(
    result
  )
    ? result
    : fallback;
}

export function classifyReleaseSummary(
  summary
) {
  const totals =
    summary?.totals
    ?? {};

  const diagnostics =
    summary?.diagnostics
    ?? {};

  const gateChecks =
    summary?.gate_checks
    ?? {};

  const failures =
    Array.isArray(
      summary?.failures
    )
      ? summary.failures
      : [];

  const failedChecks =
    Object.entries(
      gateChecks
    )
      .filter(
        (
          [
            ,
            passed
          ]
        ) =>
          passed !== true
      )
      .map(
        (
          [
            name
          ]
        ) =>
          name
      )
      .sort();

  const counts = {
    total:
      finiteNumber(
        totals.total
      ),
    passed:
      finiteNumber(
        totals.passed
      ),
    failed:
      finiteNumber(
        totals.failed
      ),
    skipped:
      finiteNumber(
        totals.skipped
      ),
    flaky:
      finiteNumber(
        totals.flaky
      ),
    retried:
      finiteNumber(
        totals.retried
      ),
    unexpected_warnings:
      finiteNumber(
        diagnostics.unexpected_warnings
      ),
    unexpected_errors:
      finiteNumber(
        diagnostics.unexpected_errors
      ),
    page_errors:
      finiteNumber(
        diagnostics.page_errors
      ),
    release_blocking_tests:
      finiteNumber(
        diagnostics.release_blocking_tests
      )
  };

  const releaseBlocking =
    summary?.gate !== "PASS"
    || counts.failed > 0
    || counts.skipped > 0
    || counts.flaky > 0
    || counts.retried > 0
    || counts.unexpected_errors > 0
    || counts.page_errors > 0
    || counts.release_blocking_tests > 0
    || failedChecks.length > 0;

  const warningOnly =
    !releaseBlocking
    && counts.unexpected_warnings > 0;

  const status =
    releaseBlocking
      ? "FAIL"
      : warningOnly
        ? "WARN"
        : "PASS";

  const level =
    status === "FAIL"
      ? "error"
      : status === "WARN"
        ? "warning"
        : "notice";

  return {
    schema_version:
      TRIAGE_SCHEMA,
    status,
    level,
    story:
      summary?.story
      ?? "unknown",
    gate:
      summary?.gate
      ?? "UNKNOWN",
    counts,
    failed_checks:
      failedChecks,
    failures:
      failures.map(
        (failure) => ({
          project:
            failure?.project
            ?? "unknown",
          title:
            failure?.title
            ?? "Unnamed browser test",
          file:
            failure?.file
            ?? "unknown",
          line:
            failure?.line
            ?? null
        })
      )
  };
}

export function triageMessage(
  triage
) {
  const parts = [
    `Gate ${triage.gate}`,
    `${triage.counts.passed}/${triage.counts.total} passed`,
    `${triage.counts.failed} failed`,
    `${triage.counts.skipped} skipped`,
    `${triage.counts.flaky} flaky`,
    `${triage.counts.retried} retries`,
    `${triage.counts.unexpected_errors} console errors`,
    `${triage.counts.page_errors} page errors`
  ];

  if (
    triage.failed_checks.length > 0
  ) {
    parts.push(
      "failed checks: "
      + triage.failed_checks.join(
          ", "
        )
    );
  }

  return parts.join(
    "; "
  );
}

export function triageMarkdown(
  triage
) {
  const lines = [
    "# Browser CI Triage",
    "",
    `**Status:** ${triage.status}`,
    "",
    `**Story:** ${triage.story}`,
    "",
    `**Release gate:** ${triage.gate}`,
    "",
    "## Counts",
    "",
    "| Metric | Count |",
    "|---|---:|",
    `| Total | ${triage.counts.total} |`,
    `| Passed | ${triage.counts.passed} |`,
    `| Failed | ${triage.counts.failed} |`,
    `| Skipped | ${triage.counts.skipped} |`,
    `| Flaky | ${triage.counts.flaky} |`,
    `| Retries | ${triage.counts.retried} |`,
    `| Unexpected warnings | ${triage.counts.unexpected_warnings} |`,
    `| Unexpected console errors | ${triage.counts.unexpected_errors} |`,
    `| Uncaught page errors | ${triage.counts.page_errors} |`,
    "",
    "## Failed gate checks",
    ""
  ];

  if (
    triage.failed_checks.length === 0
  ) {
    lines.push(
      "No failed gate checks."
    );
  } else {
    for (
      const check
      of triage.failed_checks
    ) {
      lines.push(
        `- ${check}`
      );
    }
  }

  lines.push(
    "",
    "## Failed browser tests",
    ""
  );

  if (
    triage.failures.length === 0
  ) {
    lines.push(
      "No failed browser tests."
    );
  } else {
    for (
      const failure
      of triage.failures
    ) {
      lines.push(
        `- \`${failure.project}\` ? ${failure.title}`
      );
    }
  }

  lines.push(
    ""
  );

  return lines.join(
    "\n"
  );
}
