import {
  afterEach,
  describe,
  expect,
  it
} from "vitest";

import {
  expectNoAccessibilityViolations,
  formatAccessibilityViolations,
  runAccessibilityAudit
} from "./accessibility-harness";

function createContainer(
  markup: string
): HTMLElement {
  const container =
    document.createElement("div");

  container.innerHTML = markup;

  document.body.appendChild(container);

  return container;
}

describe(
  "accessibility harness",
  () => {
    afterEach(() => {
      document.body.innerHTML = "";
    });

    it(
      "passes accessible semantic markup",
      async () => {
        const container =
          createContainer(`
            <main>
              <h1>Governance Console</h1>
              <button type="button">
                Create checkpoint
              </button>
            </main>
          `);

        await expectNoAccessibilityViolations(
          container
        );
      }
    );

    it(
      "detects an unlabeled form input",
      async () => {
        const container =
          createContainer(`
            <main>
              <h1>Governance Console</h1>
              <input type="text" />
            </main>
          `);

        const results =
          await runAccessibilityAudit(
            container
          );

        expect(
          results.violations.some(
            (violation) =>
              violation.id === "label"
          )
        ).toBe(true);
      }
    );

    it(
      "formats violations for readable test output",
      async () => {
        const container =
          createContainer(`
            <main>
              <h1>Governance Console</h1>
              <button></button>
            </main>
          `);

        const results =
          await runAccessibilityAudit(
            container
          );

        const formatted =
          formatAccessibilityViolations(
            results
          );

        expect(formatted).toContain(
          "button-name"
        );

        expect(formatted).toContain(
          "Target:"
        );
      }
    );
  }
);
