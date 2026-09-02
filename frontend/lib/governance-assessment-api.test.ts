import {
  afterEach,
  describe,
  expect,
  it,
  vi
} from "vitest";

import {
  executePaidAssessment,
  fetchPaidAssessmentExecutionInputBinding,
  GovernanceAssessmentApiError,
  type CommercialPaidAssessmentExecutionRequest,
  type CommercialPaidAssessmentExecutionResponse,
  type GovernanceAssessmentApiConfig
} from "./governance-assessment-api";


const CONFIG: GovernanceAssessmentApiConfig = {
  baseUrl: "http://127.0.0.1:8000",
  tenantId: "tenant-alpha",
  actorId: "console-admin",
  actorRoles: "assessment:admin"
};


const IDENTITY = {
  tenantId: "tenant-alpha",
  clientId: "client-001",
  engagementId: "engagement-001",
  assessmentId: "assessment-001"
};


const REQUEST:
  CommercialPaidAssessmentExecutionRequest = {
    intake: {
      tenant_id: "tenant-alpha",
      client_id: "client-001",
      engagement_id: "engagement-001",
      assessment_id: "assessment-001",
      client_display_name:
        "Synthetic Test Organization",
      assessment_name:
        "FIP Governance Assessment",
      operator_name: "FIP Operator",
      client_contact_name: "Client Contact",
      assessment_scope_confirmed: true,
      evidence_scope_confirmed: true,
      client_data_use_confirmed: true,
      operator_readiness_confirmed: true,
      evidence: [
        {
          evidence_id: "evidence-001",
          source_kind: "csv",
          description:
            "Governance workflow telemetry",
          classification: "non_sensitive",
          client_authorized_for_assessment: true,
          minimization_review_completed: true,
          direct_identifiers_removed: true
        }
      ],
      storage: {
        operator_controlled_location: true,
        access_restricted: true,
        storage_protection_confirmed: true,
        backup_plan_recorded: true,
        retention_period_recorded: true,
        deletion_plan_recorded: true
      }
    },
    contract_execution_event: {
      contract_execution_event_id:
        "contract-event-001",
      contract_executed: true,
      contract_execution_review_ready: true,
      contract_execution_confirmed: true,
      executed_contract_reference_recorded: true,
      executed_at_recorded: true,
      all_required_signatures_recorded: true,
      human_operator_confirmed_execution: true,
      requires_final_paid_work_authorization: true,
      human_boundary_required: true,
      gagf_kernel_authoritative: true,
      ai_override_allowed: false
    },
    paid_work_authorization: {
      authorization_id: "authorization-001",
      tenant_id: "tenant-alpha",
      client_id: "client-001",
      engagement_id: "engagement-001",
      assessment_id: "assessment-001",
      contract_execution_event_id:
        "contract-event-001",
      authorized_by: "Authorized Operator",
      authorized_at:
        "2026-08-30T20:00:00+00:00",
      paid_assessment_authorized: true
    },
    execution_evidence_approvals: [
      {
        evidence_id: "evidence-001",
        approved_content_sha256:
          "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
        approved_by: "Evidence Approver",
        approved_at:
          "2026-08-30T20:01:00+00:00",
        execution_evidence_approved: true
      }
    ]
  };


function buildBindingResponse() {
  return {
    hierarchy_key:
      "tenant-alpha/client-001/engagement-001/assessment-001",
    assessment_name:
      "FIP Governance Assessment",
    client_display_name:
      "Synthetic Test Organization",
    assessment_execution_request_hash:
      "request-hash-001",
    execution_input_hash:
      "execution-input-hash-001",
    binding_hash:
      "binding-hash-001",
    schema_version:
      "1.2.0",
    evidence: [
      {
        evidence_id:
          "evidence-001",
        source_id:
          "evidence-001",
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
}


function buildResponse(
  disposition:
    | "executed"
    | "resumed"
    | "reconciled"
): CommercialPaidAssessmentExecutionResponse {
  const hierarchyKey =
    "tenant-alpha/client-001/engagement-001/assessment-001";

  return {
    operator_run_passed: true,
    result: {
      recovery_type:
        "governance-real-paid-assessment-execution-recovery",
      recovery_version: "1.0.0",
      schema_version: "1.0",
      attempt_hash: "attempt-hash-001",
      record_hash: "record-hash-001",
      hierarchy_key: hierarchyKey,
      disposition,
      artifact_count_before:
        disposition === "executed"
          ? 0
          : 10,
      artifact_count_after: 10,
      execution_result: {
        completed: true
      },
      boundaries: {
        recovery_is_not_second_execution_authority:
          true
      }
    },
    execution_input_binding: {
      hierarchy_key: hierarchyKey,
      assessment_execution_request_hash:
        "request-hash-001",
      execution_input_hash:
        "execution-input-hash-001",
      binding_hash:
        "binding-hash-001",
      schema_version: "1.2.0"
    },
    boundaries: {
      api_request_is_not_paid_work_authorization:
        true,
      api_request_is_not_execution_authority:
        true,
      api_request_is_not_recovery_authority:
        true,
      assessment_execution_request_is_server_bound:
        true,
      raw_execution_evidence_is_not_browser_resubmitted:
        true,
      browser_cannot_replace_bound_execution_input:
        true,
      repository_path_is_server_assigned:
        true,
      execution_database_is_hierarchy_scoped:
        true,
      recovery_service_remains_governed_authority_path:
        true
    }
  };
}


function mockFetchJson(
  payload: unknown,
  status = 200
) {
  const fetchMock = vi.fn().mockResolvedValue(
    new Response(
      JSON.stringify(payload),
      {
        status,
        headers: {
          "Content-Type": "application/json"
        }
      }
    )
  );

  vi.stubGlobal(
    "fetch",
    fetchMock
  );

  return fetchMock;
}


afterEach(() => {
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
});


describe(
  "fetchPaidAssessmentExecutionInputBinding",
  () => {
    it(
      "loads safe server-bound execution metadata",
      async () => {
        const fetchMock =
          mockFetchJson(
            buildBindingResponse(),
            200
          );

        const result =
          await fetchPaidAssessmentExecutionInputBinding(
            CONFIG,
            IDENTITY
          );

        expect(
          fetchMock
        ).toHaveBeenCalledTimes(
          1
        );

        const [
          url,
          options
        ] =
          fetchMock.mock.calls[0];

        expect(
          String(url)
        ).toBe(
          "http://127.0.0.1:8000/api/v1/governance-paid-assessments/tenant-alpha/client-001/engagement-001/assessment-001/execution-input-binding"
        );

        expect(
          options
        ).toEqual(
          expect.objectContaining({
            method: "GET",
            cache: "no-store"
          })
        );

        expect(
          result.hierarchy_key
        ).toBe(
          "tenant-alpha/client-001/engagement-001/assessment-001"
        );

        expect(
          result.evidence[0]
            .content_sha256
        ).toBe(
          "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
        );
      }
    );

    it(
      "sends assessment actor authentication headers",
      async () => {
        const fetchMock =
          mockFetchJson(
            buildBindingResponse(),
            200
          );

        await fetchPaidAssessmentExecutionInputBinding(
          CONFIG,
          IDENTITY
        );

        const options =
          fetchMock.mock.calls[0][1];

        expect(
          options.headers
        ).toEqual({
          "X-Tenant-ID":
            "tenant-alpha",
          "X-Actor-ID":
            "console-admin",
          "X-Actor-Roles":
            "assessment:admin"
        });
      }
    );

    it(
      "does not receive raw evidence",
      async () => {
        mockFetchJson(
          buildBindingResponse(),
          200
        );

        const result =
          await fetchPaidAssessmentExecutionInputBinding(
            CONFIG,
            IDENTITY
          );

        const serialized =
          JSON.stringify(result);

        expect(
          serialized
        ).not.toContain(
          "csv_text"
        );

        expect(
          serialized
        ).not.toContain(
          "assessment_execution_request_payload"
        );

        expect(
          serialized
        ).not.toContain(
          "assessment_execution_request_material"
        );
      }
    );

    it(
      "rejects a hierarchy mismatch",
      async () => {
        const payload =
          buildBindingResponse();

        payload.hierarchy_key =
          "tenant-alpha/client-001/engagement-001/wrong-assessment";

        mockFetchJson(
          payload,
          200
        );

        await expect(
          fetchPaidAssessmentExecutionInputBinding(
            CONFIG,
            IDENTITY
          )
        ).rejects.toEqual(
          expect.objectContaining({
            name:
              "GovernanceAssessmentApiError",
            message:
              "Paid assessment execution-input binding hierarchy did not match the requested assessment",
            status: 200
          })
        );
      }
    );

    it(
      "rejects invalid evidence commitment metadata",
      async () => {
        const payload =
          buildBindingResponse();

        const invalidPayload =
          payload as unknown as {
            evidence: Array<
              Record<
                string,
                unknown
              >
            >;
          };

        delete invalidPayload
          .evidence[0]
          .content_sha256;

        mockFetchJson(
          invalidPayload,
          200
        );

        await expect(
          fetchPaidAssessmentExecutionInputBinding(
            CONFIG,
            IDENTITY
          )
        ).rejects.toEqual(
          expect.objectContaining({
            name:
              "GovernanceAssessmentApiError",
            message:
              "Paid assessment execution-input binding evidence did not match the expected contract",
            status: 200
          })
        );
      }
    );

    it(
      "rejects missing non-authority boundaries",
      async () => {
        const payload =
          buildBindingResponse();

        payload.boundaries
          .raw_evidence_not_exposed =
          false;

        mockFetchJson(
          payload,
          200
        );

        await expect(
          fetchPaidAssessmentExecutionInputBinding(
            CONFIG,
            IDENTITY
          )
        ).rejects.toEqual(
          expect.objectContaining({
            name:
              "GovernanceAssessmentApiError",
            message:
              "Paid assessment execution-input binding boundaries did not match the expected contract",
            status: 200
          })
        );
      }
    );

    it(
      "preserves backend binding errors",
      async () => {
        const payload = {
          detail: {
            code:
              "COMMERCIAL_PAID_ASSESSMENT_EXECUTION_INPUT_BINDING_ERROR",
            message:
              "binding database does not exist"
          }
        };

        mockFetchJson(
          payload,
          409
        );

        let captured:
          GovernanceAssessmentApiError | null =
            null;

        try {
          await fetchPaidAssessmentExecutionInputBinding(
            CONFIG,
            IDENTITY
          );
        } catch (error) {
          if (
            error instanceof
            GovernanceAssessmentApiError
          ) {
            captured =
              error;
          } else {
            throw error;
          }
        }

        expect(
          captured
        ).not.toBeNull();

        expect(
          captured?.status
        ).toBe(
          409
        );

        expect(
          captured?.payload
        ).toEqual(
          payload
        );
      }
    );
  }
);


describe(
  "executePaidAssessment",
  () => {
    it(
      "posts to the governed paid-assessment endpoint",
      async () => {
        const fetchMock = mockFetchJson(
          buildResponse("executed"),
          201
        );

        await executePaidAssessment(
          CONFIG,
          REQUEST
        );

        expect(
          fetchMock
        ).toHaveBeenCalledTimes(
          1
        );

        const [
          url,
          options
        ] = fetchMock.mock.calls[0];

        expect(
          String(url)
        ).toBe(
          "http://127.0.0.1:8000/api/v1/governance-paid-assessments/execute"
        );

        expect(
          options
        ).toEqual(
          expect.objectContaining({
            method: "POST",
            cache: "no-store"
          })
        );
      }
    );

    it(
      "sends the assessment actor authentication headers",
      async () => {
        const fetchMock = mockFetchJson(
          buildResponse("executed"),
          201
        );

        await executePaidAssessment(
          CONFIG,
          REQUEST
        );

        const options =
          fetchMock.mock.calls[0][1];

        expect(
          options.headers
        ).toEqual({
          "Content-Type":
            "application/json",
          "X-Tenant-ID":
            "tenant-alpha",
          "X-Actor-ID":
            "console-admin",
          "X-Actor-Roles":
            "assessment:admin"
        });
      }
    );

    it(
      "sends only the governed commercial request",
      async () => {
        const fetchMock = mockFetchJson(
          buildResponse("executed"),
          201
        );

        await executePaidAssessment(
          CONFIG,
          REQUEST
        );

        const options =
          fetchMock.mock.calls[0][1];

        expect(
          typeof options.body
        ).toBe(
          "string"
        );

        const body = JSON.parse(
          options.body as string
        ) as Record<
          string,
          unknown
        >;

        expect(
          body
        ).toEqual(
          REQUEST
        );

        expect(
          body
        ).not.toHaveProperty(
          "assessment_execution_request"
        );

        const intake =
          body.intake as {
            storage:
              Record<string, unknown>;
          };

        expect(
          intake.storage
        ).not.toHaveProperty(
          "repository_path"
        );
      }
    );

    it(
      "accepts an executed disposition",
      async () => {
        mockFetchJson(
          buildResponse("executed"),
          201
        );

        const result =
          await executePaidAssessment(
            CONFIG,
            REQUEST
          );

        expect(
          result.operator_run_passed
        ).toBe(
          true
        );

        expect(
          result.result.disposition
        ).toBe(
          "executed"
        );

        expect(
          result.result.artifact_count_before
        ).toBe(
          0
        );

        expect(
          result.result.artifact_count_after
        ).toBe(
          10
        );
      }
    );

    it(
      "accepts a resumed disposition",
      async () => {
        mockFetchJson(
          buildResponse("resumed"),
          201
        );

        const result =
          await executePaidAssessment(
            CONFIG,
            REQUEST
          );

        expect(
          result.result.disposition
        ).toBe(
          "resumed"
        );
      }
    );

    it(
      "accepts a reconciled disposition",
      async () => {
        mockFetchJson(
          buildResponse("reconciled"),
          201
        );

        const result =
          await executePaidAssessment(
            CONFIG,
            REQUEST
          );

        expect(
          result.result.disposition
        ).toBe(
          "reconciled"
        );

        expect(
          result.result.artifact_count_before
        ).toBe(
          10
        );

        expect(
          result.result.artifact_count_after
        ).toBe(
          10
        );
      }
    );

    it(
      "returns the server-side execution input binding receipt",
      async () => {
        mockFetchJson(
          buildResponse("executed"),
          201
        );

        const result =
          await executePaidAssessment(
            CONFIG,
            REQUEST
          );

        expect(
          result.execution_input_binding
            .hierarchy_key
        ).toBe(
          result.result.hierarchy_key
        );

        expect(
          result.execution_input_binding
            .assessment_execution_request_hash
        ).toBe(
          "request-hash-001"
        );

        expect(
          result.execution_input_binding
            .execution_input_hash
        ).toBe(
          "execution-input-hash-001"
        );

        expect(
          result.execution_input_binding
            .binding_hash
        ).toBe(
          "binding-hash-001"
        );
      }
    );

    it(
      "preserves governed backend errors",
      async () => {
        const payload = {
          detail: {
            code:
              "COMMERCIAL_PAID_ASSESSMENT_EXECUTION_ERROR",
            message:
              "paid assessment authorization is not valid"
          }
        };

        mockFetchJson(
          payload,
          422
        );

        let captured:
          GovernanceAssessmentApiError | null =
            null;

        try {
          await executePaidAssessment(
            CONFIG,
            REQUEST
          );
        } catch (error) {
          if (
            error instanceof
            GovernanceAssessmentApiError
          ) {
            captured = error;
          } else {
            throw error;
          }
        }

        expect(
          captured
        ).not.toBeNull();

        expect(
          captured?.status
        ).toBe(
          422
        );

        expect(
          captured?.payload
        ).toEqual(
          payload
        );
      }
    );

    it(
      "rejects an invalid top-level response contract",
      async () => {
        mockFetchJson(
          {
            operator_run_passed: false,
            result: {}
          },
          201
        );

        await expect(
          executePaidAssessment(
            CONFIG,
            REQUEST
          )
        ).rejects.toEqual(
          expect.objectContaining({
            name:
              "GovernanceAssessmentApiError",
            message:
              "Paid assessment execution response did not match the expected contract",
            status: 201
          })
        );
      }
    );

    it(
      "rejects an invalid governed result disposition",
      async () => {
        const payload = buildResponse(
          "executed"
        ) as unknown as {
          operator_run_passed: true;
          result:
            Record<string, unknown>;
        };

        payload.result.disposition =
          "duplicated";

        mockFetchJson(
          payload,
          201
        );

        await expect(
          executePaidAssessment(
            CONFIG,
            REQUEST
          )
        ).rejects.toEqual(
          expect.objectContaining({
            name:
              "GovernanceAssessmentApiError",
            message:
              "Paid assessment execution result did not match the expected contract",
            status: 201
          })
        );
      }
    );

    it(
      "rejects a missing execution input binding receipt",
      async () => {
        const payload =
          buildResponse(
            "executed"
          ) as unknown as Record<
            string,
            unknown
          >;

        delete payload[
          "execution_input_binding"
        ];

        mockFetchJson(
          payload,
          201
        );

        await expect(
          executePaidAssessment(
            CONFIG,
            REQUEST
          )
        ).rejects.toEqual(
          expect.objectContaining({
            name:
              "GovernanceAssessmentApiError",
            message:
              "Paid assessment execution binding did not match the expected contract",
            status: 201
          })
        );
      }
    );

    it(
      "rejects a binding hierarchy mismatch",
      async () => {
        const payload =
          buildResponse(
            "executed"
          );

        payload
          .execution_input_binding
          .hierarchy_key =
          "tenant-alpha/client-001/engagement-001/other-assessment";

        mockFetchJson(
          payload,
          201
        );

        await expect(
          executePaidAssessment(
            CONFIG,
            REQUEST
          )
        ).rejects.toEqual(
          expect.objectContaining({
            name:
              "GovernanceAssessmentApiError",
            message:
              "Paid assessment execution binding did not match the expected contract",
            status: 201
          })
        );
      }
    );

    it(
      "rejects missing server-boundary confirmation",
      async () => {
        const payload =
          buildResponse(
            "executed"
          );

        payload
          .boundaries
          .assessment_execution_request_is_server_bound =
          false;

        mockFetchJson(
          payload,
          201
        );

        await expect(
          executePaidAssessment(
            CONFIG,
            REQUEST
          )
        ).rejects.toEqual(
          expect.objectContaining({
            name:
              "GovernanceAssessmentApiError",
            message:
              "Paid assessment execution boundaries did not match the expected contract",
            status: 201
          })
        );
      }
    );
  }
);