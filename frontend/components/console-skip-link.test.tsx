import {
  render,
  screen
} from "@testing-library/react";

import {
  describe,
  expect,
  it
} from "vitest";

import {
  ConsoleSkipLink
} from "./console-skip-link";

import {
  expectNoAccessibilityViolations
} from "@/test/accessibility-harness";

describe(
  "ConsoleSkipLink",
  () => {
    it(
      "links to the focusable main-content target",
      () => {
        render(
          <>
            <ConsoleSkipLink />

            <main
              id="console-main-content"
              tabIndex={-1}
            >
              Main content
            </main>
          </>
        );

        expect(
          screen.getByRole(
            "link",
            {
              name:
                "Skip to main content"
            }
          )
        ).toHaveAttribute(
          "href",
          "#console-main-content"
        );
      }
    );

    it(
      "has no automated accessibility violations",
      async () => {
        const {
          container
        } = render(
          <>
            <ConsoleSkipLink />

            <main
              id="console-main-content"
              tabIndex={-1}
            >
              Main content
            </main>
          </>
        );

        await expectNoAccessibilityViolations(
          container
        );
      }
    );
  }
);
