import {
  expect,
  test as base,
  type ConsoleMessage
} from "@playwright/test";

import {
  evaluateDiagnosticPolicy,
  partitionExpectedHttpDiagnostics,
  redactSensitiveText,
  sanitizeDiagnostic
} from "./browser-diagnostic-policy";

type DiagnosticLocation = {
  url?: string;
  lineNumber?: number;
  columnNumber?: number;
};

type PolicyDiagnostic = {
  event_index?: number;
  source:
    | "console"
    | "pageerror";
  level:
    | "warning"
    | "error";
  message: string;
  location?: DiagnosticLocation;
  stack?: string;
};

type DiagnosticPolicyResult = {
  expected_warnings: number;
  unexpected_warnings: number;
  unexpected_errors: number;
  page_errors: number;
  release_blocking: boolean;
  expected_warning_events:
    PolicyDiagnostic[];
  unexpected_warning_events:
    PolicyDiagnostic[];
  unexpected_error_events:
    PolicyDiagnostic[];
  page_error_events:
    PolicyDiagnostic[];
};
type BrowserDiagnosticFixture = {
  browserDiagnostics:
    PolicyDiagnostic[];
};

function consoleLocation(
  message: ConsoleMessage
): PolicyDiagnostic["location"] {
  const location =
    message.location();

  if (
    !location.url
    && location.lineNumber === 0
    && location.columnNumber === 0
  ) {
    return undefined;
  }

  return {
    url:
      location.url || undefined,
    lineNumber:
      location.lineNumber,
    columnNumber:
      location.columnNumber
  };
}

function policyFailureMessage(
  policy:
    DiagnosticPolicyResult
): string {
  const messages = [
    "Unexpected browser runtime diagnostics were captured.",
    `Console errors: ${policy.unexpected_errors}.`,
    `Page errors: ${policy.page_errors}.`
  ];

  const firstError =
    policy.unexpected_error_events[0]
    ?? policy.page_error_events[0];

  if (
    firstError
  ) {
    messages.push(
      `First error: ${
        redactSensitiveText(
          firstError.message
        )
      }`
    );
  }

  return messages.join(
    " "
  );
}

export const test =
  base.extend<
    BrowserDiagnosticFixture
  >({
    browserDiagnostics: [
      async (
        {
          page
        },
        use,
        testInfo
      ) => {
        const rawDiagnostics:
          PolicyDiagnostic[] = [];

        const onConsole = (
          message: ConsoleMessage
        ): void => {
          const type =
            message.type();

          if (
            type !== "warning"
            && type !== "error"
          ) {
            return;
          }

          rawDiagnostics.push({
            source:
              "console",
            level:
              type === "warning"
                ? "warning"
                : "error",
            message:
              message.text(),
            location:
              consoleLocation(
                message
              )
          });
        };

        const onPageError = (
          error: Error
        ): void => {
          rawDiagnostics.push({
            source:
              "pageerror",
            level:
              "error",
            message:
              error.message,
            stack:
              error.stack
          });
        };

        page.on(
          "console",
          onConsole
        );

        page.on(
          "pageerror",
          onPageError
        );

        await use(
          rawDiagnostics
        );

        page.off(
          "console",
          onConsole
        );

        page.off(
          "pageerror",
          onPageError
        );

        const diagnostics =
          rawDiagnostics.map(
            (
              diagnostic,
              index
            ) =>
              sanitizeDiagnostic(
                diagnostic,
                index + 1
              )
          );

        const {
          enforced_diagnostics:
            enforcedDiagnostics,
          expected_http_error_events:
            expectedHttpErrorEvents
        } =
          partitionExpectedHttpDiagnostics(
            diagnostics,
            testInfo.title
          );

        const policy =
          evaluateDiagnosticPolicy(
            enforcedDiagnostics
          );

        const summary = {
          schema_version:
            "gagf.browser-diagnostics.v2",
          story:
            process.env.GAGF_STORY_ID
            ?? "GRA-UI-010L",
          test_id:
            testInfo.testId,
          title:
            redactSensitiveText(
              testInfo.title
            ),
          project:
            testInfo.project.name,
          status:
            testInfo.status,
          expected_status:
            testInfo.expectedStatus,
          retry:
            testInfo.retry,
          counts: {
            warnings:
              diagnostics.filter(
                (item) =>
                  item.level
                  === "warning"
              ).length,
            errors:
              diagnostics.filter(
                (item) =>
                  item.level
                  === "error"
              ).length,
            page_errors:
              diagnostics.filter(
                (item) =>
                  item.source
                  === "pageerror"
              ).length,
            expected_warnings:
              policy.expected_warnings,
            expected_http_errors:
              expectedHttpErrorEvents.length,
            unexpected_warnings:
              policy.unexpected_warnings,
            unexpected_errors:
              policy.unexpected_errors
          },
          policy: {
            release_blocking:
              policy.release_blocking,
            expected_warnings:
              policy.expected_warnings,
            expected_http_errors:
              expectedHttpErrorEvents.length,
            unexpected_warnings:
              policy.unexpected_warnings,
            unexpected_errors:
              policy.unexpected_errors,
            page_errors:
              policy.page_errors
          },
          diagnostics
        };

        await testInfo.attach(
          "browser-diagnostics",
          {
            body:
              Buffer.from(
                JSON.stringify(
                  summary,
                  null,
                  2
                ),
                "utf-8"
              ),
            contentType:
              "application/json"
          }
        );

        const testOtherwisePassed =
          testInfo.status
          === testInfo.expectedStatus;

        if (
          testOtherwisePassed
          && policy.release_blocking
        ) {
          throw new Error(
            policyFailureMessage(
              policy
            )
          );
        }
      },
      {
        auto: true
      }
    ]
  });

export {
  expect
};

export type {
  Page,
  Request,
  Route
} from "@playwright/test";
