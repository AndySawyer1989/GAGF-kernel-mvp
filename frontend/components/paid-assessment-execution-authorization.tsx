"use client";

import type {
  CommercialPaidAssessmentExecutionInputBindingMetadata
} from "@/lib/governance-assessment-api";


export type PaidAssessmentExecutionAuthorizationValue = {
  operatorName: string;
  clientContactName: string;
  classification: string;

  assessmentScopeConfirmed: boolean;
  evidenceScopeConfirmed: boolean;
  clientDataUseConfirmed: boolean;
  operatorReadinessConfirmed: boolean;

  clientAuthorizedForAssessment: boolean;
  minimizationReviewCompleted: boolean;
  directIdentifiersRemoved: boolean;

  operatorControlledLocation: boolean;
  accessRestricted: boolean;
  storageProtectionConfirmed: boolean;
  backupPlanRecorded: boolean;
  retentionPeriodRecorded: boolean;
  deletionPlanRecorded: boolean;

  contractExecuted: boolean;
  contractExecutionReviewReady: boolean;
  contractExecutionConfirmed: boolean;
  executedContractReferenceRecorded: boolean;
  executedAtRecorded: boolean;
  allRequiredSignaturesRecorded: boolean;
  humanOperatorConfirmedExecution: boolean;

  paidAssessmentAuthorized: boolean;
  executionEvidenceApproved: boolean;
};


type PaidAssessmentExecutionAuthorizationProps = {
  binding:
    CommercialPaidAssessmentExecutionInputBindingMetadata | null;

  value:
    PaidAssessmentExecutionAuthorizationValue;

  disabled?: boolean;

  onChange: (
    value:
      PaidAssessmentExecutionAuthorizationValue
  ) => void;
};


function updateBoolean(
  value:
    PaidAssessmentExecutionAuthorizationValue,
  key:
    keyof PaidAssessmentExecutionAuthorizationValue,
  checked: boolean
): PaidAssessmentExecutionAuthorizationValue {
  return {
    ...value,
    [key]: checked
  };
}


export function
PaidAssessmentExecutionAuthorization({
  binding,
  value,
  disabled = false,
  onChange
}: PaidAssessmentExecutionAuthorizationProps) {
  return (
    <section
      className="form-section"
      aria-labelledby="paid-execution-authorization-title"
    >
      <div className="form-section-heading">
        <p className="panel-kicker">
          Governed execution boundary
        </p>

        <h2 id="paid-execution-authorization-title">
          Paid Assessment Execution Authorization
        </h2>

        <p>
          Review the server-bound assessment
          commitment and explicitly confirm the
          human-controlled conditions required
          before governed execution.
        </p>
      </div>

      {!binding && (
        <div
          className="error-panel"
          role="status"
        >
          <div>
            <p className="error-title">
              Execution binding unavailable
            </p>

            <p>
              The assessment cannot be authorized
              for paid execution until its
              immutable server-side execution
              binding is available.
            </p>
          </div>
        </div>
      )}

      {binding && (
        <>
          <dl className="assessment-workflow-identity">
            <div>
              <dt>Assessment</dt>
              <dd>
                {binding.assessment_name}
              </dd>
            </div>

            <div>
              <dt>Client</dt>
              <dd>
                {binding.client_display_name}
              </dd>
            </div>

            <div>
              <dt>Binding</dt>
              <dd>
                {binding.binding_hash}
              </dd>
            </div>
          </dl>

          <div className="form-grid">
            <label>
              <span>
                Operator name
              </span>

              <input
                type="text"
                value={value.operatorName}
                disabled={disabled}
                onChange={(event) =>
                  onChange({
                    ...value,
                    operatorName:
                      event.target.value
                  })
                }
              />
            </label>

            <label>
              <span>
                Client contact
              </span>

              <input
                type="text"
                value={
                  value.clientContactName
                }
                disabled={disabled}
                onChange={(event) =>
                  onChange({
                    ...value,
                    clientContactName:
                      event.target.value
                  })
                }
              />
            </label>

            <label className="form-span-full">
              <span>
                Evidence classification
              </span>

              <input
                type="text"
                value={value.classification}
                disabled={disabled}
                onChange={(event) =>
                  onChange({
                    ...value,
                    classification:
                      event.target.value
                  })
                }
              />
            </label>
          </div>

          <div className="paid-execution-confirmations">
            <h3>
              Assessment scope
            </h3>

            <label>
              <input
                type="checkbox"
                checked={
                  value.assessmentScopeConfirmed
                }
                disabled={disabled}
                onChange={(event) =>
                  onChange(
                    updateBoolean(
                      value,
                      "assessmentScopeConfirmed",
                      event.target.checked
                    )
                  )
                }
              />

              Assessment scope has been reviewed
              and confirmed.
            </label>

            <label>
              <input
                type="checkbox"
                checked={
                  value.evidenceScopeConfirmed
                }
                disabled={disabled}
                onChange={(event) =>
                  onChange(
                    updateBoolean(
                      value,
                      "evidenceScopeConfirmed",
                      event.target.checked
                    )
                  )
                }
              />

              Evidence scope has been reviewed
              and confirmed.
            </label>

            <label>
              <input
                type="checkbox"
                checked={
                  value.clientDataUseConfirmed
                }
                disabled={disabled}
                onChange={(event) =>
                  onChange(
                    updateBoolean(
                      value,
                      "clientDataUseConfirmed",
                      event.target.checked
                    )
                  )
                }
              />

              Client data use has been confirmed.
            </label>

            <label>
              <input
                type="checkbox"
                checked={
                  value.operatorReadinessConfirmed
                }
                disabled={disabled}
                onChange={(event) =>
                  onChange(
                    updateBoolean(
                      value,
                      "operatorReadinessConfirmed",
                      event.target.checked
                    )
                  )
                }
              />

              Operator readiness has been
              confirmed.
            </label>
          </div>

          <div className="paid-execution-confirmations">
            <h3>
              Evidence approval
            </h3>

            {binding.evidence.map(
              (item) => (
                <article
                  key={item.evidence_id}
                  className="paid-execution-evidence"
                >
                  <strong>
                    {item.display_name}
                  </strong>

                  <span>
                    {item.source_kind}
                  </span>

                  <code>
                    {item.content_sha256}
                  </code>
                </article>
              )
            )}

            <label>
              <input
                type="checkbox"
                checked={
                  value.clientAuthorizedForAssessment
                }
                disabled={disabled}
                onChange={(event) =>
                  onChange(
                    updateBoolean(
                      value,
                      "clientAuthorizedForAssessment",
                      event.target.checked
                    )
                  )
                }
              />

              Client authorization covers this
              evidence for the assessment.
            </label>

            <label>
              <input
                type="checkbox"
                checked={
                  value.minimizationReviewCompleted
                }
                disabled={disabled}
                onChange={(event) =>
                  onChange(
                    updateBoolean(
                      value,
                      "minimizationReviewCompleted",
                      event.target.checked
                    )
                  )
                }
              />

              Evidence minimization review is
              complete.
            </label>

            <label>
              <input
                type="checkbox"
                checked={
                  value.directIdentifiersRemoved
                }
                disabled={disabled}
                onChange={(event) =>
                  onChange(
                    updateBoolean(
                      value,
                      "directIdentifiersRemoved",
                      event.target.checked
                    )
                  )
                }
              />

              Direct identifiers have been
              removed where required.
            </label>

            <label>
              <input
                type="checkbox"
                checked={
                  value.executionEvidenceApproved
                }
                disabled={disabled}
                onChange={(event) =>
                  onChange(
                    updateBoolean(
                      value,
                      "executionEvidenceApproved",
                      event.target.checked
                    )
                  )
                }
              />

              I approve the displayed immutable
              evidence commitments for execution.
            </label>
          </div>

          <div className="paid-execution-confirmations">
            <h3>
              Storage controls
            </h3>

            {[
              [
                "operatorControlledLocation",
                "Execution storage is operator controlled."
              ],
              [
                "accessRestricted",
                "Access is restricted."
              ],
              [
                "storageProtectionConfirmed",
                "Storage protection is confirmed."
              ],
              [
                "backupPlanRecorded",
                "Backup plan is recorded."
              ],
              [
                "retentionPeriodRecorded",
                "Retention period is recorded."
              ],
              [
                "deletionPlanRecorded",
                "Deletion plan is recorded."
              ]
            ].map(
              ([key, label]) => (
                <label key={key}>
                  <input
                    type="checkbox"
                    checked={
                      Boolean(
                        value[
                          key as keyof PaidAssessmentExecutionAuthorizationValue
                        ]
                      )
                    }
                    disabled={disabled}
                    onChange={(event) =>
                      onChange(
                        updateBoolean(
                          value,
                          key as keyof PaidAssessmentExecutionAuthorizationValue,
                          event.target.checked
                        )
                      )
                    }
                  />

                  {label}
                </label>
              )
            )}
          </div>

          <div className="paid-execution-confirmations">
            <h3>
              Contract execution
            </h3>

            {[
              [
                "contractExecuted",
                "The contract has been executed."
              ],
              [
                "contractExecutionReviewReady",
                "Contract execution is ready for review."
              ],
              [
                "contractExecutionConfirmed",
                "Contract execution has been confirmed."
              ],
              [
                "executedContractReferenceRecorded",
                "Executed contract reference is recorded."
              ],
              [
                "executedAtRecorded",
                "Execution timestamp is recorded."
              ],
              [
                "allRequiredSignaturesRecorded",
                "All required signatures are recorded."
              ],
              [
                "humanOperatorConfirmedExecution",
                "A human operator confirmed contract execution."
              ]
            ].map(
              ([key, label]) => (
                <label key={key}>
                  <input
                    type="checkbox"
                    checked={
                      Boolean(
                        value[
                          key as keyof PaidAssessmentExecutionAuthorizationValue
                        ]
                      )
                    }
                    disabled={disabled}
                    onChange={(event) =>
                      onChange(
                        updateBoolean(
                          value,
                          key as keyof PaidAssessmentExecutionAuthorizationValue,
                          event.target.checked
                        )
                      )
                    }
                  />

                  {label}
                </label>
              )
            )}
          </div>

          <div className="paid-execution-confirmations">
            <h3>
              Final paid-work authorization
            </h3>

            <label>
              <input
                type="checkbox"
                checked={
                  value.paidAssessmentAuthorized
                }
                disabled={disabled}
                onChange={(event) =>
                  onChange(
                    updateBoolean(
                      value,
                      "paidAssessmentAuthorized",
                      event.target.checked
                    )
                  )
                }
              />

              Paid assessment execution is
              explicitly authorized.
            </label>

            <p className="assessment-workflow-description">
              This form records operator
              attestations. It does not itself
              grant execution authority; the
              governed backend remains
              authoritative.
            </p>
          </div>
        </>
      )}
    </section>
  );
}