import {
  render,
  screen,
  waitFor
} from "@testing-library/react";

import userEvent from "@testing-library/user-event";

import {
  beforeEach,
  describe,
  expect,
  it,
  vi
} from "vitest";

import NewAssessmentPage from "./page";

import {
  executeAssessment
} from "@/lib/governance-assessment-api";

import {
  createTestApiConfig
} from "@/test/governance-assessment-fixtures";

vi.mock(
  "@/lib/governance-assessment-api",
  async (importOriginal) => {
    const actual =
      await importOriginal<
        typeof import(
          "@/lib/governance-assessment-api"
        )
      >();

    return {
      ...actual,

      getGovernanceAssessmentApiConfig:
        vi.fn(
          () =>
            createTestApiConfig()
        ),

      executeAssessment:
        vi.fn()
    };
  }
);

const mockedExecuteAssessment =
  vi.mocked(
    executeAssessment
  );

async function reachReviewStep() {
  const user =
    userEvent.setup();

  await user.click(
    screen.getByRole(
      "button",
      {
        name:
          "Continue to scope"
      }
    )
  );

  await user.click(
    screen.getByRole(
      "button",
      {
        name:
          "Continue to evidence"
      }
    )
  );

  await user.click(
    screen.getByRole(
      "button",
      {
        name:
          "Review assessment"
      }
    )
  );

  return user;
}

describe(
  "NewAssessmentPage guided intake",
  () => {
    beforeEach(() => {
      vi.clearAllMocks();

      window.history.replaceState(
        {},
        "",
        "/assessments/new"
      );

      mockedExecuteAssessment
        .mockResolvedValue({
          completed:
            true,

          hierarchy_key:
            "tenant-alpha/client-acme/engagement-001/assessment-001",

          artifact_count:
            6,

          request_hash:
            "request-hash-001",

          demonstration_hash:
            "demonstration-hash-001",

          persistence_hash:
            "persistence-hash-001",

          report_id:
            "report-001",

          application_hash:
            "application-hash-001",

          schema_version:
            "1.0.0"
        });
    });

    it(
      "guides the operator through client, scope, evidence, and review steps",
      async () => {
        const user =
          userEvent.setup();

        render(
          <NewAssessmentPage />
        );

        expect(
          screen.getByRole(
            "heading",
            {
              name:
                "Client & Assessment"
            }
          )
        ).toBeInTheDocument();

        expect(
          screen.getByText(
            "Step 1 of 4"
          )
        ).toBeInTheDocument();

        expect(
          screen.getByRole(
            "button",
            {
              name:
                "Client Current"
            }
          )
        ).toHaveAttribute(
          "aria-current",
          "step"
        );

        expect(
          screen.getByRole(
            "button",
            {
              name:
                "Scope Upcoming"
            }
          )
        ).toBeInTheDocument();

        await user.click(
          screen.getByRole(
            "button",
            {
              name:
                "Continue to scope"
            }
          )
        );

        expect(
          screen.getByRole(
            "heading",
            {
              name:
                "Assessment Scope"
            }
          )
        ).toBeInTheDocument();

        expect(
          screen.getByRole(
            "button",
            {
              name:
                "Client Complete"
            }
          )
        ).toBeInTheDocument();

        expect(
          screen.getByRole(
            "button",
            {
              name:
                "Scope Current"
            }
          )
        ).toHaveAttribute(
          "aria-current",
          "step"
        );

        await user.click(
          screen.getByRole(
            "button",
            {
              name:
                "Continue to evidence"
            }
          )
        );

        expect(
          screen.getByRole(
            "heading",
            {
              name:
                "Evidence"
            }
          )
        ).toBeInTheDocument();

        expect(
          screen.getByText(
            "Count satisfied"
          )
        ).toBeInTheDocument();

        expect(
          screen.getByRole(
            "button",
            {
              name:
                "Evidence Current"
            }
          )
        ).toHaveAttribute(
          "aria-current",
          "step"
        );

        await user.click(
          screen.getByRole(
            "button",
            {
              name:
                "Review assessment"
            }
          )
        );

        expect(
          screen.getByRole(
            "heading",
            {
              name:
                "Review & Execute"
            }
          )
        ).toBeInTheDocument();

        expect(
          screen.getByText(
            "Ready to run FIP"
          )
        ).toBeInTheDocument();

        expect(
          screen.getByRole(
            "button",
            {
              name:
                "Review Current"
            }
          )
        ).toHaveAttribute(
          "aria-current",
          "step"
        );

        expect(
          screen.getByRole(
            "button",
            {
              name:
                "Execute assessment"
            }
          )
        ).toBeInTheDocument();
      }
    );

    it(
      "submits the governed assessment request only from the review step",
      async () => {
        render(
          <NewAssessmentPage />
        );

        const user =
          await reachReviewStep();

        expect(
          mockedExecuteAssessment
        ).not.toHaveBeenCalled();

        await user.click(
          screen.getByRole(
            "button",
            {
              name:
                "Execute assessment"
            }
          )
        );

        await waitFor(() => {
          expect(
            mockedExecuteAssessment
          ).toHaveBeenCalledTimes(
            1
          );
        });

        expect(
          mockedExecuteAssessment
        ).toHaveBeenCalledWith(
          expect.anything(),

          expect.objectContaining({
            tenant_id:
              "tenant-alpha",

            client_id:
              "client-acme",

            engagement_id:
              "engagement-001",

            assessment_id:
              "assessment-001",

            assessment_name:
              "Governance Runway Assessment",

            workflow_names: [
              "Incident Management"
            ],

            organizational_units: [
              "IT Operations"
            ],

            objectives: [
              "Reduce governance friction"
            ],

            expected_outcomes: [
              "Faster completion"
            ],

            client_display_name:
              "ACME Corporation",

            prepared_by:
              "FIP Governance Services",

            maximum_priorities:
              3
          })
        );
      }
    );

    it(
      "opens the completed assessment and client report from the submitted hierarchy",
      async () => {
        render(
          <NewAssessmentPage />
        );

        const user =
          await reachReviewStep();

        await user.click(
          screen.getByRole(
            "button",
            {
              name:
                "Execute assessment"
            }
          )
        );

        await waitFor(() => {
          expect(
            mockedExecuteAssessment
          ).toHaveBeenCalledTimes(
            1
          );
        });

        expect(
          await screen.findByText(
            "Assessment complete"
          )
        ).toBeInTheDocument();

        expect(
          screen.getByText(
            "6 governed artifacts were persisted."
          )
        ).toBeInTheDocument();

        expect(
          screen.getByRole(
            "link",
            {
              name:
                "Open assessment"
            }
          )
        ).toHaveAttribute(
          "href",
          "/assessments/tenant-alpha/client-acme/engagement-001/assessment-001"
        );

        expect(
          screen.getByRole(
            "link",
            {
              name:
                "View client report"
            }
          )
        ).toHaveAttribute(
          "href",
          "/assessments/tenant-alpha/client-acme/engagement-001/assessment-001/report"
        );

        expect(
          screen.getByRole(
            "link",
            {
              name:
                "View all assessments"
            }
          )
        ).toHaveAttribute(
          "href",
          "/assessments"
        );
      }
    );

    it(
      "binds delivery links to the submitted identity rather than later form edits",
      async () => {
        render(
          <NewAssessmentPage />
        );

        const user =
          await reachReviewStep();

        await user.click(
          screen.getByRole(
            "button",
            {
              name:
                "Execute assessment"
            }
          )
        );

        await screen.findByText(
          "Assessment complete"
        );

        await user.click(
          screen.getByRole(
            "button",
            {
              name:
                "Edit client details"
            }
          )
        );

        const clientInput =
          screen.getByRole(
            "textbox",
            {
              name:
                "Client ID"
            }
          );

        await user.clear(
          clientInput
        );

        await user.type(
          clientInput,
          "client-changed"
        );

        expect(
          screen.getByRole(
            "link",
            {
              name:
                "Open assessment"
            }
          )
        ).toHaveAttribute(
          "href",
          "/assessments/tenant-alpha/client-acme/engagement-001/assessment-001"
        );

        expect(
          screen.getByRole(
            "link",
            {
              name:
                "View client report"
            }
          )
        ).toHaveAttribute(
          "href",
          "/assessments/tenant-alpha/client-acme/engagement-001/assessment-001/report"
        );
      }
    );

    it(
      "lets the operator return from review to edit evidence without executing",
      async () => {
        render(
          <NewAssessmentPage />
        );

        const user =
          await reachReviewStep();

        await user.click(
          screen.getByRole(
            "button",
            {
              name:
                "Edit evidence"
            }
          )
        );

        expect(
          screen.getByRole(
            "textbox",
            {
              name:
                "CSV evidence"
            }
          )
        ).toBeInTheDocument();

        expect(
          screen.getByRole(
            "button",
            {
              name:
                "Evidence Current"
            }
          )
        ).toHaveAttribute(
          "aria-current",
          "step"
        );

        expect(
          mockedExecuteAssessment
        ).not.toHaveBeenCalled();
      }
    );
  }
);