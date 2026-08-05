import {
  existsSync,
  mkdirSync,
  readFileSync,
  writeFileSync
} from "node:fs";

import {
  dirname,
  resolve
} from "node:path";

import {
  annotationCommand,
  classifyReleaseSummary,
  triageMarkdown,
  triageMessage
} from "./browser-ci-triage.mjs";

const root =
  process.cwd();

const resultsDirectory =
  resolve(
    root,
    "test-evidence",
    "playwright",
    "results"
  );

const releaseSummaryPath =
  resolve(
    resultsDirectory,
    "release-summary.json"
  );

const triageJsonPath =
  resolve(
    resultsDirectory,
    "ci-triage.json"
  );

const triageMarkdownPath =
  resolve(
    resultsDirectory,
    "ci-triage.md"
  );

mkdirSync(
  dirname(
    triageJsonPath
  ),
  {
    recursive: true
  }
);

if (
  !existsSync(
    releaseSummaryPath
  )
) {
  const message =
    "Browser release summary was not generated. "
    + "Inspect the workflow logs and uploaded raw evidence.";

  console.log(
    annotationCommand(
      "error",
      "Browser release evidence missing",
      message
    )
  );

  const missingTriage = {
    schema_version:
      "gagf.browser-ci-triage.v1",
    status:
      "FAIL",
    level:
      "error",
    story:
      process.env.GAGF_STORY_ID
      ?? "unknown",
    gate:
      "MISSING",
    counts: {
      total: 0,
      passed: 0,
      failed: 0,
      skipped: 0,
      flaky: 0,
      retried: 0,
      unexpected_warnings: 0,
      unexpected_errors: 0,
      page_errors: 0,
      release_blocking_tests: 0
    },
    failed_checks: [
      "release_summary_present"
    ],
    failures: []
  };

  writeFileSync(
    triageJsonPath,
    JSON.stringify(
      missingTriage,
      null,
      2
    )
    + "\n",
    "utf-8"
  );

  writeFileSync(
    triageMarkdownPath,
    triageMarkdown(
      missingTriage
    ),
    "utf-8"
  );

  process.exit(1);
}

const summary =
  JSON.parse(
    readFileSync(
      releaseSummaryPath,
      "utf-8"
    )
  );

const triage =
  classifyReleaseSummary(
    summary
  );

const message =
  triageMessage(
    triage
  );

console.log(
  annotationCommand(
    triage.level,
    `Browser release ${triage.status}`,
    message
  )
);

for (
  const failure
  of triage.failures.slice(
    0,
    10
  )
) {
  console.log(
    annotationCommand(
      "error",
      `Failed: ${failure.project}`,
      failure.title
    )
  );
}

writeFileSync(
  triageJsonPath,
  JSON.stringify(
    triage,
    null,
    2
  )
  + "\n",
  "utf-8"
);

writeFileSync(
  triageMarkdownPath,
  triageMarkdown(
    triage
  ),
  "utf-8"
);

console.log(
  `CI triage status: ${triage.status}`
);

console.log(
  "CI triage JSON: "
  + "test-evidence/playwright/results/ci-triage.json"
);

console.log(
  "CI triage Markdown: "
  + "test-evidence/playwright/results/ci-triage.md"
);

if (
  triage.status === "FAIL"
) {
  process.exitCode = 1;
}
