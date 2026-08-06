import {
  expect,
  test
} from "./browser-test";

import {
  installAuditIntegrityApiHarness,
  installGovernanceApiHarness
} from "./governance-api-harness";

test.describe(
  "Governance Console shell",
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
      "renders Signed Checkpoints with accessible page structure",
      async ({ page }) => {
        await page.goto(
          "/signed-checkpoints"
        );

        await expect(
          page.locator("h1")
        ).toHaveCount(1);

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

        await expect(
          page.getByRole(
            "navigation",
            {
              name:
                "Primary navigation"
            }
          )
        ).toBeVisible();

        const mainContent =
          page.locator(
            "#console-main-content"
          );

        await expect(
          mainContent
        ).toBeVisible();

        await expect(
          mainContent
        ).toHaveAttribute(
          "tabindex",
          "-1"
        );
      }
    );

    test(
      "reveals the skip link and transfers focus to main content",
      async ({ page }) => {
        await page.goto(
          "/signed-checkpoints"
        );

        const skipLink =
          page.getByRole(
            "link",
            {
              name:
                "Skip to main content"
            }
          );

        await page.keyboard.press(
          "Tab"
        );

        await expect(
          skipLink
        ).toBeFocused();

        await expect(
          skipLink
        ).toBeVisible();

        await page.keyboard.press(
          "Enter"
        );

        await expect(
          page.locator(
            "#console-main-content"
          )
        ).toBeFocused();

        await expect(page).toHaveURL(
          /#console-main-content$/
        );
      }
    );

    test(
      "navigates between audit pages in a real browser",
      async ({ page }) => {
        await page.goto(
          "/signed-checkpoints"
        );

        const auditIntegrityLink =
          page.locator(
            'a.secondary-button'
            + '[href="/audit-integrity"]'
          );

        await expect(
          auditIntegrityLink
        ).toBeVisible();

        await auditIntegrityLink.click();

        await expect(page).toHaveURL(
          /\/audit-integrity$/
        );

        await expect(
          page.getByRole(
            "heading",
            {
              name:
                "Audit Integrity",
              level: 1
            }
          )
        ).toBeVisible();
      }
    );
  }
);
