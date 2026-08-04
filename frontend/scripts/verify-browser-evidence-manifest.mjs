import {
  existsSync,
  readFileSync
} from "node:fs";

import {
  resolve
} from "node:path";

import {
  verifyManifest
} from "./browser-evidence-integrity.mjs";

const root =
  process.cwd();

const evidenceRoot =
  resolve(
    root,
    "test-evidence",
    "playwright"
  );

const manifestPath =
  resolve(
    evidenceRoot,
    "results",
    "evidence-manifest.json"
  );

if (
  !existsSync(
    manifestPath
  )
) {
  console.error(
    "Evidence manifest is missing."
  );

  process.exit(1);
}

const manifest =
  JSON.parse(
    readFileSync(
      manifestPath,
      "utf-8"
    )
  );

const result =
  verifyManifest(
    manifest,
    root,
    {
      evidenceDirectory:
        evidenceRoot,
      allowedUnexpectedFiles: [
        "test-evidence/playwright/results/evidence-manifest.json"
      ],
      ignoredUnexpectedPrefixes: [
        "test-evidence/playwright/bundles"
      ],
      ignoredUnexpectedPrefixes: [
        "test-evidence/playwright/bundles"
      ]
    }
  );

console.log(
  `Artifacts checked: ${result.checked}`
);

console.log(
  `Artifacts valid: ${result.valid_artifacts}`
);

console.log(
  `Missing: ${result.missing.length}`
);

console.log(
  `Modified: ${result.modified.length}`
);

console.log(
  `Unexpected: ${result.unexpected.length}`
);

if (
  result.missing.length > 0
) {
  console.error(
    "Missing artifacts:"
  );

  for (
    const item
    of result.missing
  ) {
    console.error(
      `  - ${item}`
    );
  }
}

if (
  result.modified.length > 0
) {
  console.error(
    "Modified artifacts:"
  );

  for (
    const item
    of result.modified
  ) {
    console.error(
      `  - ${item.path}`
    );
  }
}

if (
  result.unexpected.length > 0
) {
  console.error(
    "Unexpected artifacts:"
  );

  for (
    const item
    of result.unexpected
  ) {
    console.error(
      `  - ${item}`
    );
  }
}

if (
  !result.valid
) {
  console.error(
    "Browser evidence integrity: FAIL"
  );

  process.exit(1);
}

console.log(
  "Browser evidence integrity: PASS"
);
