import assert from "node:assert/strict";
import test from "node:test";

import {
  evaluateRequiredCheckContract,
  requiredCheckMarkdown
} from "./browser-required-check-contract.mjs";

function validWorkflow() {
  return `name: Browser Release Gate

on:
  pull_request:
  push:
    branches:
      - main
  merge_group:
  workflow_dispatch:

permissions:
  contents: read

jobs:
  browser-release:
    name: Governed Browser Evidence
    runs-on: ubuntu-latest
    steps:
      - run: echo pass

  browser-release-required:
    name: Browser Release Required
    if: always()
    needs:
      - browser-release
    runs-on: ubuntu-latest
    steps:
      - name: Enforce browser release result
        env:
          BROWSER_RELEASE_RESULT: \${{ needs.browser-release.result }}
        run: |
          if [[ "\${BROWSER_RELEASE_RESULT}" != "success" ]]; then
            exit 1
          fi
`;
}

test(
  "accepts a valid required-check workflow",
  () => {
    const result =
      evaluateRequiredCheckContract(
        validWorkflow()
      );

    assert.equal(
      result.status,
      "PASS"
    );

    assert.deepEqual(
      result.failed_checks,
      []
    );
  }
);

test(
  "rejects a missing merge-group trigger",
  () => {
    const workflow =
      validWorkflow().replace(
        "  merge_group:\n",
        ""
      );

    const result =
      evaluateRequiredCheckContract(
        workflow
      );

    assert.equal(
      result.status,
      "FAIL"
    );

    assert.ok(
      result.failed_checks.includes(
        "merge_group_trigger"
      )
    );
  }
);

test(
  "rejects a renamed required check",
  () => {
    const workflow =
      validWorkflow().replace(
        "name: Browser Release Required",
        "name: Browser Release Final"
      );

    const result =
      evaluateRequiredCheckContract(
        workflow
      );

    assert.ok(
      result.failed_checks.includes(
        "required_check_name"
      )
    );
  }
);

test(
  "rejects removal of always",
  () => {
    const workflow =
      validWorkflow().replace(
        "    if: always()\n",
        ""
      );

    const result =
      evaluateRequiredCheckContract(
        workflow
      );

    assert.ok(
      result.failed_checks.includes(
        "required_job_always_runs"
      )
    );
  }
);

test(
  "rejects a missing upstream dependency",
  () => {
    const workflow =
      validWorkflow().replace(
        `    needs:
      - browser-release
`,
        ""
      );

    const result =
      evaluateRequiredCheckContract(
        workflow
      );

    assert.ok(
      result.failed_checks.includes(
        "required_job_needs_upstream"
      )
    );
  }
);

test(
  "rejects a required job that does not fail",
  () => {
    const workflow =
      validWorkflow().replace(
        "            exit 1",
        "            echo ignored"
      );

    const result =
      evaluateRequiredCheckContract(
        workflow
      );

    assert.ok(
      result.failed_checks.includes(
        "failure_exit_present"
      )
    );
  }
);

test(
  "creates contract Markdown",
  () => {
    const markdown =
      requiredCheckMarkdown(
        evaluateRequiredCheckContract(
          validWorkflow()
        )
      );

    assert.match(
      markdown,
      /# Browser Required-Check Contract/
    );

    assert.match(
      markdown,
      /\*\*Status:\*\* PASS/
    );
  }
);
