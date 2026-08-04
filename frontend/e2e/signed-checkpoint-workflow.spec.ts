import {
  expect,
  test
} from "./browser-test";

import {
  CREATED_CHECKPOINT_ID,
  expectGovernanceHeaders,
  installGovernanceApiHarness
} from "./governance-api-harness";

test.describe(
  "Signed Checkpoint real API workflow",
  () => {
    test(
      "paginates through intercepted records and restores history",
      async ({ page }) => {
        await installGovernanceApiHarness(
          page,
          12
        );

        await page.goto(
          "/signed-checkpoints"
        );

        await expect(
          page.getByRole(
            "heading",
            {
              name:
                "Signed checkpoint inventory"
            }
          )
        ).toBeVisible();

        await expect(
          page.getByText(
            "Page 1 of 3"
          )
        ).toBeVisible();

        await expect(
          page.getByText(
            "checkpoint-e2e-001"
          )
        ).toBeVisible();

        await page.getByRole(
          "button",
          {
            name:
              "Next Signed checkpoints page"
          }
        ).click();

        await expect(page).toHaveURL(
          /[?&]signedPage=2(?:&|$)/
        );

        await expect(
          page.getByText(
            "Page 2 of 3"
          )
        ).toBeVisible();

        await expect(
          page.getByText(
            "checkpoint-e2e-006"
          )
        ).toBeVisible();

        await page.getByRole(
          "button",
          {
            name:
              "Next Signed checkpoints page"
          }
        ).click();

        await expect(page).toHaveURL(
          /[?&]signedPage=3(?:&|$)/
        );

        await expect(
          page.getByText(
            "checkpoint-e2e-011"
          )
        ).toBeVisible();

        await page.goBack();

        await expect(page).toHaveURL(
          /[?&]signedPage=2(?:&|$)/
        );

        await expect(
          page.getByText(
            "Page 2 of 3"
          )
        ).toBeVisible();

        await expect(
          page.getByText(
            "checkpoint-e2e-006"
          )
        ).toBeVisible();
      }
    );

    test(
      "creates and verifies a signed checkpoint through the dialog",
      async ({ page }) => {
        const harness =
          await installGovernanceApiHarness(
            page,
            6
          );

        await page.goto(
          "/signed-checkpoints"
        );

        await expect(
          page.getByRole(
            "heading",
            {
              name:
                "Durable signing available"
            }
          )
        ).toBeVisible();

        await page.getByRole(
          "button",
          {
            name:
              "Create signed checkpoint"
          }
        ).click();

        const dialog =
          page.getByRole(
            "dialog",
            {
              name:
                "Create a signed checkpoint?"
            }
          );

        await expect(
          dialog
        ).toBeVisible();

        await dialog.getByRole(
          "button",
          {
            name: "Create and sign"
          }
        ).click();

        await expect(
          page.getByText(
            `Checkpoint `
            + `${CREATED_CHECKPOINT_ID} `
            + "was created and signed."
          )
        ).toBeVisible();

        await expect(
          page.getByRole(
            "heading",
            {
              name:
                "Signed checkpoint created"
            }
          )
        ).toBeVisible();

        await expect(
          page.getByText(
            CREATED_CHECKPOINT_ID
          ).first()
        ).toBeVisible();

        await expect(
          page.getByText(
            "Signature valid"
          ).first()
        ).toBeVisible();

        const createRequest =
          harness.requests.find(
            (request) => {
              const url =
                new URL(
                  request.url()
                );

              return (
                request.method()
                  === "POST"
                && url.pathname
                  ===
                  "/api/v1/"
                  + "governance-assessments/"
                  + "audit-checkpoints"
              );
            }
          );

        expect(
          createRequest
        ).toBeDefined();

        await expectGovernanceHeaders(
          createRequest!
        );

        expect(
          harness.signedRecords[0]
        ).toMatchObject({
          checkpoint: {
            checkpoint_id:
              CREATED_CHECKPOINT_ID
          }
        });

        expect(
          harness.verificationItems[0]
        ).toMatchObject({
          checkpoint_id:
            CREATED_CHECKPOINT_ID,
          valid: true
        });
      }
    );
  }
);
