import {
  createHash
} from "node:crypto";

import {
  existsSync,
  readFileSync
} from "node:fs";

import {
  resolve
} from "node:path";

const root =
  process.cwd();

const bundleDirectory =
  resolve(
    root,
    "test-evidence",
    "playwright",
    "bundles"
  );

const digestFiles =
  existsSync(bundleDirectory)
    ? (
        await import("node:fs")
      ).readdirSync(bundleDirectory)
        .filter(
          (name) =>
            name.endsWith(
              ".zip.sha256.json"
            )
        )
        .sort()
    : [];

if (
  digestFiles.length === 0
) {
  console.error(
    "No browser evidence bundle digest record was found."
  );

  process.exit(1);
}

const digestFile =
  digestFiles.at(-1);

const digestPath =
  resolve(
    bundleDirectory,
    digestFile
  );

const record =
  JSON.parse(
    readFileSync(
      digestPath,
      "utf-8"
    )
  );

const bundlePath =
  resolve(
    bundleDirectory,
    record.bundle
  );

if (
  !existsSync(bundlePath)
) {
  console.error(
    `Evidence bundle is missing: ${record.bundle}`
  );

  process.exit(1);
}

const hash =
  createHash("sha256");

hash.update(
  readFileSync(bundlePath)
);

const actualHash =
  hash.digest("hex");

if (
  actualHash
  !== record.sha256
) {
  console.error(
    "Browser evidence bundle integrity: FAIL"
  );

  console.error(
    `Expected: ${record.sha256}`
  );

  console.error(
    `Actual:   ${actualHash}`
  );

  process.exit(1);
}

console.log(
  `Bundle verified: ${record.bundle}`
);

console.log(
  `SHA-256: ${actualHash}`
);

console.log(
  "Browser evidence bundle integrity: PASS"
);
