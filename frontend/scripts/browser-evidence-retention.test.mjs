import assert from "node:assert/strict";
import test from "node:test";

import {
  closeSync,
  existsSync,
  mkdtempSync,
  openSync,
  rmSync,
  utimesSync,
  writeFileSync
} from "node:fs";

import {
  tmpdir
} from "node:os";

import {
  resolve
} from "node:path";

import {
  deleteExpiredBundles,
  findExpiredBundles,
  isEvidenceBundle,
  retentionCutoff
} from "./browser-evidence-retention.mjs";

function temporaryDirectory() {
  return mkdtempSync(
    resolve(
      tmpdir(),
      "gagf-retention-"
    )
  );
}

test(
  "computes the retention cutoff",
  () => {
    const now =
      new Date(
        "2026-08-04T20:00:00.000Z"
      );

    const cutoff =
      retentionCutoff(
        now,
        30
      );

    assert.equal(
      cutoff.toISOString(),
      "2026-07-05T20:00:00.000Z"
    );
  }
);

test(
  "recognizes valid evidence bundle names",
  () => {
    assert.equal(
      isEvidenceBundle(
        "gagf-browser-evidence-GRA-UI-010J-acde123.zip"
      ),
      true
    );

    assert.equal(
      isEvidenceBundle(
        "unrelated.zip"
      ),
      false
    );

    assert.equal(
      isEvidenceBundle(
        "gagf-browser-evidence-GRA-UI-010J-acde123.json"
      ),
      false
    );
  }
);

test(
  "finds only expired browser evidence bundles",
  () => {
    const directory =
      temporaryDirectory();

    try {
      const expired =
        resolve(
          directory,
          "gagf-browser-evidence-GRA-UI-010J-acde111.zip"
        );

      const current =
        resolve(
          directory,
          "gagf-browser-evidence-GRA-UI-010J-acde222.zip"
        );

      const unrelated =
        resolve(
          directory,
          "unrelated.zip"
        );

      for (
        const filePath
        of [
          expired,
          current,
          unrelated
        ]
      ) {
        writeFileSync(
          filePath,
          "bundle",
          "utf-8"
        );
      }

      const expiredDate =
        new Date(
          "2026-06-01T00:00:00.000Z"
        );

      const currentDate =
        new Date(
          "2026-08-01T00:00:00.000Z"
        );

      utimesSync(
        expired,
        expiredDate,
        expiredDate
      );

      utimesSync(
        current,
        currentDate,
        currentDate
      );

      utimesSync(
        unrelated,
        expiredDate,
        expiredDate
      );

      const result =
        findExpiredBundles(
          directory,
          {
            now:
              new Date(
                "2026-08-04T00:00:00.000Z"
              ),
            retentionDays:
              30
          }
        );

      assert.deepEqual(
        result,
        [
          expired
        ]
      );
    } finally {
      rmSync(
        directory,
        {
          recursive: true,
          force: true
        }
      );
    }
  }
);

test(
  "deletes only expired browser evidence bundles",
  () => {
    const directory =
      temporaryDirectory();

    try {
      const expired =
        resolve(
          directory,
          "gagf-browser-evidence-GRA-UI-010J-acde333.zip"
        );

      const current =
        resolve(
          directory,
          "gagf-browser-evidence-GRA-UI-010J-acde444.zip"
        );

      for (
        const filePath
        of [
          expired,
          current
        ]
      ) {
        const descriptor =
          openSync(
            filePath,
            "w"
          );

        closeSync(
          descriptor
        );
      }

      const expiredDate =
        new Date(
          "2026-01-01T00:00:00.000Z"
        );

      const currentDate =
        new Date(
          "2026-08-03T00:00:00.000Z"
        );

      utimesSync(
        expired,
        expiredDate,
        expiredDate
      );

      utimesSync(
        current,
        currentDate,
        currentDate
      );

      const removed =
        deleteExpiredBundles(
          directory,
          {
            now:
              new Date(
                "2026-08-04T00:00:00.000Z"
              ),
            retentionDays:
              30
          }
        );

      assert.deepEqual(
        removed,
        [
          expired
        ]
      );

      assert.equal(
        existsSync(
          expired
        ),
        false
      );

      assert.equal(
        existsSync(
          current
        ),
        true
      );
    } finally {
      rmSync(
        directory,
        {
          recursive: true,
          force: true
        }
      );
    }
  }
);
