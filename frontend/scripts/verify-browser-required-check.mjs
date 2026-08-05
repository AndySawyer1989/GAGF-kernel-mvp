import {
  mkdirSync,
  writeFileSync
} from "node:fs";

import {
  dirname,
  resolve
} from "node:path";

import {
  evaluateRequiredCheckContract,
  loadWorkflow,
  requiredCheckMarkdown
} from "./browser-required-check-contract.mjs";

const frontendRoot =
  process.cwd();

const repositoryRoot =
  resolve(
    frontendRoot,
    ".."
  );

const workflowPath =
  resolve(
    repositoryRoot,
    ".github",
    "workflows",
    "browser-release-gate.yml"
  );

const resultDirectory =
  resolve(
    frontendRoot,
    "test-evidence",
    "playwright",
    "results"
  );

const jsonPath =
  resolve(
    resultDirectory,
    "required-check-contract.json"
  );

const markdownPath =
  resolve(
    resultDirectory,
    "required-check-contract.md"
  );

const workflow =
  loadWorkflow(
    workflowPath
  );

const result =
  evaluateRequiredCheckContract(
    workflow
  );

mkdirSync(
  dirname(
    jsonPath
  ),
  {
    recursive: true
  }
);

writeFileSync(
  jsonPath,
  JSON.stringify(
    result,
    null,
    2
  )
  + "\n",
  "utf-8"
);

writeFileSync(
  markdownPath,
  requiredCheckMarkdown(
    result
  ),
  "utf-8"
);

if (
  result.status === "PASS"
) {
  console.log(
    "::notice title=Browser Required Check::Required-check contract passed."
  );
} else {
  console.log(
    "::error title=Browser Required Check::Required-check contract failed: "
    + result.failed_checks.join(
        ", "
      )
  );
}

console.log(
  `Required-check contract: ${result.status}`
);

console.log(
  "Contract JSON: "
  + "test-evidence/playwright/results/required-check-contract.json"
);

console.log(
  "Contract Markdown: "
  + "test-evidence/playwright/results/required-check-contract.md"
);

if (
  result.status !== "PASS"
) {
  process.exitCode = 1;
}
