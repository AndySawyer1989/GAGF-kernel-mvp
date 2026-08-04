import {
  createHash
} from "node:crypto";

import {
  existsSync,
  mkdirSync,
  readFileSync,
  rmSync,
  writeFileSync
} from "node:fs";

import {
  execFileSync
} from "node:child_process";

import {
  basename,
  relative,
  resolve
} from "node:path";

import {
  verifyManifest
} from "./browser-evidence-integrity.mjs";

import {
  DEFAULT_RETENTION_DAYS,
  deleteExpiredBundles
} from "./browser-evidence-retention.mjs";

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

const bundleDirectory =
  resolve(
    evidenceRoot,
    "bundles"
  );

const manifestPath =
  resolve(
    resultsDirectory,
    "evidence-manifest.json"
  );

function sha256File(
  filePath
) {
  const hash =
    createHash(
      "sha256"
    );

  hash.update(
    readFileSync(
      filePath
    )
  );

  return hash.digest(
    "hex"
  );
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
    manifestPath
  )
) {
  throw new Error(
    "Evidence manifest is missing. "
    + "Run npm run test:e2e:manifest first."
  );
}

const manifest =
  JSON.parse(
    readFileSync(
      manifestPath,
      "utf-8"
    )
  );

const verification =
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
      ]
    }
  );

if (
  !verification.valid
) {
  throw new Error(
    "Evidence manifest verification failed. "
    + "Run npm run test:e2e:verify for details."
  );
}

mkdirSync(
  bundleDirectory,
  {
    recursive: true
  }
);

const story =
  String(
    manifest.story
    ?? "GRA-UI-010K"
  ).replace(
    /[^A-Za-z0-9._-]/g,
    "-"
  );

const shortCommit =
  gitValue([
    "rev-parse",
    "--short",
    "HEAD"
  ])
    .replace(
      /[^a-f0-9]/gi,
      ""
    )
  || "unknown";

const bundleName =
  `gagf-browser-evidence-${story}-${shortCommit}.zip`;

const bundlePath =
  resolve(
    bundleDirectory,
    bundleName
  );

const digestPath =
  `${bundlePath}.sha256.json`;

const archiveItems = [
  "html",
  "results",
  "traces"
].filter(
  (item) =>
    existsSync(
      resolve(
        evidenceRoot,
        item
      )
    )
);

if (
  archiveItems.length === 0
) {
  throw new Error(
    "No evidence directories were available for packaging."
  );
}

if (
  existsSync(
    bundlePath
  )
) {
  rmSync(
    bundlePath,
    {
      force: true
    }
  );
}

if (
  process.platform
  === "win32"
) {
  const powershellCommand = [
    "$ErrorActionPreference = 'Stop'",
    `$source = '${evidenceRoot.replaceAll("'", "''")}'`,
    `$destination = '${bundlePath.replaceAll("'", "''")}'`,
    "$items = @(",
    ...archiveItems.map(
      (item) =>
        `  (Join-Path $source '${item}')`
    ),
    ")",
    "Compress-Archive "
      + "-Path $items "
      + "-DestinationPath $destination "
      + "-CompressionLevel Optimal"
  ].join(
    "\n"
  );

  execFileSync(
    "powershell.exe",
    [
      "-NoProfile",
      "-NonInteractive",
      "-Command",
      powershellCommand
    ],
    {
      cwd:
        root,
      stdio:
        "inherit"
    }
  );
} else {
  execFileSync(
    "zip",
    [
      "-q",
      "-r",
      bundlePath,
      ...archiveItems
    ],
    {
      cwd:
        evidenceRoot,
      stdio:
        "inherit"
    }
  );
}

if (
  !existsSync(
    bundlePath
  )
) {
  throw new Error(
    "Evidence bundle was not created."
  );
}

const retentionDays =
  Number.parseInt(
    process.env.GAGF_EVIDENCE_RETENTION_DAYS
    ?? String(
      DEFAULT_RETENTION_DAYS
    ),
    10
  );

const digestRecord = {
  schema_version:
    "gagf.browser-evidence-bundle.v1",
  story:
    manifest.story,
  release_gate:
    manifest.release_gate,
  created_at:
    new Date().toISOString(),
  retention_days:
    retentionDays,
  bundle:
    basename(
      bundlePath
    ),
  sha256:
    sha256File(
      bundlePath
    ),
  git: {
    commit:
      gitValue([
        "rev-parse",
        "HEAD"
      ]),
    short_commit:
      shortCommit,
    branch:
      gitValue([
        "branch",
        "--show-current"
      ])
  },
  source_manifest:
    "test-evidence/playwright/results/evidence-manifest.json",
  artifact_count:
    manifest.artifact_count,
  aggregate_size_bytes:
    manifest.aggregate_size_bytes
};

writeFileSync(
  digestPath,
  JSON.stringify(
    digestRecord,
    null,
    2
  )
  + "\n",
  "utf-8"
);

const removedBundles =
  deleteExpiredBundles(
    bundleDirectory,
    {
      retentionDays
    }
  );

console.log(
  "Bundle source directories: "
  + archiveItems.join(
      ", "
    )
);

console.log(
  "Bundle relative path: "
  + relative(
      root,
      bundlePath
    ).replaceAll(
      "\\",
      "/"
    )
);

console.log(
  `Evidence bundle: ${basename(bundlePath)}`
);

console.log(
  `Bundle SHA-256: ${digestRecord.sha256}`
);

console.log(
  `Retention: ${retentionDays} days`
);

console.log(
  `Expired bundles removed: ${removedBundles.length}`
);
