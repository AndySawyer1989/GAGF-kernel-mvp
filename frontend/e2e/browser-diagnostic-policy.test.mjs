import assert from "node:assert/strict";
import test from "node:test";

import {
  evaluateDiagnosticPolicy,
  redactSensitiveText,
  sanitizeDiagnostic
} from "./browser-diagnostic-policy.mjs";

test(
  "redacts authorization credentials and tokens",
  () => {
    const input = [
      "Authorization: Bearer abc.def.ghi",
      "api_key=super-secret-value",
      "refresh_token: refresh-secret",
      "Cookie=session=private-cookie"
    ].join(" ");

    const result =
      redactSensitiveText(input);

    assert.doesNotMatch(
      result,
      /super-secret-value/
    );

    assert.doesNotMatch(
      result,
      /refresh-secret/
    );

    assert.doesNotMatch(
      result,
      /private-cookie/
    );

    assert.match(
      result,
      /\[REDACTED\]/
    );
  }
);

test(
  "redacts sensitive URL query parameters",
  () => {
    const result =
      redactSensitiveText(
        "https://example.test/path"
        + "?tenant_id=tenant-alpha"
        + "&access_token=secret-token"
        + "&signature=private-signature"
      );

    assert.match(
      result,
      /tenant_id=tenant-alpha/
    );

    assert.doesNotMatch(
      result,
      /secret-token/
    );

    assert.doesNotMatch(
      result,
      /private-signature/
    );
  }
);

test(
  "normalizes timestamps and local Windows paths",
  () => {
    const result =
      redactSensitiveText(
        "2026-08-04T18:45:31.123Z "
        + "C:\\Users\\Andy Sawyer\\Desktop\\secret.txt"
      );

    assert.match(
      result,
      /\[TIMESTAMP\]/
    );

    assert.match(
      result,
      /\[LOCAL_PATH\]/
    );

    assert.doesNotMatch(
      result,
      /Andy Sawyer/
    );
  }
);

test(
  "sanitizes diagnostic message location and stack",
  () => {
    const result =
      sanitizeDiagnostic(
        {
          source:
            "pageerror",
          level:
            "error",
          message:
            "token=secret-value",
          location: {
            url:
              "http://localhost/test"
              + "?api_key=private-key",
            lineNumber:
              10,
            columnNumber:
              4
          },
          stack:
            "Error at "
            + "C:\\Users\\Andy\\app.ts:10:4"
        },
        1
      );

    assert.equal(
      result.event_index,
      1
    );

    assert.doesNotMatch(
      JSON.stringify(result),
      /secret-value|private-key|Andy/
    );
  }
);

test(
  "allows a known development warning",
  () => {
    const policy =
      evaluateDiagnosticPolicy([
        {
          source:
            "console",
          level:
            "warning",
          message:
            "Download the React DevTools "
            + "for a better development experience."
        }
      ]);

    assert.equal(
      policy.expected_warnings,
      1
    );

    assert.equal(
      policy.release_blocking,
      false
    );
  }
);

test(
  "records an unexpected warning without blocking release",
  () => {
    const policy =
      evaluateDiagnosticPolicy([
        {
          source:
            "console",
          level:
            "warning",
          message:
            "Unexpected governance warning"
        }
      ]);

    assert.equal(
      policy.unexpected_warnings,
      1
    );

    assert.equal(
      policy.release_blocking,
      false
    );
  }
);

test(
  "blocks unexpected console errors",
  () => {
    const policy =
      evaluateDiagnosticPolicy([
        {
          source:
            "console",
          level:
            "error",
          message:
            "Unhandled request failure"
        }
      ]);

    assert.equal(
      policy.unexpected_errors,
      1
    );

    assert.equal(
      policy.release_blocking,
      true
    );
  }
);

test(
  "blocks uncaught page errors",
  () => {
    const policy =
      evaluateDiagnosticPolicy([
        {
          source:
            "pageerror",
          level:
            "error",
          message:
            "Uncaught TypeError"
        }
      ]);

    assert.equal(
      policy.page_errors,
      1
    );

    assert.equal(
      policy.release_blocking,
      true
    );
  }
);
