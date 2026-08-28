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
  DiagnosticFindingsSummary
} from "./diagnostic-findings-summary";

describe(
  "DiagnosticFindingsSummary",
  () => {
    it(
      "renders the governed primary diagnostic and supporting metrics",
      () => {
        render(
          <DiagnosticFindingsSummary
            dominantConstraint="APPROVAL_DELAYED"
            governanceDebtScore={72.4}
            governanceDebtBand="high"
            totalFriction={38.7}
            evidenceQualityScore={0.91}
            evidenceQualityGrade="strong"
            recognizedConstraintEvents={14}
            uniqueWorkItemCount={9}
            findings={[
              "Approval delay is concentrated in the review workflow.",
              "Escalation events increase after repeated approval waits."
            ]}
            readyForAnalysis={true}
          />
        );

        expect(
          screen.getByRole(
            "heading",
            {
              name:
                "What FIP diagnosed"
            }
          )
        ).toBeInTheDocument();

        expect(
          screen.getByText(
            "APPROVAL_DELAYED"
          )
        ).toBeInTheDocument();

        expect(
          screen.getByText(
            "72.4"
          )
        ).toBeInTheDocument();

        expect(
          screen.getByText(
            "38.7"
          )
        ).toBeInTheDocument();

        expect(
          screen.getByText(
            "0.91"
          )
        ).toBeInTheDocument();

        expect(
          screen.getByText(
            "14"
          )
        ).toBeInTheDocument();

        expect(
          screen.getByText(
            "9"
          )
        ).toBeInTheDocument();

        expect(
          screen.getByText(
            "High band"
          )
        ).toBeInTheDocument();

        expect(
          screen.getByText(
            "Strong quality"
          )
        ).toBeInTheDocument();

        expect(
          screen.getByText(
            "2 findings"
          )
        ).toBeInTheDocument();

        expect(
          screen.getByText(
            "Approval delay is concentrated in the review workflow."
          )
        ).toBeInTheDocument();

        expect(
          screen.getByText(
            "Escalation events increase after repeated approval waits."
          )
        ).toBeInTheDocument();

        expect(
          screen.getByText(
            "Evidence ready"
          )
        ).toBeInTheDocument();
      }
    );

    it(
      "does not promote the dominant constraint to root cause",
      () => {
        render(
          <DiagnosticFindingsSummary
            dominantConstraint="WORK_BLOCKED"
            governanceDebtScore={45}
            governanceDebtBand="moderate"
            totalFriction={21}
            evidenceQualityScore={0.78}
            evidenceQualityGrade="adequate"
            recognizedConstraintEvents={6}
            uniqueWorkItemCount={4}
            findings={[]}
            readyForAnalysis={false}
          />
        );

        expect(
          screen.getByText(
            /not an assertion of root cause/i
          )
        ).toBeInTheDocument();

        expect(
          screen.getByText(
            /should not be interpreted automatically as the root cause/i
          )
        ).toBeInTheDocument();

        expect(
          screen.getByText(
            "Evidence review"
          )
        ).toBeInTheDocument();

        expect(
          screen.getByText(
            "No supporting findings were generated for this assessment."
          )
        ).toBeInTheDocument();
      }
    );
  }
);