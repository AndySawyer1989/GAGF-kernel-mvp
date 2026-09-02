import {
  fireEvent,
  render,
  screen
} from "@testing-library/react";

import {
  describe,
  expect,
  it,
  vi
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


function renderShell(
  overrides: Partial<
    React.ComponentProps<
      typeof AssessmentWorkflowShell
    >
  > = {}
) {
  return render(
    <AssessmentWorkflowShell
      clientId="client-acme"
      engagementId="engagement-001"
      assessmentId="assessment-001"
      steps={steps}
      evidenceHref="/evidence/example"
      reportHref="/report/example"
      {...overrides}
    />
  );
}


describe(
  "AssessmentWorkflowShell",
  () => {
    it(
      "renders the commercial assessment identity",
      () => {
        renderShell();

        expect(
          screen.getByText(
            "client-acme"
          )
        ).toBeInTheDocument();

        expect(
          screen.getByText(
            "engagement-001"
          )
        ).toBeInTheDocument();

        expect(
          screen.getByText(
            "assessment-001"
          )
        ).toBeInTheDocument();
      }
    );

    it(
      "renders the five operator workflow steps",
      () => {
        renderShell();

        expect(
          screen.getByText(
            "Evidence Intake"
          )
        ).toBeInTheDocument();

        expect(
          screen.getByText(
            "Validate Evidence"
          )
        ).toBeInTheDocument();

        expect(
          screen.getAllByText(
            "Run Diagnostic"
          ).length
        ).toBeGreaterThan(
          0
        );

        expect(
          screen.getByText(
            "Review Findings"
          )
        ).toBeInTheDocument();

        expect(
          screen.getByText(
            "Generate Report"
          )
        ).toBeInTheDocument();
      }
    );

    it(
      "marks the governed current step",
      () => {
        renderShell();

        const currentStep =
          screen.getAllByText(
            "Run Diagnostic"
          )[0].closest(
            "li"
          );

        expect(
          currentStep
        ).toHaveAttribute(
          "aria-current",
          "step"
        );
      }
    );

    it(
      "links to governed evidence and report surfaces",
      () => {
        renderShell();

        expect(
          screen.getByRole(
            "link",
            {
              name:
                "Explore evidence"
            }
          )
        ).toHaveAttribute(
          "href",
          "/evidence/example"
        );

        expect(
          screen.getByRole(
            "link",
            {
              name:
                "Open client report"
            }
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
          steps.map(
            (step) => ({
              ...step,
              state:
                "complete" as const
            })
          );

        renderShell({
          steps:
            completeSteps
        });

        expect(
          screen.getByText(
            "Workflow complete"
          )
        ).toBeInTheDocument();
      }
    );

    it(
      "enables governed diagnostic execution when ready",
      () => {
        const onRunDiagnostic =
          vi.fn();

        renderShell({
          canRunDiagnostic: true,
          onRunDiagnostic
        });

        const button =
          screen.getByRole(
            "button",
            {
              name:
                "Run Diagnostic"
            }
          );

        expect(
          button
        ).toBeEnabled();

        fireEvent.click(
          button
        );

        expect(
          onRunDiagnostic
        ).toHaveBeenCalledTimes(
          1
        );
      }
    );

    it(
      "disables diagnostic execution before readiness",
      () => {
        const onRunDiagnostic =
          vi.fn();

        renderShell({
          canRunDiagnostic: false,
          onRunDiagnostic
        });

        const button =
          screen.getByRole(
            "button",
            {
              name:
                "Run Diagnostic"
            }
          );

        expect(
          button
        ).toBeDisabled();

        fireEvent.click(
          button
        );

        expect(
          onRunDiagnostic
        ).not.toHaveBeenCalled();
      }
    );

    it(
      "shows running state during governed execution",
      () => {
        renderShell({
          canRunDiagnostic: true,
          diagnosticRunning: true,
          onRunDiagnostic:
            vi.fn()
        });

        expect(
          screen.getByRole(
            "button",
            {
              name:
                "Running diagnostic..."
            }
          )
        ).toBeDisabled();
      }
    );

    it(
      "does not allow a second run after diagnostic completion",
      () => {
        const completeDiagnosticSteps =
          steps.map(
            (step) =>
              step.id ===
              "diagnostic"
                ? {
                    ...step,
                    state:
                      "complete" as const
                  }
                : step
          );

        renderShell({
          steps:
            completeDiagnosticSteps,
          canRunDiagnostic: true,
          onRunDiagnostic:
            vi.fn()
        });

        expect(
          screen.getByRole(
            "button",
            {
              name:
                "Diagnostic complete"
            }
          )
        ).toBeDisabled();
      }
    );

    it(
      "surfaces the governed execution disposition",
      () => {
        renderShell({
          diagnosticDisposition:
            "reconciled"
        });

        expect(
          screen.getByText(
            "Diagnostic reconciled"
          )
        ).toBeInTheDocument();
      }
    );
  }
);