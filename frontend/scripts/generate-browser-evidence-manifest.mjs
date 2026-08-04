import {
  existsSync,
  mkdirSync,
  readFileSync
} from "node:fs";

import {
  execFileSync
} from "node:child_process";

import {
  dirname,
  resolve
} from "node:path";

import {
  MANIFEST_SCHEMA,
  artifactRecord,
  listFilesRecursive,
  normalizePath,
  writeCanonicalManifest
} from "./browser-evidence-integrity.mjs";

const root =
  process.cwd();

const evidenceRoot =
  resolve(
    root,
    "test-evidence",
    "playwright"
  );

const resultsDirectory =
  resolve(
    evidenceRoot,
    "results"
  );

const summaryPath =
  resolve(
    resultsDirectory,
    "release-summary.json"
  );

const manifestPath =
  resolve(
    resultsDirectory,
    "evidence-manifest.json"
  );

const includedRoots = [
  resolve(
    evidenceRoot,
    "html"
  ),
  resolve(
    evidenceRoot,
    "results"
  ),
  resolve(
    evidenceRoot,
    "traces"
  )
];

const excludedNames =
  new Set([
    "evidence-manifest.json"
  ]);

function gitValue(
  args,
  fallback = "unknown"
) {
  try {
    return execFileSync(
      "git",
      args,
      {
        cwd:
          resolve(
            root,
            ".."
          ),
        encoding:
          "utf-8",
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

if (
  !existsSync(
    summaryPath
  )
) {
  throw new Error(
    "Release summary is missing. "
    + "Run npm run test:e2e:summary first."
  );
}

const summary =
  JSON.parse(
    readFileSync(
      summaryPath,
      "utf-8"
    )
  );

const artifactFiles =
  includedRoots
    .flatMap(
      listFilesRecursive
    )
    .filter(
      (filePath) =>
        !excludedNames.has(
          filePath
            .split(/[\\/]/)
            .at(-1)
        )
    );

const artifacts =
  artifactFiles.map(
    (filePath) =>
      artifactRecord(
        filePath,
        root
      )
  );

const aggregateBytes =
  artifacts.reduce(
    (
      total,
      artifact
    ) =>
      total
      + artifact.size_bytes,
    0
  );

const manifest = {
  schema_version:
    MANIFEST_SCHEMA,
  story:
    summary.story
    ?? "GRA-UI-010J",
  generated_at:
    new Date().toISOString(),
  release_gate:
    summary.gate
    ?? "UNKNOWN",
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
  evidence_root:
    normalizePath(
      "test-evidence/playwright"
    ),
  artifact_count:
    artifacts.length,
  aggregate_size_bytes:
    aggregateBytes,
  artifacts
};

mkdirSync(
  dirname(
    manifestPath
  ),
  {
    recursive: true
  }
);

const canonical =
  writeCanonicalManifest(
    manifest,
    manifestPath
  );

console.log(
  `Evidence manifest generated: ${canonical.artifact_count} artifacts`
);

console.log(
  `Aggregate size: ${canonical.aggregate_size_bytes} bytes`
);

console.log(
  "Manifest: "
  + "test-evidence/playwright/results/evidence-manifest.json"
);
