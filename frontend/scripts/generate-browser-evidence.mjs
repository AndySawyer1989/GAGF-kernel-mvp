import {
  existsSync,
  mkdirSync,
  readFileSync,
  writeFileSync
} from "node:fs";

import {
  execFileSync
} from "node:child_process";

import {
  dirname,
  relative,
  resolve
} from "node:path";

const SCHEMA_VERSION =
  "gagf.browser-release-evidence.v1";

const STORY_ID =
  process.env.GAGF_STORY_ID
  ?? "GRA-UI-010J";

const EXPECTED_TESTS =
  Number.parseInt(
    process.env.GAGF_EXPECTED_BROWSER_TESTS
    ?? "58",
    10
  );

const REQUIRED_PROJECTS = [
  "desktop-chromium",
  "mobile-chromium"
];

const root =
  process.cwd();

const evidenceRoot =
  resolve(
    root,
    "test-evidence",
    "playwright"
  );

const resultsPath =
  resolve(
    evidenceRoot,
    "results",
    "results.json"
  );

const summaryJsonPath =
  resolve(
    evidenceRoot,
    "results",
    "release-summary.json"
  );

const summaryMarkdownPath =
  resolve(
    evidenceRoot,
    "results",
    "release-summary.md"
  );

function fail(
  message
) {
  console.error(
    `Browser evidence generation failed: ${message}`
  );

  process.exitCode = 1;
}

function readJson(
  filePath
) {
  try {
    return JSON.parse(
      readFileSync(
        filePath,
        "utf-8"
      )
    );
  } catch (error) {
    throw new Error(
      `Could not parse ${filePath}: ${
        error instanceof Error
          ? error.message
          : String(error)
      }`
    );
  }
}

function gitValue(
  args,
  fallback = "unknown"
) {
  try {
    return execFileSync(
      "git",
      args,
      {
        cwd: resolve(
          root,
          ".."
        ),
        encoding: "utf-8",
        stdio: [
          "ignore",
          "pipe",
          "ignore"
        ]
      }
    ).trim() || fallback;
  } catch {
    return fallback;
  }
}

function collectSpecs(
  suites,
  parents = [],
  output = []
) {
  for (
    const suite
    of suites ?? []
  ) {
    const currentParents = [
      ...parents,
      suite.title
    ].filter(Boolean);

    for (
      const spec
      of suite.specs ?? []
    ) {
      output.push({
        ...spec,
        suitePath:
          currentParents
      });
    }

    collectSpecs(
      suite.suites,
      currentParents,
      output
    );
  }

  return output;
}

function normalizeStatus(
  status
) {
  switch (status) {
    case "expected":
    case "passed":
      return "passed";

    case "unexpected":
    case "failed":
    case "timedOut":
    case "interrupted":
      return "failed";

    case "skipped":
      return "skipped";

    case "flaky":
      return "flaky";

    default:
      return status
        ? String(status)
        : "unknown";
  }
}

function projectNameFromTest(
  test
) {
  return (
    test.projectName
    ?? test.project?.name
    ?? test.project
    ?? "unknown"
  );
}

function artifactPathsFromResult(
  result
) {
  const artifacts = [];

  for (
    const attachment
    of result.attachments ?? []
  ) {
    artifacts.push({
      name:
        attachment.name
        ?? "unnamed",
      content_type:
        attachment.contentType
        ?? "unknown",
      path:
        attachment.path
          ? relative(
              root,
              resolve(
                root,
                attachment.path
              )
            ).replaceAll(
              "\\",
              "/"
            )
          : null,
      embedded:
        Boolean(
          attachment.body
        )
    });
  }

  return artifacts;
}

function diagnosticCountFromAttachment(
  result
) {
  for (
    const attachment
    of result.attachments ?? []
  ) {
    if (
      attachment.name
      !== "browser-diagnostics"
    ) {
      continue;
    }

    if (
      !attachment.body
    ) {
      return {
        warnings: 0,
        errors: 0,
        page_errors: 0,
        expected_warnings: 0,
        unexpected_warnings: 0,
        unexpected_errors: 0,
        release_blocking: false,
        available: false
      };
    }

    try {
      const raw =
        Buffer.from(
          attachment.body,
          "base64"
        ).toString(
          "utf-8"
        );

      const payload =
        JSON.parse(raw);

      return {
        warnings:
          Number(
            payload.counts?.warnings
            ?? 0
          ),
        errors:
          Number(
            payload.counts?.errors
            ?? 0
          ),
        page_errors:
          Number(
            payload.counts?.page_errors
            ?? 0
          ),
        expected_warnings:
          Number(
            payload.policy?.expected_warnings
            ?? 0
          ),
        unexpected_warnings:
          Number(
            payload.policy?.unexpected_warnings
            ?? 0
          ),
        unexpected_errors:
          Number(
            payload.policy?.unexpected_errors
            ?? payload.counts?.errors
            ?? 0
          ),
        release_blocking:
          Boolean(
            payload.policy?.release_blocking
          ),
        available: true
      };
    } catch {
      return {
        warnings: 0,
        errors: 0,
        page_errors: 0,
        expected_warnings: 0,
        unexpected_warnings: 0,
        unexpected_errors: 0,
        release_blocking: false,
        available: false
      };
    }
  }

  return {
    warnings: 0,
    errors: 0,
    page_errors: 0,
    available: false
  };
}

function summarizeSpec(
  spec
) {
  const tests =
    spec.tests ?? [];

  return tests.map(
    (test) => {
      const results =
        test.results ?? [];

      const finalResult =
        results.at(-1);

      const normalizedStatus =
        normalizeStatus(
          test.status
          ?? finalResult?.status
        );

      const retryCount =
        Math.max(
          0,
          results.length - 1
        );

      const durationMs =
        results.reduce(
          (
            total,
            result
          ) =>
            total
            + Number(
                result.duration
                ?? 0
              ),
          0
        );

      const diagnostics =
        finalResult
          ? diagnosticCountFromAttachment(
              finalResult
            )
          : {
              warnings: 0,
              errors: 0,
              page_errors: 0,
              available: false
            };

      return {
        title:
          [
            ...spec.suitePath,
            spec.title
          ]
            .filter(Boolean)
            .join(
              " ? "
            ),
        file:
          spec.file
          ?? "unknown",
        line:
          spec.line
          ?? null,
        column:
          spec.column
          ?? null,
        project:
          projectNameFromTest(
            test
          ),
        status:
          normalizedStatus,
        expected_status:
          test.expectedStatus
          ?? "passed",
        retries:
          retryCount,
        duration_ms:
          durationMs,
        errors:
          results.flatMap(
            (result) =>
              result.errors
              ?? (
                result.error
                  ? [
                      result.error
                    ]
                  : []
              )
          ).map(
            (error) => ({
              message:
                error.message
                ?? String(error),
              stack:
                error.stack
                ?? null
            })
          ),
        artifacts:
          results.flatMap(
            artifactPathsFromResult
          ),
        diagnostics
      };
    }
  );
}

function formatDuration(
  milliseconds
) {
  const seconds =
    milliseconds / 1000;

  return `${
    seconds.toFixed(2)
  }s`;
}

if (
  !existsSync(
    resultsPath
  )
) {
  fail(
    `Playwright JSON report was not found at ${resultsPath}.`
  );
} else {
  try {
    const report =
      readJson(
        resultsPath
      );

    const specs =
      collectSpecs(
        report.suites
      );

    const tests =
      specs.flatMap(
        summarizeSpec
      );

    const totals = {
      total:
        tests.length,
      passed:
        tests.filter(
          (test) =>
            test.status
            === "passed"
        ).length,
      failed:
        tests.filter(
          (test) =>
            test.status
            === "failed"
        ).length,
      skipped:
        tests.filter(
          (test) =>
            test.status
            === "skipped"
        ).length,
      flaky:
        tests.filter(
          (test) =>
            test.status
            === "flaky"
            || test.retries > 0
        ).length,
      retried:
        tests.reduce(
          (
            total,
            test
          ) =>
            total
            + test.retries,
          0
        ),
      duration_ms:
        tests.reduce(
          (
            total,
            test
          ) =>
            total
            + test.duration_ms,
          0
        )
    };

    const projects =
      [...new Set(
        tests.map(
          (test) =>
            test.project
        )
      )].sort();

    const missingProjects =
      REQUIRED_PROJECTS.filter(
        (required) =>
          !projects.includes(
            required
          )
      );

    const diagnostics = {
      warnings:
        tests.reduce(
          (
            total,
            test
          ) =>
            total
            + test.diagnostics.warnings,
          0
        ),
      errors:
        tests.reduce(
          (
            total,
            test
          ) =>
            total
            + test.diagnostics.errors,
          0
        ),
      page_errors:
        tests.reduce(
          (
            total,
            test
          ) =>
            total
            + test.diagnostics.page_errors,
          0
        ),
      expected_warnings:
        tests.reduce(
          (
            total,
            test
          ) =>
            total
            + test.diagnostics.expected_warnings,
          0
        ),
      unexpected_warnings:
        tests.reduce(
          (
            total,
            test
          ) =>
            total
            + test.diagnostics.unexpected_warnings,
          0
        ),
      unexpected_errors:
        tests.reduce(
          (
            total,
            test
          ) =>
            total
            + test.diagnostics.unexpected_errors,
          0
        ),
      release_blocking_tests:
        tests.filter(
          (test) =>
            test.diagnostics.release_blocking
        ).length,
      tests_with_diagnostics:
        tests.filter(
          (test) =>
            test.diagnostics.available
        ).length
    };

    const failedTests =
      tests.filter(
        (test) =>
          test.status
          === "failed"
      );

    const skippedTests =
      tests.filter(
        (test) =>
          test.status
          === "skipped"
      );

    const flakyTests =
      tests.filter(
        (test) =>
          test.status
          === "flaky"
          || test.retries > 0
      );

    const gateChecks = {
      expected_test_count:
        totals.total
        === EXPECTED_TESTS,
      no_failures:
        totals.failed === 0,
      no_skips:
        totals.skipped === 0,
      no_flaky_or_retried:
        totals.flaky === 0
        && totals.retried === 0,
      required_projects_present:
        missingProjects.length
        === 0,
      diagnostics_attached_to_all_tests:
        diagnostics.tests_with_diagnostics
        === totals.total,
      no_release_blocking_browser_diagnostics:
        diagnostics.release_blocking_tests
        === 0
        && diagnostics.unexpected_errors
        === 0
        && diagnostics.page_errors
        === 0
    };

    const gate =
      Object.values(
        gateChecks
      ).every(Boolean)
        ? "PASS"
        : "FAIL";

    const artifacts = {
      html_report:
        "test-evidence/playwright/html/index.html",
      json_report:
        "test-evidence/playwright/results/results.json",
      junit_report:
        "test-evidence/playwright/results/junit.xml",
      release_summary_json:
        "test-evidence/playwright/results/release-summary.json",
      release_summary_markdown:
        "test-evidence/playwright/results/release-summary.md",
      failure_artifacts:
        "test-evidence/playwright/traces"
    };

    const generatedAt =
      new Date().toISOString();

    const evidence = {
      schema_version:
        SCHEMA_VERSION,
      story:
        STORY_ID,
      generated_at:
        generatedAt,
      gate,
      gate_checks:
        gateChecks,
      expected_tests:
        EXPECTED_TESTS,
      totals,
      projects,
      required_projects:
        REQUIRED_PROJECTS,
      missing_projects:
        missingProjects,
      diagnostics,
      git: {
        commit:
          gitValue([
            "rev-parse",
            "HEAD"
          ]),
        short_commit:
          gitValue([
            "rev-parse",
            "--short",
            "HEAD"
          ]),
        branch:
          gitValue([
            "branch",
            "--show-current"
          ]),
        dirty:
          gitValue([
            "status",
            "--porcelain"
          ], "")
            .length > 0
      },
      artifacts,
      failures:
        failedTests,
      skipped:
        skippedTests,
      flaky:
        flakyTests
    };

    mkdirSync(
      dirname(
        summaryJsonPath
      ),
      {
        recursive: true
      }
    );

    writeFileSync(
      summaryJsonPath,
      JSON.stringify(
        evidence,
        null,
        2
      )
      + "\n",
      "utf-8"
    );

    const markdown = [
      `# Browser Release Evidence`,
      ``,
      `**Story:** ${STORY_ID}`,
      ``,
      `**Release gate:** ${gate}`,
      ``,
      `**Generated:** ${generatedAt}`,
      ``,
      `**Commit:** \`${evidence.git.short_commit}\``,
      ``,
      `## Test summary`,
      ``,
      `| Metric | Result |`,
      `|---|---:|`,
      `| Expected | ${EXPECTED_TESTS} |`,
      `| Total | ${totals.total} |`,
      `| Passed | ${totals.passed} |`,
      `| Failed | ${totals.failed} |`,
      `| Skipped | ${totals.skipped} |`,
      `| Flaky | ${totals.flaky} |`,
      `| Retries | ${totals.retried} |`,
      `| Aggregate duration | ${formatDuration(totals.duration_ms)} |`,
      ``,
      `## Project coverage`,
      ``,
      ...REQUIRED_PROJECTS.map(
        (project) =>
          `- ${projects.includes(project) ? "PASS" : "MISSING"} ? \`${project}\``
      ),
      ``,
      `## Browser diagnostics`,
      ``,
      `| Metric | Count |`,
      `|---|---:|`,
      `| Console warnings | ${diagnostics.warnings} |`,
      `| Expected warnings | ${diagnostics.expected_warnings} |`,
      `| Unexpected warnings | ${diagnostics.unexpected_warnings} |`,
      `| Console errors | ${diagnostics.errors} |`,
      `| Unexpected console errors | ${diagnostics.unexpected_errors} |`,
      `| Uncaught page errors | ${diagnostics.page_errors} |`,
      `| Release-blocking tests | ${diagnostics.release_blocking_tests} |`,
      `| Tests with diagnostic attachments | ${diagnostics.tests_with_diagnostics}/${totals.total} |`,
      ``,
      `## Release-gate checks`,
      ``,
      ...Object.entries(
        gateChecks
      ).map(
        ([name, passed]) =>
          `- ${passed ? "PASS" : "FAIL"} ? ${name.replaceAll("_", " ")}`
      ),
      ``,
      `## Evidence artifacts`,
      ``,
      ...Object.entries(
        artifacts
      ).map(
        ([name, path]) =>
          `- **${name.replaceAll("_", " ")}:** \`${path}\``
      ),
      ``,
      `## Failed tests`,
      ``,
      ...(
        failedTests.length > 0
          ? failedTests.map(
              (test) =>
                `- \`${test.project}\` ? ${test.title}`
            )
          : [
              `No failed tests.`
            ]
      ),
      ``,
      `## Flaky or retried tests`,
      ``,
      ...(
        flakyTests.length > 0
          ? flakyTests.map(
              (test) =>
                `- \`${test.project}\` ? ${test.title} (${test.retries} retries)`
            )
          : [
              `No flaky or retried tests.`
            ]
      ),
      ``
    ].join(
      "\n"
    );

    writeFileSync(
      summaryMarkdownPath,
      markdown,
      "utf-8"
    );

    console.log(
      `Browser release gate: ${gate}`
    );

    console.log(
      `Tests: ${totals.passed}/${totals.total} passed`
    );

    console.log(
      `Projects: ${projects.join(", ")}`
    );

    console.log(
      `JSON: ${relative(root, summaryJsonPath)}`
    );

    console.log(
      `Markdown: ${relative(root, summaryMarkdownPath)}`
    );

    if (
      gate !== "PASS"
    ) {
      process.exitCode = 1;
    }
  } catch (error) {
    fail(
      error instanceof Error
        ? error.message
        : String(error)
    );
  }
}
