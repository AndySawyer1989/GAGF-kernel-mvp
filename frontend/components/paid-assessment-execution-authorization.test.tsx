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
  PaidAssessmentExecutionAuthorization,
  type PaidAssessmentExecutionAuthorizationValue
} from "./paid-assessment-execution-authorization";


const VALUE:
  PaidAssessmentExecutionAuthorizationValue = {
    operatorName: "",
    clientContactName: "",
    classification: "non_sensitive",

    assessmentScopeConfirmed: false,
    evidenceScopeConfirmed: false,
    clientDataUseConfirmed: false,
    operatorReadinessConfirmed: false,

    clientAuthorizedForAssessment: false,
    minimizationReviewCompleted: false,
    directIdentifiersRemoved: false,

    operatorControlledLocation: false,
    accessRestricted: false,
    storageProtectionConfirmed: false,
    backupPlanRecorded: false,
    retentionPeriodRecorded: false,
    deletionPlanRecorded: false,

    contractExecuted: false,
    contractExecutionReviewReady: false,
    contractExecutionConfirmed: false,
    executedContractReferenceRecorded: false,
    executedAtRecorded: false,
    allRequiredSignaturesRecorded: false,
    humanOperatorConfirmedExecution: false,

    paidAssessmentAuthorized: false,
    executionEvidenceApproved: false
  };


const BINDING = {
  hierarchy_key:
    "tenant-alpha/client-001/engagement-001/assessment-001",
  assessment_name:
    "FIP Governance Assessment",
  client_display_name:
    "Synthetic Test Organization",
  assessment_execution_request_hash:
    "request-hash-001",
  execution_input_hash:
    "execution-hash-001",
  binding_hash:
    "binding-hash-001",
  schema_version:
    "1.2.0",
  evidence: [
    {
      evidence_id:
        "evidence-001",
      source_id:
        "source-001",
      source_kind:
        "csv",
      display_name:
        "Governance workflow telemetry",
      source_location:
        "operator-upload",
      content_sha256:
        "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
    }
  ],
  boundaries: {
    raw_evidence_not_exposed:
      true,
    binding_metadata_is_not_execution_authority:
      true,
    binding_metadata_is_not_evidence_approval:
      true
  }
};


describe(
  "PaidAssessmentExecutionAuthorization",
  () => {
    it(
      "shows unavailable state without a server binding",
      () => {
        render(
          <PaidAssessmentExecutionAuthorization
            binding={null}
            value={VALUE}
            onChange={vi.fn()}
          />
        );

        expect(
          screen.getByText(
            "Execution binding unavailable"
          )
        ).toBeInTheDocument();
      }
    );

    it(
      "shows server-bound assessment metadata",
      () => {
        render(
          <PaidAssessmentExecutionAuthorization
            binding={BINDING}
            value={VALUE}
            onChange={vi.fn()}
          />
        );

        expect(
          screen.getByText(
            "FIP Governance Assessment"
          )
        ).toBeInTheDocument();

        expect(
          screen.getByText(
            "Synthetic Test Organization"
          )
        ).toBeInTheDocument();

        expect(
          screen.getByText(
            "binding-hash-001"
          )
        ).toBeInTheDocument();
      }
    );

    it(
      "shows immutable evidence commitment hashes",
      () => {
        render(
          <PaidAssessmentExecutionAuthorization
            binding={BINDING}
            value={VALUE}
            onChange={vi.fn()}
          />
        );

        expect(
          screen.getByText(
            "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
          )
        ).toBeInTheDocument();
      }
    );

    it(
      "updates operator-entered identity",
      () => {
        const onChange =
          vi.fn();

        render(
          <PaidAssessmentExecutionAuthorization
            binding={BINDING}
            value={VALUE}
            onChange={onChange}
          />
        );

        fireEvent.change(
          screen.getByLabelText(
            "Operator name"
          ),
          {
            target: {
              value:
                "FIP Operator"
            }
          }
        );

        expect(
          onChange
        ).toHaveBeenCalledWith(
          expect.objectContaining({
            operatorName:
              "FIP Operator"
          })
        );
      }
    );

    it(
      "records explicit paid-work authorization",
      () => {
        const onChange =
          vi.fn();

        render(
          <PaidAssessmentExecutionAuthorization
            binding={BINDING}
            value={VALUE}
            onChange={onChange}
          />
        );

        fireEvent.click(
          screen.getByLabelText(
            "Paid assessment execution is explicitly authorized."
          )
        );

        expect(
          onChange
        ).toHaveBeenCalledWith(
          expect.objectContaining({
            paidAssessmentAuthorized:
              true
          })
        );
      }
    );

    it(
      "does not treat evidence metadata as approval",
      () => {
        render(
          <PaidAssessmentExecutionAuthorization
            binding={BINDING}
            value={VALUE}
            onChange={vi.fn()}
          />
        );

        expect(
          screen.getByLabelText(
            "I approve the displayed immutable evidence commitments for execution."
          )
        ).not.toBeChecked();
      }
    );

    it(
      "disables operator controls during execution",
      () => {
        render(
          <PaidAssessmentExecutionAuthorization
            binding={BINDING}
            value={VALUE}
            disabled
            onChange={vi.fn()}
          />
        );

        expect(
          screen.getByLabelText(
            "Operator name"
          )
        ).toBeDisabled();

        expect(
          screen.getByLabelText(
            "Paid assessment execution is explicitly authorized."
          )
        ).toBeDisabled();
      }
    );
  }
);