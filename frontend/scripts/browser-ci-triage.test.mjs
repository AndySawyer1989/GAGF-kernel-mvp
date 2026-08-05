import assert from "node:assert/strict";
import test from "node:test";

import {
  annotationCommand,
  classifyReleaseSummary,
  escapeWorkflowCommand,
  triageMarkdown,
  triageMessage
} from "./browser-ci-triage.mjs";

function passingSummary() {
  return {
    story:
      "GRA-UI-010L",
    gate:
      "PASS",
    totals: {
      total: 58,
      passed: 58,
      failed: 0,
      skipped: 0,
      flaky: 0,
      retried: 0
    },
    diagnostics: {
      unexpected_warnings: 0,
      unexpected_errors: 0,
      page_errors: 0,
      release_blocking_tests: 0
    },
    gate_checks: {
      expected_test_count: true,
      no_failures: true,
      no_skips: true
    },
    failures: []
  };
}

test(
  "classifies a clean release as PASS",
  () => {
    const triage =
      classifyReleaseSummary(
        passingSummary()
      );

    assert.equal(
      triage.status,
      "PASS"
    );

    assert.equal(
      triage.level,
      "notice"
    );
  }
);

test(
  "classifies unexpected warnings as WARN",
  () => {
    const summary =
      passingSummary();

    summary.diagnostics
      .unexpected_warnings = 2;

    const triage =
      classifyReleaseSummary(
        summary
      );

    assert.equal(
      triage.status,
      "WARN"
    );

    assert.equal(
      triage.level,
      "warning"
    );
  }
);

test(
  "classifies failed tests as FAIL",
  () => {
    const summary =
      passingSummary();

    summary.gate =
      "FAIL";

    summary.totals.passed =
      57;

    summary.totals.failed =
      1;

    summary.failures = [
      {
        project:
          "desktop-chromium",
        title:
          "creates a signed checkpoint",
        file:
          "signed-checkpoint-workflow.spec.ts",
        line:
          111
      }
    ];

    const triage =
      classifyReleaseSummary(
        summary
      );

    assert.equal(
      triage.status,
      "FAIL"
    );

    assert.equal(
      triage.failures.length,
      1
    );
  }
);

test(
  "classifies a failed gate check as FAIL",
  () => {
    const summary =
      passingSummary();

    summary.gate_checks
      .no_flaky_or_retried = false;

    const triage =
      classifyReleaseSummary(
        summary
      );

    assert.equal(
      triage.status,
      "FAIL"
    );

    assert.deepEqual(
      triage.failed_checks,
      [
        "no_flaky_or_retried"
      ]
    );
  }
);

test(
  "escapes GitHub workflow-command characters",
  () => {
    assert.equal(
      escapeWorkflowCommand(
        "line 1%\nline 2"
      ),
      "line 1%25%0Aline 2"
    );
  }
);

test(
  "creates a GitHub error annotation",
  () => {
    const output =
      annotationCommand(
        "error",
        "Browser gate",
        "One test failed"
      );

    assert.equal(
      output,
      "::error title=Browser gate::One test failed"
    );
  }
);

test(
  "creates a concise triage message",
  () => {
    const output =
      triageMessage(
        classifyReleaseSummary(
          passingSummary()
        )
      );

    assert.match(
      output,
      /58\/58 passed/
    );

    assert.match(
      output,
      /0 failed/
    );
  }
);

test(
  "creates Markdown triage evidence",
  () => {
    const output =
      triageMarkdown(
        classifyReleaseSummary(
          passingSummary()
        )
      );

    assert.match(
      output,
      /# Browser CI Triage/
    );

    assert.match(
      output,
      /\*\*Status:\*\* PASS/
    );
  }
);
