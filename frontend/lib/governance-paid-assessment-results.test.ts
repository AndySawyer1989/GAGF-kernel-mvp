import {
  afterEach,
  describe,
  expect,
  it,
  vi
} from "vitest";

import {
  fetchPaidAssessmentResults,
  GovernanceAssessmentApiError,
  type GovernanceAssessmentApiConfig,
  type GovernanceAssessmentIdentity
} from "./governance-assessment-api";


const config:
  GovernanceAssessmentApiConfig = {
    baseUrl: "http://localhost:8000",
    tenantId: "tenant-001",
    actorId: "operator-001",
    actorRoles: "assessment_operator"
  };

const identity:
  GovernanceAssessmentIdentity = {
    tenantId: "tenant-001",
    clientId: "client-001",
    engagementId: "engagement-001",
    assessmentId: "assessment-001"
  };

const hierarchyKey =
  "tenant-001/"
  + "client-001/"
  + "engagement-001/"
  + "assessment-001";

const inventoryTypes = [
  "scope-configuration",
  "evidence-intake-batch",
  "evidence-quality",
  "friction-summary",
  "governance-debt-score",
  "intervention-plan",
  "assessment-roadmap",
  "executive-projection",
  "client-report-package",
  "demonstration-manifest"
];

const resultTypes =
  inventoryTypes.slice(2);

const safeBoundaries = {
  read_model_is_read_only: true,
  read_model_is_not_execution_authority: true,
  read_model_is_not_recovery_authority: true,
  read_model_is_not_delivery_approval: true,
  repository_path_not_exposed: true,
  raw_evidence_payloads_not_exposed: true,
  evidence_intake_payload_not_exposed: true,
  scope_configuration_payload_not_exposed: true,
  result_payloads_are_canonical_paid_artifacts: true
};

function jsonResponse(
  payload: unknown,
  status = 200
): Response {
  return new Response(
    JSON.stringify(payload),
    {
      status,
      headers: {
        "Content-Type":
          "application/json"
      }
    }
  );
}

function safePayload() {
  return {
    read_model_type:
      "governance-commercial-paid-assessment-results-read-model",
    version: "0.1.0",
    schema_version: "1.0.0",
    tenant_id: "tenant-001",
    client_id: "client-001",
    engagement_id: "engagement-001",
    assessment_id: "assessment-001",
    assessment_name:
      "Governance Health Assessment",
    hierarchy_key:
      hierarchyKey,
    execution_disposition:
      "executed",
    execution_status_hash:
      "status-hash-001",
    execution_input_binding_hash:
      "binding-hash-001",
    assessment_execution_request_hash:
      "request-hash-001",
    artifact_count: 10,
    repository_chain_valid:
      true,
    artifact_inventory:
      inventoryTypes.map(
        (artifactType, index) => ({
          artifact_id:
            `artifact-${index + 1}`,
          artifact_type:
            artifactType,
          artifact_hash:
            `artifact-hash-${index + 1}`,
          sequence_number:
            index + 1,
          chain_hash:
            `chain-hash-${index + 1}`,
          schema_version:
            "1.0.0"
        })
      ),
    result_artifacts:
      resultTypes.map(
        (artifactType, index) => ({
          artifact_id:
            `artifact-${index + 3}`,
          artifact_type:
            artifactType,
          artifact_hash:
            `artifact-hash-${index + 3}`,
          payload: {
            artifact_type:
              artifactType
          },
          created_at:
            "2026-09-02T12:00:00+00:00",
          sequence_number:
            index + 3,
          previous_artifact_hash:
            `artifact-hash-${index + 2}`,
          chain_hash:
            `chain-hash-${index + 3}`,
          schema_version:
            "1.0.0"
        })
      ),
    boundaries:
      safeBoundaries
  };
}

afterEach(() => {
  vi.unstubAllGlobals();
});


describe(
  "fetchPaidAssessmentResults",
  () => {
    it(
      "returns validated governed paid results",
      async () => {
        const fetchMock =
          vi.fn().mockResolvedValue(
            jsonResponse(
              safePayload()
            )
          );

        vi.stubGlobal(
          "fetch",
          fetchMock
        );

        const result =
          await fetchPaidAssessmentResults(
            config,
            identity
          );

        expect(
          result.hierarchy_key
        ).toBe(
          hierarchyKey
        );

        expect(
          result.artifact_count
        ).toBe(10);

        expect(
          result.repository_chain_valid
        ).toBe(true);

        expect(
          result.result_artifacts
        ).toHaveLength(8);

        expect(
          result.result_artifacts[0]
            .artifact_type
        ).toBe(
          "evidence-quality"
        );

        expect(
          result.result_artifacts[7]
            .artifact_type
        ).toBe(
          "demonstration-manifest"
        );

        const requestUrl =
          String(
            fetchMock.mock.calls[0][0]
          );

        expect(
          requestUrl
        ).toContain(
          (
            "/api/v1/"
            + "governance-paid-assessments/"
            + "tenant-001/"
            + "client-001/"
            + "engagement-001/"
            + "assessment-001/"
            + "results"
          )
        );
      }
    );

    it(
      "rejects hierarchy mismatch",
      async () => {
        const payload =
          safePayload();

        payload.hierarchy_key =
          "wrong/client/path/value";

        vi.stubGlobal(
          "fetch",
          vi.fn().mockResolvedValue(
            jsonResponse(payload)
          )
        );

        await expect(
          fetchPaidAssessmentResults(
            config,
            identity
          )
        ).rejects.toThrow(
          "hierarchy mismatch"
        );
      }
    );

    it(
      "rejects invalid artifact count",
      async () => {
        const payload =
          safePayload();

        payload.artifact_count =
          9;

        vi.stubGlobal(
          "fetch",
          vi.fn().mockResolvedValue(
            jsonResponse(payload)
          )
        );

        await expect(
          fetchPaidAssessmentResults(
            config,
            identity
          )
        ).rejects.toThrow(
          "artifact count is invalid"
        );
      }
    );

    it(
      "rejects invalid canonical inventory order",
      async () => {
        const payload =
          safePayload();

        const first =
          payload.artifact_inventory[0];

        payload.artifact_inventory[0] =
          payload.artifact_inventory[1];

        payload.artifact_inventory[1] =
          first;

        vi.stubGlobal(
          "fetch",
          vi.fn().mockResolvedValue(
            jsonResponse(payload)
          )
        );

        await expect(
          fetchPaidAssessmentResults(
            config,
            identity
          )
        ).rejects.toThrow(
          "inventory order is invalid"
        );
      }
    );

    it(
      "rejects raw evidence artifact in result projection",
      async () => {
        const payload =
          safePayload();

        payload.result_artifacts[0]
          .artifact_type =
          "evidence-intake-batch";

        vi.stubGlobal(
          "fetch",
          vi.fn().mockResolvedValue(
            jsonResponse(payload)
          )
        );

        await expect(
          fetchPaidAssessmentResults(
            config,
            identity
          )
        ).rejects.toThrow(
          "result artifact order is invalid"
        );
      }
    );

    it(
      "rejects missing safety boundary",
      async () => {
        const payload =
          safePayload();

        payload.boundaries
          .raw_evidence_payloads_not_exposed =
          false;

        vi.stubGlobal(
          "fetch",
          vi.fn().mockResolvedValue(
            jsonResponse(payload)
          )
        );

        await expect(
          fetchPaidAssessmentResults(
            config,
            identity
          )
        ).rejects.toThrow(
          "raw_evidence_payloads_not_exposed"
        );
      }
    );

    it(
      "preserves backend read-model failure",
      async () => {
        vi.stubGlobal(
          "fetch",
          vi.fn().mockResolvedValue(
            jsonResponse(
              {
                detail: {
                  code:
                    "COMMERCIAL_PAID_ASSESSMENT_RESULTS_READ_MODEL_ERROR",
                  message:
                    "canonical artifact chain is invalid"
                }
              },
              409
            )
          )
        );

        try {
          await fetchPaidAssessmentResults(
            config,
            identity
          );

          throw new Error(
            "expected API failure"
          );
        } catch (caught) {
          expect(
            caught
          ).toBeInstanceOf(
            GovernanceAssessmentApiError
          );

          expect(
            (
              caught as
                GovernanceAssessmentApiError
            ).status
          ).toBe(409);
        }
      }
    );
  }
);
