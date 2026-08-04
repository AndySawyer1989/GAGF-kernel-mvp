import {
  existsSync,
  readdirSync,
  statSync,
  unlinkSync
} from "node:fs";

import {
  basename,
  extname,
  resolve
} from "node:path";

export const DEFAULT_RETENTION_DAYS =
  30;

export const BUNDLE_FILENAME_PATTERN =
  /^gagf-browser-evidence-[A-Za-z0-9._-]+-[a-f0-9]+\.zip$/;

export function retentionCutoff(
  now,
  retentionDays
) {
  const millisecondsPerDay =
    24 * 60 * 60 * 1000;

  return new Date(
    now.getTime()
    - retentionDays
      * millisecondsPerDay
  );
}

export function isEvidenceBundle(
  filePath
) {
  return (
    extname(filePath).toLowerCase()
      === ".zip"
    && BUNDLE_FILENAME_PATTERN.test(
      basename(filePath)
    )
  );
}

export function findExpiredBundles(
  directory,
  options = {}
) {
  const {
    now =
      new Date(),
    retentionDays =
      DEFAULT_RETENTION_DAYS
  } = options;

  if (
    !existsSync(directory)
  ) {
    return [];
  }

  const cutoff =
    retentionCutoff(
      now,
      retentionDays
    );

  return readdirSync(
    directory,
    {
      withFileTypes: true
    }
  )
    .filter(
      (entry) =>
        entry.isFile()
    )
    .map(
      (entry) =>
        resolve(
          directory,
          entry.name
        )
    )
    .filter(
      isEvidenceBundle
    )
    .filter(
      (filePath) =>
        statSync(filePath).mtime
          < cutoff
    )
    .sort();
}

export function deleteExpiredBundles(
  directory,
  options = {}
) {
  const expired =
    findExpiredBundles(
      directory,
      options
    );

  for (
    const filePath
    of expired
  ) {
    unlinkSync(filePath);
  }

  return expired;
}
