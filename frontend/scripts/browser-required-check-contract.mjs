import {
  readFileSync
} from "node:fs";

import {
  resolve
} from "node:path";

export const REQUIRED_CHECK_NAME =
  "Browser Release Required";

export const REQUIRED_JOB_ID =
  "browser-release-required";

export const UPSTREAM_JOB_ID =
  "browser-release";

function normalizeNewlines(
  value
) {
  return String(value)
    .replaceAll(
      "\r\n",
      "\n"
    )
    .replaceAll(
      "\r",
      "\n"
    );
}

function extractTopLevelSection(
  workflow,
  heading,
  nextHeading
) {
  const normalized =
    normalizeNewlines(
      workflow
    );

  const startPattern =
    new RegExp(
      `^${heading}:\\s*$`,
      "m"
    );

  const startMatch =
    startPattern.exec(
      normalized
    );

  if (
    !startMatch
  ) {
    return "";
  }

  const start =
    startMatch.index
    + startMatch[0].length;

  const remainder =
    normalized.slice(
      start
    );

  if (
    !nextHeading
  ) {
    return remainder;
  }

  const nextPattern =
    new RegExp(
      `^${nextHeading}:\\s*$`,
      "m"
    );

  const nextMatch =
    nextPattern.exec(
      remainder
    );

  return nextMatch
    ? remainder.slice(
        0,
        nextMatch.index
      )
    : remainder;
}

function extractJobSection(
  workflow,
  jobId
) {
  const jobsSection =
    extractTopLevelSection(
      workflow,
      "jobs"
    );

  const normalized =
    normalizeNewlines(
      jobsSection
    );

  const jobPattern =
    new RegExp(
      `^  ${jobId}:\\s*$`,
      "m"
    );

  const jobMatch =
    jobPattern.exec(
      normalized
    );

  if (
    !jobMatch
  ) {
    return "";
  }

  const start =
    jobMatch.index
    + jobMatch[0].length;

  const remainder =
    normalized.slice(
      start
    );

  const nextJobMatch =
    /^  [a-zA-Z0-9_-]+:\s*$/m.exec(
      remainder
    );

  return nextJobMatch
    ? remainder.slice(
        0,
        nextJobMatch.index
      )
    : remainder;
}

function includesTrigger(
  onSection,
  trigger
) {
  const triggerPattern =
    new RegExp(
      `^  ${trigger}:`,
      "m"
    );

  return triggerPattern.test(
    onSection
  );
}

export function evaluateRequiredCheckContract(
  workflow
) {
  const onSection =
    extractTopLevelSection(
      workflow,
      "on",
      "permissions"
    );

  const requiredJob =
    extractJobSection(
      workflow,
      REQUIRED_JOB_ID
    );

  const checks = {
    pull_request_trigger:
      includesTrigger(
        onSection,
        "pull_request"
      ),

    push_trigger:
      includesTrigger(
        onSection,
        "push"
      ),

    merge_group_trigger:
      includesTrigger(
        onSection,
        "merge_group"
      ),

    workflow_dispatch_trigger:
      includesTrigger(
        onSection,
        "workflow_dispatch"
      ),

    required_job_present:
      requiredJob.length > 0,

    required_check_name:
      new RegExp(
        `^    name:\\s*${REQUIRED_CHECK_NAME}\\s*$`,
        "m"
      ).test(
        requiredJob
      ),

    required_job_always_runs:
      /^    if:\s*always\(\)\s*$/m.test(
        requiredJob
      ),

    required_job_needs_upstream:
      new RegExp(
        `^\\s*-\\s*${UPSTREAM_JOB_ID}\\s*$`,
        "m"
      ).test(
        requiredJob
      )
      || new RegExp(
        `^    needs:\\s*${UPSTREAM_JOB_ID}\\s*$`,
        "m"
      ).test(
        requiredJob
      ),

    upstream_result_exposed:
      new RegExp(
        `needs\\.${UPSTREAM_JOB_ID}\\.result`
      ).test(
        requiredJob
      ),

    non_success_result_rejected:
      /!=\s*["']success["']/.test(
        requiredJob
      ),

    failure_exit_present:
      /\bexit\s+1\b/.test(
        requiredJob
      )
  };

  const failedChecks =
    Object.entries(
      checks
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

  return {
    schema_version:
      "gagf.browser-required-check-contract.v1",
    status:
      failedChecks.length === 0
        ? "PASS"
        : "FAIL",
    required_check:
      REQUIRED_CHECK_NAME,
    required_job:
      REQUIRED_JOB_ID,
    upstream_job:
      UPSTREAM_JOB_ID,
    checks,
    failed_checks:
      failedChecks
  };
}

export function requiredCheckMarkdown(
  result
) {
  const lines = [
    "# Browser Required-Check Contract",
    "",
    `**Status:** ${result.status}`,
    "",
    `**Required check:** ${result.required_check}`,
    "",
    "| Contract | Result |",
    "|---|---|"
  ];

  for (
    const [
      name,
      passed
    ]
    of Object.entries(
      result.checks
    )
  ) {
    lines.push(
      `| ${name} | ${passed ? "PASS" : "FAIL"} |`
    );
  }

  lines.push(
    ""
  );

  if (
    result.failed_checks.length === 0
  ) {
    lines.push(
      "All required-check invariants passed."
    );
  } else {
    lines.push(
      "## Failed invariants",
      ""
    );

    for (
      const failedCheck
      of result.failed_checks
    ) {
      lines.push(
        `- ${failedCheck}`
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

export function loadWorkflow(
  workflowPath
) {
  return readFileSync(
    resolve(
      workflowPath
    ),
    "utf-8"
  );
}
