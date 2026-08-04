import assert from "node:assert/strict";
import test from "node:test";

import {
  mkdtempSync,
  mkdirSync,
  readFileSync,
  rmSync,
  writeFileSync
} from "node:fs";

import {
  tmpdir
} from "node:os";

import {
  resolve
} from "node:path";

import {
  artifactRecord,
  canonicalizeManifest,
  mediaTypeFor,
  sha256File,
  verifyManifest,
  writeCanonicalManifest
} from "./browser-evidence-integrity.mjs";

function temporaryDirectory() {
  return mkdtempSync(
    resolve(
      tmpdir(),
      "gagf-browser-evidence-"
    )
  );
}

test(
  "generates stable SHA-256 hashes",
  () => {
    const directory =
      temporaryDirectory();

    try {
      const filePath =
        resolve(
          directory,
          "artifact.json"
        );

      writeFileSync(
        filePath,
        '{"gate":"PASS"}\n',
        "utf-8"
      );

      const first =
        sha256File(
          filePath
        );

      const second =
        sha256File(
          filePath
        );

      assert.equal(
        first,
        second
      );

      assert.match(
        first,
        /^[a-f0-9]{64}$/
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
  "assigns media types from artifact extensions",
  () => {
    assert.equal(
      mediaTypeFor(
        "report.json"
      ),
      "application/json"
    );

    assert.equal(
      mediaTypeFor(
        "report.html"
      ),
      "text/html"
    );

    assert.equal(
      mediaTypeFor(
        "trace.zip"
      ),
      "application/zip"
    );

    assert.equal(
      mediaTypeFor(
        "unknown.bin"
      ),
      "application/octet-stream"
    );
  }
);

test(
  "orders manifest artifacts canonically",
  () => {
    const manifest =
      canonicalizeManifest({
        schema_version:
          "test",
        artifacts: [
          {
            path:
              "z.json"
          },
          {
            path:
              "a.json"
          },
          {
            path:
              "m.json"
          }
        ]
      });

    assert.deepEqual(
      manifest.artifacts.map(
        (artifact) =>
          artifact.path
      ),
      [
        "a.json",
        "m.json",
        "z.json"
      ]
    );
  }
);

test(
  "writes deterministic canonical manifests",
  () => {
    const directory =
      temporaryDirectory();

    try {
      const destination =
        resolve(
          directory,
          "manifest.json"
        );

      writeCanonicalManifest(
        {
          schema_version:
            "test",
          artifacts: [
            {
              path:
                "b.json"
            },
            {
              path:
                "a.json"
            }
          ]
        },
        destination
      );

      const output =
        JSON.parse(
          readFileSync(
            destination,
            "utf-8"
          )
        );

      assert.equal(
        output.artifacts[0].path,
        "a.json"
      );

      assert.equal(
        output.artifacts[1].path,
        "b.json"
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
  "verifies unchanged evidence artifacts",
  () => {
    const directory =
      temporaryDirectory();

    try {
      const evidence =
        resolve(
          directory,
          "evidence"
        );

      mkdirSync(
        evidence,
        {
          recursive: true
        }
      );

      const filePath =
        resolve(
          evidence,
          "result.json"
        );

      writeFileSync(
        filePath,
        '{"passed":true}\n',
        "utf-8"
      );

      const manifest = {
        artifacts: [
          artifactRecord(
            filePath,
            directory
          )
        ]
      };

      const result =
        verifyManifest(
          manifest,
          directory
        );

      assert.equal(
        result.valid,
        true
      );

      assert.equal(
        result.valid_artifacts,
        1
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
  "detects modified evidence artifacts",
  () => {
    const directory =
      temporaryDirectory();

    try {
      const filePath =
        resolve(
          directory,
          "result.json"
        );

      writeFileSync(
        filePath,
        '{"passed":true}\n',
        "utf-8"
      );

      const manifest = {
        artifacts: [
          artifactRecord(
            filePath,
            directory
          )
        ]
      };

      writeFileSync(
        filePath,
        '{"passed":false}\n',
        "utf-8"
      );

      const result =
        verifyManifest(
          manifest,
          directory
        );

      assert.equal(
        result.valid,
        false
      );

      assert.equal(
        result.modified.length,
        1
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
  "detects missing evidence artifacts",
  () => {
    const directory =
      temporaryDirectory();

    try {
      const filePath =
        resolve(
          directory,
          "missing.json"
        );

      const result =
        verifyManifest(
          {
            artifacts: [
              {
                path:
                  "missing.json",
                size_bytes:
                  10,
                media_type:
                  "application/json",
                sha256:
                  "0".repeat(64)
              }
            ]
          },
          directory
        );

      assert.equal(
        result.valid,
        false
      );

      assert.deepEqual(
        result.missing,
        [
          "missing.json"
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
  "detects unexpected evidence files",
  () => {
    const directory =
      temporaryDirectory();

    try {
      const evidence =
        resolve(
          directory,
          "evidence"
        );

      mkdirSync(
        evidence,
        {
          recursive: true
        }
      );

      const expected =
        resolve(
          evidence,
          "expected.json"
        );

      const unexpected =
        resolve(
          evidence,
          "unexpected.txt"
        );

      writeFileSync(
        expected,
        '{"ok":true}\n',
        "utf-8"
      );

      writeFileSync(
        unexpected,
        "unexpected\n",
        "utf-8"
      );

      const result =
        verifyManifest(
          {
            artifacts: [
              artifactRecord(
                expected,
                directory
              )
            ]
          },
          directory,
          {
            evidenceDirectory:
              evidence
          }
        );

      assert.equal(
        result.valid,
        false
      );

      assert.deepEqual(
        result.unexpected,
        [
          "evidence/unexpected.txt"
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
  "ignores files under configured generated prefixes",
  () => {
    const directory =
      temporaryDirectory();

    try {
      const evidence =
        resolve(
          directory,
          "evidence"
        );

      const bundles =
        resolve(
          evidence,
          "bundles"
        );

      mkdirSync(
        bundles,
        {
          recursive: true
        }
      );

      const expected =
        resolve(
          evidence,
          "result.json"
        );

      const generatedBundle =
        resolve(
          bundles,
          "gagf-browser-evidence-test-acde123.zip"
        );

      writeFileSync(
        expected,
        '{"ok":true}\n',
        "utf-8"
      );

      writeFileSync(
        generatedBundle,
        "bundle",
        "utf-8"
      );

      const result =
        verifyManifest(
          {
            artifacts: [
              artifactRecord(
                expected,
                directory
              )
            ]
          },
          directory,
          {
            evidenceDirectory:
              evidence,
            ignoredUnexpectedPrefixes: [
              "evidence/bundles"
            ]
          }
        );

      assert.equal(
        result.valid,
        true
      );

      assert.deepEqual(
        result.unexpected,
        []
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

