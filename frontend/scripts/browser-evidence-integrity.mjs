import {
  createHash
} from "node:crypto";

import {
  existsSync,
  readFileSync,
  readdirSync,
  statSync,
  writeFileSync
} from "node:fs";

import {
  extname,
  relative,
  resolve
} from "node:path";

export const MANIFEST_SCHEMA =
  "gagf.browser-evidence-manifest.v1";

const MEDIA_TYPES = new Map([
  [
    ".html",
    "text/html"
  ],
  [
    ".json",
    "application/json"
  ],
  [
    ".xml",
    "application/xml"
  ],
  [
    ".md",
    "text/markdown"
  ],
  [
    ".zip",
    "application/zip"
  ],
  [
    ".png",
    "image/png"
  ],
  [
    ".webm",
    "video/webm"
  ],
  [
    ".txt",
    "text/plain"
  ]
]);

export function normalizePath(
  value
) {
  return String(value).replaceAll(
    "\\",
    "/"
  );
}

export function sha256File(
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

export function mediaTypeFor(
  filePath
) {
  return (
    MEDIA_TYPES.get(
      extname(
        filePath
      ).toLowerCase()
    )
    ?? "application/octet-stream"
  );
}

export function listFilesRecursive(
  directory
) {
  if (
    !existsSync(
      directory
    )
  ) {
    return [];
  }

  const output = [];

  for (
    const entry
    of readdirSync(
      directory,
      {
        withFileTypes: true
      }
    )
  ) {
    const entryPath =
      resolve(
        directory,
        entry.name
      );

    if (
      entry.isDirectory()
    ) {
      output.push(
        ...listFilesRecursive(
          entryPath
        )
      );

      continue;
    }

    if (
      entry.isFile()
    ) {
      output.push(
        entryPath
      );
    }
  }

  return output.sort(
    (
      left,
      right
    ) =>
      normalizePath(
        left
      ).localeCompare(
        normalizePath(
          right
        )
      )
  );
}

export function artifactRecord(
  filePath,
  root
) {
  const stats =
    statSync(
      filePath
    );

  return {
    path:
      normalizePath(
        relative(
          root,
          filePath
        )
      ),
    size_bytes:
      stats.size,
    media_type:
      mediaTypeFor(
        filePath
      ),
    sha256:
      sha256File(
        filePath
      )
  };
}

export function canonicalizeManifest(
  manifest
) {
  return {
    ...manifest,
    artifacts:
      [
        ...manifest.artifacts
      ].sort(
        (
          left,
          right
        ) =>
          left.path.localeCompare(
            right.path
          )
      )
  };
}

export function writeCanonicalManifest(
  manifest,
  destination
) {
  const canonical =
    canonicalizeManifest(
      manifest
    );

  writeFileSync(
    destination,
    JSON.stringify(
      canonical,
      null,
      2
    )
    + "\n",
    "utf-8"
  );

  return canonical;
}

export function verifyManifest(
  manifest,
  root,
  options = {}
) {
  const {
    allowedUnexpectedFiles = [],
    ignoredUnexpectedPrefixes = [],
    evidenceDirectory = null
  } = options;

  const missing = [];
  const modified = [];
  const valid = [];

  const artifacts =
    Array.isArray(
      manifest.artifacts
    )
      ? manifest.artifacts
      : [];

  const expectedPaths =
    new Set(
      artifacts.map(
        (artifact) =>
          normalizePath(
            artifact.path
          )
      )
    );

  for (
    const artifact
    of artifacts
  ) {
    const artifactPath =
      normalizePath(
        artifact.path
      );

    const filePath =
      resolve(
        root,
        artifactPath
      );

    if (
      !existsSync(
        filePath
      )
    ) {
      missing.push(
        artifactPath
      );

      continue;
    }

    const actualSize =
      statSync(
        filePath
      ).size;

    const actualHash =
      sha256File(
        filePath
      );

    if (
      actualSize
        !== artifact.size_bytes
      || actualHash
        !== artifact.sha256
    ) {
      modified.push({
        path:
          artifactPath,
        expected_size_bytes:
          artifact.size_bytes,
        actual_size_bytes:
          actualSize,
        expected_sha256:
          artifact.sha256,
        actual_sha256:
          actualHash
      });

      continue;
    }

    valid.push(
      artifactPath
    );
  }

  const unexpected = [];

  if (
    evidenceDirectory
    && existsSync(
      evidenceDirectory
    )
  ) {
    const manifestPath =
      normalizePath(
        relative(
          root,
          resolve(
            evidenceDirectory,
            "results",
            "evidence-manifest.json"
          )
        )
      );

    const allowed =
      new Set([
        manifestPath,
        ...allowedUnexpectedFiles.map(
          normalizePath
        )
      ]);

    const ignoredPrefixes =
      ignoredUnexpectedPrefixes
        .map(
          normalizePath
        )
        .map(
          (prefix) =>
            prefix.endsWith("/")
              ? prefix
              : `${prefix}/`
        );

    for (
      const filePath
      of listFilesRecursive(
        evidenceDirectory
      )
    ) {
      const relativePath =
        normalizePath(
          relative(
            root,
            filePath
          )
        );

      const ignoredByPrefix =
        ignoredPrefixes.some(
          (prefix) =>
            relativePath.startsWith(
              prefix
            )
        );

      if (
        expectedPaths.has(
          relativePath
        )
        || allowed.has(
          relativePath
        )
        || ignoredByPrefix
      ) {
        continue;
      }

      unexpected.push(
        relativePath
      );
    }
  }

  unexpected.sort();

  return {
    valid:
      missing.length === 0
      && modified.length === 0
      && unexpected.length === 0,
    checked:
      artifacts.length,
    valid_artifacts:
      valid.length,
    missing,
    modified,
    unexpected
  };
}
