import {
  expect,
  test,
  type Page
} from "./browser-test";

import {
  CUSTOMER_TRIAL_ID,
  customerTrialDelivery,
  customerTrialEvidenceCommitment,
  customerTrialEvidenceCsv,
  customerTrialIdentity,
  customerTrialScope,
  customerTrialWorkflowExpectations
} from "./paid-assessment-customer-trial-fixture";

/**
 * 04H-02 / 04H-03
 *
 * Real browser-driven paid-assessment customer trial.
 *
 * This test proves workflow execution only.
 *
 * It intentionally does NOT assert:
 *
 * - dominant constraint,
 * - primary diagnosis,
 * - root cause,
 * - intervention authority,
 * - systemic scope,
 * - diagnostic correctness.
 */

function multiline(
  values: readonly string[]
): string {
  return values.join("\n");
}

async function fillWrappedTextarea(
  page: Page,
  labelText: string,
  value: string
): Promise<void> {
  const label =
    page
      .locator("label")
      .filter({
        hasText: labelText
      });

  await expect(
    label
  ).toHaveCount(1);

  const textarea =
    label.locator("textarea");

  await expect(
    textarea
  ).toBeVisible();

  await textarea.fill(
    value
  );

  await expect(
    textarea
  ).toHaveValue(
    value
  );
}

async function selectWrappedSelect(
  page: Page,
  labelText: string,
  value: string
): Promise<void> {
  const label =
    page.locator("label").filter({
      hasText: labelText
    });

  await expect(
    label
  ).toHaveCount(1);

  const select =
    label.locator("select");

  await expect(
    select
  ).toBeVisible();

  await expect(
    select
  ).toBeEnabled();

  await select.selectOption(
    value
  );

  await expect(
    select
  ).toHaveValue(
    value
  );
}


async function fillWrappedInput(
  page: Page,
  labelText: string,
  value: string
): Promise<void> {
  const label =
    page.locator("label").filter({
      hasText: labelText
    });

  await expect(
    label
  ).toHaveCount(1);

  const input =
    label.locator(
      'input:not([type="checkbox"]):not([type="radio"])'
    );

  await expect(
    input
  ).toBeVisible();

  await expect(
    input
  ).toBeEnabled();

  await input.fill(
    value
  );

  await expect(
    input
  ).toHaveValue(
    value
  );
}

async function fillAuthorizationText(
  page: Page,
  labelText: string,
  value: string
): Promise<void> {
  const label =
    page
      .locator("label")
      .filter({
        hasText: labelText
      });

  await expect(
    label
  ).toHaveCount(1);

  const input =
    label.locator(
      'input[type="text"]'
    );

  await expect(
    input
  ).toBeVisible();

  await expect(
    input
  ).toBeEnabled();

  await input.fill(
    value
  );

  await expect(
    input
  ).toHaveValue(
    value
  );
}

async function confirmAuthorization(
  page: Page,
  labelText: string
): Promise<void> {
  const checkbox =
    page.getByLabel(
      labelText,
      {
        exact: true
      }
    );

  await expect(
    checkbox
  ).toBeVisible();

  await expect(
    checkbox
  ).toBeEnabled();

  if (
    !(await checkbox.isChecked())
  ) {
    await checkbox.check();
  }

  /**
   * This verification is intentionally performed after
   * each state transition.
   *
   * The authorization component is controlled React state.
   * Waiting for each checkbox to visibly persist before
   * advancing prevents successive updates from racing a
   * stale value prop.
   */
  await expect(
    checkbox
  ).toBeChecked();
}

test.describe(
  "04H customer trial â€” real paid assessment lifecycle",
  () => {
    test(
      `${CUSTOMER_TRIAL_ID} executes and closes through the real browser workflow`,
      async ({
        page
      }, testInfo) => {
        test.setTimeout(
          180_000
        );

        page.setDefaultTimeout(
          10_000
        );

        const runNonce =
          Date.now();

        const projectToken =
          testInfo.project.name
            .toLowerCase()
            .replace(
              /[^a-z0-9]+/g,
              "-"
            )
            .replace(
              /^-|-$/g,
              ""
            );

        const assessmentId =
          (
            `${customerTrialIdentity.assessmentId}-` +
            `${projectToken}-` +
            `${runNonce}`
          );

        const engagementId =
          (
            `${customerTrialIdentity.engagementId}-` +
            `${projectToken}`
          );

        /**
         * ==================================================
         * 1. COMMERCIAL INTAKE
         * ==================================================
         */

        await test.step(
          "create the synthetic customer assessment through the real intake UI",
          async () => {
            await page.goto(
              "/assessments/new"
            );

            await expect(
              page.getByRole(
                "navigation",
                {
                  name:
                    "Assessment intake steps"
                }
              )
            ).toBeVisible();

            await page
              .getByLabel(
                "Client ID",
                {
                  exact: true
                }
              )
              .fill(
                customerTrialIdentity.clientId
              );

            await page
              .getByLabel(
                "Client display name",
                {
                  exact: true
                }
              )
              .fill(
                customerTrialIdentity.clientDisplayName
              );

            await page
              .getByLabel(
                "Engagement ID",
                {
                  exact: true
                }
              )
              .fill(
                engagementId
              );

            await page
              .getByLabel(
                "Assessment ID",
                {
                  exact: true
                }
              )
              .fill(
                assessmentId
              );

            await page
              .getByLabel(
                "Assessment name",
                {
                  exact: true
                }
              )
              .fill(
                customerTrialIdentity.assessmentName
              );

            const continueToScope =
              page.getByRole(
                "button",
                {
                  name:
                    "Continue to scope"
                }
              );

            await expect(
              continueToScope
            ).toBeEnabled();

            await continueToScope.click();

            await expect(
              page.getByText(
                "Assessment scope",
                {
                  exact: true
                }
              )
            ).toBeVisible();

            await page
              .getByLabel(
                "Period start",
                {
                  exact: true
                }
              )
              .fill(
                customerTrialScope.periodStart
              );

            await page
              .getByLabel(
                "Period end",
                {
                  exact: true
                }
              )
              .fill(
                customerTrialScope.periodEnd
              );

            await fillWrappedTextarea(
              page,
              "Workflow names",
              multiline(
                customerTrialScope.workflowNames
              )
            );

            await fillWrappedTextarea(
              page,
              "Organizational units",
              multiline(
                customerTrialScope.organizationalUnits
              )
            );

            await fillWrappedTextarea(
              page,
              "Objectives",
              multiline(
                customerTrialScope.objectives
              )
            );

            await fillWrappedTextarea(
              page,
              "Expected outcomes",
              multiline(
                customerTrialScope.expectedOutcomes
              )
            );

            const continueToEvidence =
              page.getByRole(
                "button",
                {
                  name:
                    "Continue to evidence"
                }
              );

            await expect(
              continueToEvidence
            ).toBeEnabled();

            await continueToEvidence.click();

            await expect(
              page.getByText(
                "Evidence commitment",
                {
                  exact: true
                }
              )
            ).toBeVisible();

            await page
              .getByLabel(
                "Requirement ID",
                {
                  exact: true
                }
              )
              .fill(
                customerTrialEvidenceCommitment.requirementId
              );

            await page
              .getByLabel(
                "Minimum record count",
                {
                  exact: true
                }
              )
              .fill(
                String(
                  customerTrialEvidenceCommitment.minimumRecordCount
                )
              );

            await page
              .getByLabel(
                "Requirement description",
                {
                  exact: true
                }
              )
              .fill(
                customerTrialEvidenceCommitment.requirementDescription
              );

            await page
              .getByLabel(
                "Source ID",
                {
                  exact: true
                }
              )
              .fill(
                customerTrialEvidenceCommitment.sourceId
              );

            await page
              .getByLabel(
                "Source display name",
                {
                  exact: true
                }
              )
              .fill(
                customerTrialEvidenceCommitment.sourceDisplayName
              );

            await fillWrappedTextarea(
              page,
              "CSV evidence",
              customerTrialEvidenceCsv
            );

            const reviewAssessment =
              page.getByRole(
                "button",
                {
                  name:
                    "Review assessment"
                }
              );

            await expect(
              reviewAssessment
            ).toBeEnabled();

            await reviewAssessment.click();

            await page
              .getByLabel(
                "Prepared by",
                {
                  exact: true
                }
              )
              .fill(
                customerTrialDelivery.preparedBy
              );

            await page
              .getByLabel(
                "Maximum priorities",
                {
                  exact: true
                }
              )
              .fill(
                String(
                  customerTrialDelivery.maximumPriorities
                )
              );

            await expect(
              page.getByText(
                customerTrialIdentity.clientDisplayName,
                {
                  exact: true
                }
              )
            ).toBeVisible();

            await expect(
              page.getByText(
                assessmentId,
                {
                  exact: true
                }
              )
            ).toBeVisible();
          }
        );

        /**
         * ==================================================
         * 2. GOVERNED ASSESSMENT CREATION
         * ==================================================
         */

        await test.step(
          "execute the governed assessment intake",
          async () => {
            const executeButton =
              page.getByRole(
                "button",
                {
                  name:
                    "Execute assessment"
                }
              );

            await expect(
              executeButton
            ).toBeEnabled();

            await executeButton.click();

            await expect(
              page.getByText(
                customerTrialWorkflowExpectations
                  .completionSignals[0],
                {
                  exact: true
                }
              )
            ).toBeVisible();

            const openAssessment =
              page.getByRole(
                "link",
                {
                  name:
                    customerTrialWorkflowExpectations
                      .completionSignals[1]
                }
              );

            await expect(
              openAssessment
            ).toBeVisible();

            await openAssessment.click();
          }
        );

        /**
         * ==================================================
         * 3. COMPLETE PA015 EXECUTION AUTHORIZATION
         * ==================================================
         */

        await test.step(
          "complete every explicit paid-assessment execution authorization",
          async () => {
            await expect(
              page.getByRole(
                "heading",
                {
                  name:
                    "Assessment workflow"
                }
              )
            ).toBeVisible();

            /**
             * The constitutional execution gate requires
             * three non-empty operator/context values.
             */

             await fillAuthorizationText(
              page,
              "Operator name",
              customerTrialDelivery.preparedBy
            );

            await fillAuthorizationText(
              page,
              "Client contact",
              "Northstar Customer Trial Contact"
            );

            await fillAuthorizationText(
              page,
              "Evidence classification",
              "non_sensitive"
            );

            /**
             * Assessment scope
             */

            await confirmAuthorization(
              page,
              "Assessment scope has been reviewed and confirmed."
            );

            await confirmAuthorization(
              page,
              "Evidence scope has been reviewed and confirmed."
            );

            await confirmAuthorization(
              page,
              "Client data use has been confirmed."
            );

            await confirmAuthorization(
              page,
              "Operator readiness has been confirmed."
            );

            /**
             * Evidence approval
             */

            await confirmAuthorization(
              page,
              "Client authorization covers this evidence for the assessment."
            );

            await confirmAuthorization(
              page,
              "Evidence minimization review is complete."
            );

            await confirmAuthorization(
              page,
              "Direct identifiers have been removed where required."
            );

            await confirmAuthorization(
              page,
              "I approve the displayed immutable evidence commitments for execution."
            );

            /**
             * Storage controls
             */

            await confirmAuthorization(
              page,
              "Execution storage is operator controlled."
            );

            await confirmAuthorization(
              page,
              "Access is restricted."
            );

            await confirmAuthorization(
              page,
              "Storage protection is confirmed."
            );

            await confirmAuthorization(
              page,
              "Backup plan is recorded."
            );

            await confirmAuthorization(
              page,
              "Retention period is recorded."
            );

            await confirmAuthorization(
              page,
              "Deletion plan is recorded."
            );

            /**
             * Contract execution
             */

            await confirmAuthorization(
              page,
              "The contract has been executed."
            );

            await confirmAuthorization(
              page,
              "Contract execution is ready for review."
            );

            await confirmAuthorization(
              page,
              "Contract execution has been confirmed."
            );

            await confirmAuthorization(
              page,
              "Executed contract reference is recorded."
            );

            await confirmAuthorization(
              page,
              "Execution timestamp is recorded."
            );

            await confirmAuthorization(
              page,
              "All required signatures are recorded."
            );

            await confirmAuthorization(
              page,
              "A human operator confirmed contract execution."
            );

            /**
             * Final paid-work authorization
             */

            await confirmAuthorization(
              page,
              "Paid assessment execution is explicitly authorized."
            );

            /**
             * The source gate requires every condition above,
             * plus readyForAnalysis and completed loading.
             */

            const runDiagnostic =
              page.getByRole(
                "button",
                {
                  name:
                    "Run Diagnostic"
                }
              );

            await expect(
              runDiagnostic
            ).toBeEnabled();
          }
        );

        /**
         * ==================================================
         * 4. REAL PA015 EXECUTION
         * ==================================================
         */

        await test.step(
          "run PA015 through the real governed execution endpoint",
          async () => {
            const runDiagnostic =
              page.getByRole(
                "button",
                {
                  name:
                    "Run Diagnostic"
                }
              );

            await runDiagnostic.click();

            await expect(
              page.getByRole(
                "button",
                {
                  name:
                    "Diagnostic complete"
                }
              )
            ).toBeVisible();

            const diagnosticRegion =
              page.getByRole(
                "region",
                {
                  name:
                    "What FIP diagnosed"
                }
              );

            await expect(
              diagnosticRegion
            ).toBeVisible();

            await expect(
              diagnosticRegion.getByText(
                "Governance debt",
                {
                  exact: true
                }
              )
            ).toBeVisible();

            await expect(
              diagnosticRegion.getByText(
                "Evidence quality",
                {
                  exact: true
                }
              )
            ).toBeVisible();

            await expect(
              diagnosticRegion.getByText(
                "Weighted friction",
                {
                  exact: true
                }
              )
            ).toBeVisible();
          }
        );

        /**
         * ==================================================
         * 5. DELIVERY READINESS
         * ==================================================
         */

        await test.step(
          "verify governed delivery readiness",
          async () => {
            const readinessButton =
              page.getByRole(
                "button",
                {
                  name:
                    "Verify delivery readiness"
                }
              );

            await expect(
              readinessButton
            ).toBeEnabled();

            await readinessButton.click();

            await expect(
              page.getByText(
                "Ready for approval",
                {
                  exact: true
                }
              )
            ).toBeVisible();
          }
        );

        /**
         * ==================================================
         * 6. HUMAN DELIVERY APPROVAL
         * ==================================================
         */

        await test.step(
          "record explicit human delivery approval",
          async () => {
            await confirmAuthorization(
              page,
              "Assessment scope reviewed and approved"
            );

            await confirmAuthorization(
              page,
              "Evidence boundary reviewed and approved"
            );

            await confirmAuthorization(
              page,
              "Buyer-facing language reviewed and approved"
            );

            await confirmAuthorization(
              page,
              "I explicitly approve this governed package for human delivery"
            );

            const approveButton =
              page.getByRole(
                "button",
                {
                  name:
                    "Approve for human delivery"
                }
              );

            await expect(
              approveButton
            ).toBeEnabled();

            await approveButton.click();

            await expect(
              page.getByText(
                "Approved for delivery",
                {
                  exact: true
                }
              )
            ).toBeVisible();
          }
        );

        /**
         * ==================================================
         * 7. HUMAN DELIVERY
         * ==================================================
         */

        await test.step(
          "record governed human delivery",
          async () => {
            await selectWrappedSelect(
              page,
              "Delivery method",
              "email"
            );

            await fillWrappedInput(
              page,
              "Delivery reference",
              `customer-trial-delivery-${runNonce}`
            );

            await confirmAuthorization(
              page,
              "I confirm that the governed report package was delivered"
            );

            const deliveryButton =
              page.getByRole(
                "button",
                {
                  name:
                    "Record human delivery"
                }
              );

            await expect(
              deliveryButton
            ).toBeEnabled();

            await deliveryButton.click();

            await expect(
              page.getByText(
                "Governed human delivery recorded.",
                {
                  exact: true
                }
              )
            ).toBeVisible();
          }
        );

        /**
         * ==================================================
         * 8. CLIENT RECEIPT
         * ==================================================
         */

        await test.step(
          "record explicit client receipt",
          async () => {
            await selectWrappedSelect(
              page,
              "Acknowledgment method",
              "email_reply"
            );

            await fillWrappedInput(
              page,
              "Acknowledgment reference",
              `customer-trial-receipt-${runNonce}`
            );

            await confirmAuthorization(
              page,
              "I confirm that the client explicitly acknowledged receipt of the report"
            );

            const receiptButton =
              page.getByRole(
                "button",
                {
                  name:
                    "Record client receipt"
                }
              );

            await expect(
              receiptButton
            ).toBeEnabled();

            await receiptButton.click();

            await expect(
              page.getByText(
                "Client receipt acknowledged.",
                {
                  exact: true
                }
              )
            ).toBeVisible();
          }
        );

        /**
         * ==================================================
         * 9. CLIENT RESPONSE
         * ==================================================
         */

        await test.step(
          "record an explicit client response",
          async () => {
            await selectWrappedSelect(
              page,
              "Response method",
              "email_reply"
            );

            await page
              .getByPlaceholder(
                "Message ID, meeting note, or response reference"
              )
              .fill(
                `customer-trial-response-${runNonce}`
              );

            await selectWrappedSelect(
              page,
              "Findings disposition",
              "acknowledged"
            );

            await selectWrappedSelect(
              page,
              "Recommendations disposition",
              "accepted"
            );

            await page
              .getByPlaceholder(
                "Optional client response note"
              )
              .fill(
                "Synthetic customer-trial response recorded for end-to-end lifecycle proof."
              );

            const responseButton =
              page.getByRole(
                "button",
                {
                  name:
                    "Record client response"
                }
              );

            await expect(
              responseButton
            ).toBeEnabled();

            await responseButton.click();

            await expect(
              page.getByText(
                "Client response recorded.",
                {
                  exact: true
                }
              )
            ).toBeVisible();
          }
        );

        /**
         * ==================================================
         * 10. RESPONSE-STAGE RESTORATION
         * ==================================================
         */

        await test.step(
          "restore the response state after browser reload",
          async () => {
            await page.reload({
              waitUntil:
                "domcontentloaded"
            });

            await expect(
              page.getByRole(
                "heading",
                {
                  name:
                    "Administrative closeout available"
                }
              )
            ).toBeVisible();

            await expect(
              page.getByText(
                "Client response recorded.",
                {
                  exact: true
                }
              )
            ).toBeVisible();
          }
        );

        /**
         * ==================================================
         * 11. ADMINISTRATIVE CLOSEOUT
         * ==================================================
         */

        await test.step(
          "record explicit administrative closeout",
          async () => {
            await page
              .getByLabel(
                "Closeout reason",
                {
                  exact: true
                }
              )
              .fill(
                "Customer trial lifecycle completed and administrative processing verified."
              );

            const closeoutConfirmation =
              page.getByLabel(
                /I explicitly confirm administrative closeout/i
              );

            await expect(
              closeoutConfirmation
            ).toBeVisible();

            await closeoutConfirmation.check();

            await expect(
              closeoutConfirmation
            ).toBeChecked();

            const closeoutButton =
              page.getByRole(
                "button",
                {
                  name:
                    "Record administrative closeout"
                }
              );

            await expect(
              closeoutButton
            ).toBeEnabled();

            await closeoutButton.click();

            await expect(
              page.getByRole(
                "heading",
                {
                  name:
                    "Assessment administratively closed"
                }
              )
            ).toBeVisible();

            await expect(
              page.getByText(
                "assessment_closed",
                {
                  exact: true
                }
              )
            ).toBeVisible();

            await expect(
              page.getByText(
                "Governed administrative closeout recorded.",
                {
                  exact: true
                }
              )
            ).toBeVisible();
          }
        );

        /**
         * ==================================================
         * 12. TERMINAL RESTART PROOF
         * ==================================================
         */

        await test.step(
          "restore persisted assessment_closed after reload",
          async () => {
            await page.reload({
              waitUntil:
                "domcontentloaded"
            });

            await expect(
              page.getByRole(
                "heading",
                {
                  name:
                    "Assessment administratively closed"
                }
              )
            ).toBeVisible();

            await expect(
              page.getByText(
                "assessment_closed",
                {
                  exact: true
                }
              )
            ).toBeVisible();

            await expect(
              page.getByText(
                "Governed administrative closeout recorded.",
                {
                  exact: true
                }
              )
            ).toBeVisible();

            await expect(
              page.getByRole(
                "button",
                {
                  name:
                    "Record administrative closeout"
                }
              )
            ).toHaveCount(0);
          }
        );
      }
    );
  }
);
