import {
  afterEach,
  describe,
  expect,
  it,
  vi
} from "vitest";

import {
  fetchPaidAssessmentExecutionStatus,
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

const safeBoundaries = {
  status_is_read_only: true,
  status_is_not_execution_authority: true,
  status_is_not_recovery_authority: true,
  raw_execution_evidence_not_exposed: true,
  browser_cannot_select_execution_repository: true
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

afterEach(() => {
  vi.unstubAllGlobals();
});


describe(
  "fetchPaidAssessmentExecutionStatus",
  () => {
    it(
      "returns safe missing status",
      async () => {
        const fetchMock =
          vi.fn().mockResolvedValue(
            jsonResponse({
              found: false,
              hierarchy_key:
                hierarchyKey,
              status: null,
              boundaries:
                safeBoundaries
            })
          );

        vi.stubGlobal(
          "fetch",
          fetchMock
        );

        const result =
          await fetchPaidAssessmentExecutionStatus(
            config,
            identity
          );

        expect(
          result.found
        ).toBe(false);

        expect(
          result.status
        ).toBeNull();

        expect(
          result.hierarchy_key
        ).toBe(hierarchyKey);

        expect(
          fetchMock
        ).toHaveBeenCalledTimes(1);

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
            + "execution-status"
          )
        );
      }
    );

    it(
      "restores governed disposition",
      async () => {
        vi.stubGlobal(
          "fetch",
          vi.fn().mockResolvedValue(
            jsonResponse({
              found: true,
              hierarchy_key:
                hierarchyKey,
              status: {
                disposition:
                  "reconciled",
                artifact_count_before:
                  10,
                artifact_count_after:
                  10,
                attempt_hash:
                  "attempt-001",
                attempt_record_hash:
                  "record-001",
                assessment_execution_request_hash:
                  "request-001",
                execution_input_binding_hash:
                  "binding-001",
                status_recorded_at:
                  "2026-09-02T02:30:00+00:00",
                schema_version:
                  "1.0.0"
              },
              boundaries:
                safeBoundaries
            })
          )
        );

        const result =
          await fetchPaidAssessmentExecutionStatus(
            config,
            identity
          );

        expect(
          result.found
        ).toBe(true);

        expect(
          result.status
            ?.disposition
        ).toBe(
          "reconciled"
        );

        expect(
          result.status
            ?.artifact_count_after
        ).toBe(10);
      }
    );

    it(
      "rejects hierarchy mismatch",
      async () => {
        vi.stubGlobal(
          "fetch",
          vi.fn().mockResolvedValue(
            jsonResponse({
              found: false,
              hierarchy_key:
                "wrong/hierarchy/key/value",
              status: null,
              boundaries:
                safeBoundaries
            })
          )
        );

        await expect(
          fetchPaidAssessmentExecutionStatus(
            config,
            identity
          )
        ).rejects.toThrow(
          "hierarchy mismatch"
        );
      }
    );

    it(
      "rejects invalid disposition",
      async () => {
        vi.stubGlobal(
          "fetch",
          vi.fn().mockResolvedValue(
            jsonResponse({
              found: true,
              hierarchy_key:
                hierarchyKey,
              status: {
                disposition:
                  "complete",
                artifact_count_before:
                  0,
                artifact_count_after:
                  10,
                attempt_hash:
                  "attempt-001",
                attempt_record_hash:
                  "record-001",
                assessment_execution_request_hash:
                  "request-001",
                execution_input_binding_hash:
                  "binding-001",
                status_recorded_at:
                  "2026-09-02T02:30:00+00:00",
                schema_version:
                  "1.0.0"
              },
              boundaries:
                safeBoundaries
            })
          )
        );

        await expect(
          fetchPaidAssessmentExecutionStatus(
            config,
            identity
          )
        ).rejects.toThrow(
          "disposition is invalid"
        );
      }
    );

    it(
      "rejects missing safety boundary",
      async () => {
        vi.stubGlobal(
          "fetch",
          vi.fn().mockResolvedValue(
            jsonResponse({
              found: false,
              hierarchy_key:
                hierarchyKey,
              status: null,
              boundaries: {
                ...safeBoundaries,
                status_is_not_execution_authority:
                  false
              }
            })
          )
        );

        await expect(
          fetchPaidAssessmentExecutionStatus(
            config,
            identity
          )
        ).rejects.toThrow(
          "status_is_not_execution_authority"
        );
      }
    );

    it(
      "preserves backend API failure",
      async () => {
        vi.stubGlobal(
          "fetch",
          vi.fn().mockResolvedValue(
            jsonResponse(
              {
                detail: {
                  code:
                    "COMMERCIAL_PAID_ASSESSMENT_EXECUTION_STATUS_ERROR",
                  message:
                    "status verification failed"
                }
              },
              409
            )
          )
        );

        try {
          await fetchPaidAssessmentExecutionStatus(
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