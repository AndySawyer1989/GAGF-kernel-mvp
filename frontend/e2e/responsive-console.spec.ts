import {
  expect,
  test
} from "@playwright/test";

const consolePages = [
  {
    path: "/signed-checkpoints",
    heading: "Signed Checkpoints"
  },
  {
    path: "/audit-integrity",
    heading: "Audit Integrity"
  }
] as const;

test.describe(
  "Governance Console responsive layout",
  () => {
    for (const consolePage of consolePages) {
      test(
        `${consolePage.heading} fits the active viewport`,
        async ({ page }) => {
          await page.goto(
            consolePage.path
          );

          await expect(
            page.getByRole(
              "heading",
              {
                name:
                  consolePage.heading,
                level: 1
              }
            )
          ).toBeVisible();

          await expect(
            page.locator(
              "#console-main-content"
            )
          ).toBeVisible();

          const viewportMetrics =
            await page.evaluate(() => {
              const root =
                document.documentElement;

              const body =
                document.body;

              return {
                viewportWidth:
                  window.innerWidth,

                rootScrollWidth:
                  root.scrollWidth,

                bodyScrollWidth:
                  body.scrollWidth
              };
            });

          expect(
            viewportMetrics
              .rootScrollWidth
          ).toBeLessThanOrEqual(
            viewportMetrics
              .viewportWidth
          );

          expect(
            viewportMetrics
              .bodyScrollWidth
          ).toBeLessThanOrEqual(
            viewportMetrics
              .viewportWidth
          );
        }
      );
    }

    test(
      "preserves keyboard access to main content at every viewport",
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
      }
    );

    test(
      "keeps essential governance identity visible",
      async ({ page }) => {
        await page.goto(
          "/audit-integrity"
        );

        await expect(
          page.getByText(
            "Constitutional Audit Layer"
          )
        ).toBeVisible();

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
