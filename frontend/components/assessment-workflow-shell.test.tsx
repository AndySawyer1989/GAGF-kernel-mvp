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
  AssessmentWorkflowShell,
  type AssessmentWorkflowStep
} from "./assessment-workflow-shell";

const steps: AssessmentWorkflowStep[] = [
  {
    id: "intake",
    label: "Evidence Intake",
    description:
      "Evidence has been attached to the assessment.",
    state: "complete"
  },
  {
    id: "validate",
    label: "Validate Evidence",
    description:
      "Evidence must pass governed validation.",
    state: "complete"
  },
  {
    id: "diagnostic",
    label: "Run Diagnostic",
    description:
      "Governed diagnostic artifacts must be present.",
    state: "current"
  },
  {
    id: "findings",
    label: "Review Findings",
    description:
      "Review governed findings and supporting evidence.",
    state: "upcoming"
  },
  {
    id: "report",
    label: "Generate Report",
    description:
      "Prepare the governed client report.",
    state: "upcoming"
  }
];

describe(
  "AssessmentWorkflowShell",
  () => {
    it(
      "renders the commercial assessment identity",
      () => {
        render(
          <AssessmentWorkflowShell
            clientId="client-acme"
            engagementId="engagement-001"
            assessmentId="assessment-001"
            steps={steps}
            evidenceHref="/evidence/example"
            reportHref="/report/example"
          />
        );

        expect(
          screen.getByText("client-acme")
        ).toBeInTheDocument();

        expect(
          screen.getByText("engagement-001")
        ).toBeInTheDocument();

        expect(
          screen.getByText("assessment-001")
        ).toBeInTheDocument();
      }
    );

    it(
      "renders the five operator workflow steps",
      () => {
        render(
          <AssessmentWorkflowShell
            clientId="client-acme"
            engagementId="engagement-001"
            assessmentId="assessment-001"
            steps={steps}
            evidenceHref="/evidence/example"
            reportHref="/report/example"
          />
        );

        expect(
          screen.getByText("Evidence Intake")
        ).toBeInTheDocument();

        expect(
          screen.getByText("Validate Evidence")
        ).toBeInTheDocument();

        expect(
          screen.getByText("Run Diagnostic")
        ).toBeInTheDocument();

        expect(
          screen.getByText("Review Findings")
        ).toBeInTheDocument();

        expect(
          screen.getByText("Generate Report")
        ).toBeInTheDocument();
      }
    );

    it(
      "marks the governed current step",
      () => {
        render(
          <AssessmentWorkflowShell
            clientId="client-acme"
            engagementId="engagement-001"
            assessmentId="assessment-001"
            steps={steps}
            evidenceHref="/evidence/example"
            reportHref="/report/example"
          />
        );

        const currentStep =
          screen.getByText(
            "Run Diagnostic"
          ).closest("li");

        expect(currentStep).toHaveAttribute(
          "aria-current",
          "step"
        );
      }
    );

    it(
      "links to governed evidence and report surfaces",
      () => {
        render(
          <AssessmentWorkflowShell
            clientId="client-acme"
            engagementId="engagement-001"
            assessmentId="assessment-001"
            steps={steps}
            evidenceHref="/evidence/example"
            reportHref="/report/example"
          />
        );

        expect(
          screen.getByRole(
            "link",
            { name: "Explore evidence" }
          )
        ).toHaveAttribute(
          "href",
          "/evidence/example"
        );

        expect(
          screen.getByRole(
            "link",
            { name: "Open client report" }
          )
        ).toHaveAttribute(
          "href",
          "/report/example"
        );
      }
    );

    it(
      "shows workflow complete only when every step is complete",
      () => {
        const completeSteps =
          steps.map((step) => ({
            ...step,
            state: "complete" as const
          }));

        render(
          <AssessmentWorkflowShell
            clientId="client-acme"
            engagementId="engagement-001"
            assessmentId="assessment-001"
            steps={completeSteps}
            evidenceHref="/evidence/example"
            reportHref="/report/example"
          />
        );

        expect(
          screen.getByText(
            "Workflow complete"
          )
        ).toBeInTheDocument();
      }
    );
  }
);