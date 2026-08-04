import {
  expect,
  test,
  type Page
} from "@playwright/test";

import {
  installAuditIntegrityApiHarness
} from "./governance-api-harness";

async function waitForSearch(
  page: Page,
  expectedSearch: string
): Promise<void> {
  await page.waitForFunction(
    (search) =>
      window.location.search === search,
    expectedSearch
  );
}

test.describe(
  "Governance Console browser history",
  () => {
    test(
      "restores Audit Integrity filters with Back and Forward",
      async ({ page }) => {
        await installAuditIntegrityApiHarness(
          page,
          {
            eventCount: 8,
            checkpointCount: 3
          }
        );

        await page.goto(
          "/audit-integrity"
        );

        const outcome =
          page.getByLabel("Outcome");

        await expect(
          outcome
        ).toHaveValue("ALL");

        await outcome.selectOption(
          "DENIED"
        );

        await waitForSearch(
          page,
          "?outcome=DENIED"
        );

        await expect(
          outcome
        ).toHaveValue("DENIED");

        await outcome.selectOption(
          "ALLOWED"
        );

        await waitForSearch(
          page,
          "?outcome=ALLOWED"
        );

        await page.goBack();

        await waitForSearch(
          page,
          "?outcome=DENIED"
        );

        await expect(
          outcome
        ).toHaveValue("DENIED");

        await page.goForward();

        await waitForSearch(
          page,
          "?outcome=ALLOWED"
        );

        await expect(
          outcome
        ).toHaveValue("ALLOWED");
      }
    );

    test(
      "restores Signed Checkpoints pagination state",
      async ({ page }) => {
        await page.goto(
          "/signed-checkpoints"
          + "?source=history"
        );

        await page.evaluate(() => {
          window.history.pushState(
            window.history.state,
            "",
            "/signed-checkpoints"
            + "?source=history"
            + "&signedPage=2"
          );

          window.dispatchEvent(
            new PopStateEvent(
              "popstate"
            )
          );
        });

        await waitForSearch(
          page,
          "?source=history"
          + "&signedPage=2"
        );

        await page.evaluate(() => {
          window.history.pushState(
            window.history.state,
            "",
            "/signed-checkpoints"
            + "?source=history"
            + "&signedPage=3"
          );

          window.dispatchEvent(
            new PopStateEvent(
              "popstate"
            )
          );
        });

        await waitForSearch(
          page,
          "?source=history"
          + "&signedPage=3"
        );

        await page.goBack();

        await waitForSearch(
          page,
          "?source=history"
          + "&signedPage=2"
        );

        await page.goForward();

        await waitForSearch(
          page,
          "?source=history"
          + "&signedPage=3"
        );
      }
    );

    test(
      "does not create history entries during canonical cleanup",
      async ({ page }) => {
        await page.goto(
          "/audit-integrity"
        );

        const historyLengthBefore =
          await page.evaluate(() => {
            window.history.replaceState(
              window.history.state,
              "",
              "/audit-integrity"
              + "?outcome=UNKNOWN"
              + "&auditPage=-4"
            );

            return window.history.length;
          });

        await page.reload();

        await waitForSearch(
          page,
          ""
        );

        const historyLengthAfter =
          await page.evaluate(
            () => window.history.length
          );

        expect(
          historyLengthAfter
        ).toBe(historyLengthBefore);

        await expect(
          page.getByRole(
            "heading",
            {
              name: "Audit Integrity",
              level: 1
            }
          )
        ).toBeVisible();
      }
    );
  }
);
