import {
  expect,
  test,
  type Page
} from "./browser-test";

import {
  installAuditIntegrityApiHarness,
  installGovernanceApiHarness
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

  expect(
    new URL(page.url()).search
  ).toBe(expectedSearch);
}

test.describe(
  "Governance Console URL state",
  () => {
    test.beforeEach(
      async ({ page }) => {
        await installAuditIntegrityApiHarness(
          page,
          {
            eventCount: 32,
            checkpointCount: 12,
            fallbackUnhandled: true
          }
        );

        await installGovernanceApiHarness(
          page,
          12,
          true
        );
      }
    );


    test(
      "preserves a valid Audit Integrity bookmark across reload",
      async ({ page }) => {
await page.goto(
          "/audit-integrity"
          + "?outcome=DENIED"
          + "&auditPage=2"
          + "&checkpointPage=3"
        );

        await waitForSearch(
          page,
          "?outcome=DENIED"
          + "&auditPage=2"
          + "&checkpointPage=3"
        );

        await page.reload();

        await waitForSearch(
          page,
          "?outcome=DENIED"
          + "&auditPage=2"
          + "&checkpointPage=3"
        );

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

    test(
      "normalizes invalid Audit Integrity state",
      async ({ page }) => {
        await page.goto(
          "/audit-integrity"
          + "?outcome=UNKNOWN"
          + "&auditPage=-4"
          + "&checkpointPage=zero"
        );

        await waitForSearch(
          page,
          ""
        );

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

    test(
      "removes explicit default Audit Integrity values",
      async ({ page }) => {
        await page.goto(
          "/audit-integrity"
          + "?outcome=ALL"
          + "&auditPage=1"
          + "&checkpointPage=1"
        );

        await waitForSearch(
          page,
          ""
        );
      }
    );

    test(
      "preserves unrelated parameters while canonicalizing table state",
      async ({ page }) => {
        await page.goto(
          "/audit-integrity"
          + "?source=operator"
          + "&outcome=ALL"
          + "&auditPage=1"
          + "&checkpointPage=2"
        );

        await waitForSearch(
          page,
          "?source=operator"
          + "&checkpointPage=2"
        );
      }
    );

    test(
      "preserves a valid Signed Checkpoints bookmark across reload",
      async ({ page }) => {
        await page.goto(
          "/signed-checkpoints"
          + "?signedPage=4"
        );

        await waitForSearch(
          page,
          "?signedPage=4"
        );

        await page.reload();

        await waitForSearch(
          page,
          "?signedPage=4"
        );

        await expect(
          page.getByRole(
            "heading",
            {
              name:
                "Signed Checkpoints",
              level: 1
            }
          )
        ).toBeVisible();
      }
    );

    test(
      "normalizes invalid Signed Checkpoints state",
      async ({ page }) => {
        await page.goto(
          "/signed-checkpoints"
          + "?signedPage=-8"
        );

        await waitForSearch(
          page,
          ""
        );
      }
    );

    test(
      "removes the explicit Signed Checkpoints default",
      async ({ page }) => {
        await page.goto(
          "/signed-checkpoints"
          + "?signedPage=1"
        );

        await waitForSearch(
          page,
          ""
        );
      }
    );

    test(
      "preserves unrelated Signed Checkpoints parameters",
      async ({ page }) => {
        await page.goto(
          "/signed-checkpoints"
          + "?source=audit"
          + "&signedPage=3"
        );

        await waitForSearch(
          page,
          "?source=audit"
          + "&signedPage=3"
        );
      }
    );
  }
);
