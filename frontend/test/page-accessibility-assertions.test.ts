import {
  describe,
  expect,
  it
} from "vitest";

import {
  expectDescribedControl,
  expectNavigationLandmark,
  expectSinglePrimaryHeading,
  expectSkipLinkTarget
} from "./page-accessibility-assertions";

function createContainer(
  markup: string
): HTMLElement {
  const container =
    document.createElement("div");

  container.innerHTML = markup;

  return container;
}

describe(
  "page accessibility assertions",
  () => {
    it(
      "accepts one primary heading",
      () => {
        const container =
          createContainer(`
            <h1>Audit Integrity</h1>
            <h2>Chain verification</h2>
          `);

        expectSinglePrimaryHeading(
          container
        );
      }
    );

    it(
      "requires a navigation landmark",
      () => {
        const container =
          createContainer(`
            <nav aria-label="Console">
              <a href="/">Overview</a>
            </nav>
          `);

        expectNavigationLandmark(
          container
        );
      }
    );

    it(
      "validates the skip-link destination",
      () => {
        const container =
          createContainer(`
            <a href="#console-main-content">
              Skip to content
            </a>

            <main
              id="console-main-content"
              tabindex="-1"
            >
              Content
            </main>
          `);

        expectSkipLinkTarget(container);
      }
    );

    it(
      "validates an aria-describedby relationship",
      () => {
        const container =
          createContainer(`
            <button
              aria-describedby="action-help"
              disabled
            >
              Create signed checkpoint
            </button>

            <p id="action-help">
              Signing is unavailable.
            </p>
          `);

        const button =
          container.querySelector(
            "button"
          );

        expect(button).not.toBeNull();

        expectDescribedControl(
          button as HTMLButtonElement,
          container
        );
      }
    );
  }
);
