import {
  afterEach,
  describe,
  expect,
  it,
  vi
} from "vitest";

import {
  GovernanceAssessmentApiError
} from "./governance-assessment-api";

import {
  approvePaidAssessmentDelivery,
  fetchPaidAssessmentDeliveryStatus,
  projectPaidAssessmentRecordedDelivery,
  fetchPaidAssessmentDeliveryReadiness,
  fetchPaidAssessmentLifecycleStatus,
  recordPaidAssessmentClientAcknowledgment,
  recordPaidAssessmentClientResponse,
  recordPaidAssessmentDelivery,
  type PaidAssessmentClientAcknowledgmentRequest,
  type PaidAssessmentClientResponseRequest,
  type PaidAssessmentDeliveryApprovalRequest,
  type PaidAssessmentDeliveryRecordingRequest,
  type PaidAssessmentHierarchy
} from "./governance-paid-assessment-delivery-api";


const CONFIG = {
  baseUrl: "http://127.0.0.1:8000",
  tenantId: "tenant-alpha",
  actorId: "console-admin",
  actorRoles: "assessment:admin"
};

const HIERARCHY: PaidAssessmentHierarchy = {
  tenantId: "tenant-alpha",
  clientId: "client-acme",
  engagementId: "engagement-001",
  assessmentId: "assessment-001"
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
        "Content-Type": "application/json"
      }
    }
  );
}


function approvalRequest():
PaidAssessmentDeliveryApprovalRequest {
  return {
    approval_id: "approval-001",
    tenant_id: "tenant-alpha",
    client_id: "client-acme",
    engagement_id: "engagement-001",
    assessment_id: "assessment-001",
    report_id: "report-001",
    approved_by: "console-admin",
    approved_at: "2026-09-02T20:00:00+00:00",
    scope_approved: true,
    evidence_boundary_approved: true,
    buyer_language_approved: true,
    delivery_approved: true
  };
}


function recordingRequest():
PaidAssessmentDeliveryRecordingRequest {
  return {
    delivery_event_id: "delivery-event-001",
    tenant_id: "tenant-alpha",
    client_id: "client-acme",
    engagement_id: "engagement-001",
    assessment_id: "assessment-001",
    report_id: "report-001",
    delivered_by: "console-admin",
    delivered_at: "2026-09-02T20:15:00+00:00",
    delivery_method: "email",
    delivery_reference: "customer-message-001",
    delivery_completed: true
  };
}


function acknowledgmentRequest():
PaidAssessmentClientAcknowledgmentRequest {
  return {
    acknowledgment_id: "client-ack-001",
    acknowledged_by: "client-representative",
    acknowledged_at: "2026-09-07T19:15:00+00:00",
    acknowledgment_method: "email_reply",
    acknowledgment_reference: "receipt-mail-001",
    client_acknowledged_receipt: true
  };
}


function clientResponseRequest():
PaidAssessmentClientResponseRequest {
  return {
    response_id: "client-response-001",
    responded_by: "client-representative",
    responded_at: "2026-09-07T19:30:00+00:00",
    response_method: "email_reply",
    response_reference: "response-mail-001",
    findings_disposition: "acknowledged",
    recommendations_disposition: "accepted",
    response_note:
      "Client accepts recommendations for planning review."
  };
}


function requestUrl(
  input: RequestInfo | URL
): string {
  if (input instanceof URL) {
    return input.toString();
  }

  if (typeof input === "string") {
    return input;
  }

  return input.url;
}


afterEach(() => {
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
});


describe(
  "governance paid assessment delivery api",
  () => {
    it(
      "projects governed persisted delivery into restart-safe UI state",
      () => {
        const result =
          projectPaidAssessmentRecordedDelivery({
            found: true,
            delivery_recorded: true,
            delivery_status: "delivered",
            report_id: "report-001",
            delivered_by: "operator-001",
            delivered_at:
              "2026-09-03T12:00:00Z",
            delivery_method: "email",
            delivery_reference: "message-001",
            repository_chain_valid: true
          });

        expect(result).toEqual({
          deliveredAt:
            "2026-09-03T12:00:00Z",
          deliveredBy: "operator-001"
        });
      }
    );

    it(
      "does not restore UI delivery state without governed delivery",
      () => {
        const result =
          projectPaidAssessmentRecordedDelivery({
            found: false,
            delivery_recorded: false,
            delivery_status: null,
            report_id: null,
            delivered_by: null,
            delivered_at: null,
            delivery_method: null,
            delivery_reference: null,
            repository_chain_valid: true
          });

        expect(result).toBeNull();
      }
    );

    it(
      "fetches restart-safe delivery status with governed actor headers",
      async () => {
        const fetchMock = vi.fn<
          (
            input: RequestInfo | URL,
            init?: RequestInit
          ) => Promise<Response>
        >(
          async () =>
            jsonResponse({
              found: true,
              delivery_recorded: true,
              delivery_status: "delivered",
              report_id: "report-001",
              delivered_by: "operator-001",
              delivered_at:
                "2026-09-03T12:00:00Z",
              delivery_method: "email",
              delivery_reference:
                "message-001",
              repository_chain_valid: true,
              boundaries: {
                delivery_is_not_client_receipt: true
              }
            })
        );

        vi.stubGlobal("fetch", fetchMock);

        const result =
          await fetchPaidAssessmentDeliveryStatus(
            CONFIG,
            HIERARCHY
          );

        expect(result.delivery_recorded).toBe(true);
        expect(result.delivery_status).toBe(
          "delivered"
        );
        expect(result.report_id).toBe("report-001");
        expect(result.delivered_by).toBe(
          "operator-001"
        );

        expect(fetchMock).toHaveBeenCalledTimes(1);

        const [
          input,
          init
        ] = fetchMock.mock.calls[0];

        expect(requestUrl(input)).toBe(
          (
            "http://127.0.0.1:8000/" +
            "api/v1/governance-paid-assessments/" +
            "tenant-alpha/client-acme/" +
            "engagement-001/assessment-001/" +
            "delivery-status"
          )
        );

        expect(init).toMatchObject({
          method: "GET",
          cache: "no-store",
          headers: {
            "X-Tenant-ID": "tenant-alpha",
            "X-Actor-ID": "console-admin",
            "X-Actor-Roles": "assessment:admin"
          }
        });
      }
    );

    it(
      "preserves not-recorded delivery status",
      async () => {
        const fetchMock = vi.fn<
          (
            input: RequestInfo | URL,
            init?: RequestInit
          ) => Promise<Response>
        >(
          async () =>
            jsonResponse({
              found: false,
              delivery_recorded: false,
              delivery_status: null,
              report_id: null,
              delivered_by: null,
              delivered_at: null,
              delivery_method: null,
              delivery_reference: null,
              repository_chain_valid: true,
              boundaries: {
                delivery_status_is_read_only_projection:
                  true
              }
            })
        );

        vi.stubGlobal("fetch", fetchMock);

        const result =
          await fetchPaidAssessmentDeliveryStatus(
            CONFIG,
            HIERARCHY
          );

        expect(result.found).toBe(false);
        expect(result.delivery_recorded).toBe(
          false
        );
        expect(result.delivery_status).toBeNull();
        expect(result.delivered_at).toBeNull();
        expect(result.delivered_by).toBeNull();
      }
    );

    it(
      "fetches delivery readiness with governed actor headers",
      async () => {
        const fetchMock = vi.fn<
          (
            input: RequestInfo | URL,
            init?: RequestInit
          ) => Promise<Response>
        >(
          async () =>
            jsonResponse({
              delivery_readiness_status:
                "ready_for_delivery_approval_review",
              boundaries: {
                readiness_is_not_delivery_approval:
                  true
              }
            })
        );

        vi.stubGlobal("fetch", fetchMock);

        const result =
          await fetchPaidAssessmentDeliveryReadiness(
            CONFIG,
            HIERARCHY
          );

        expect(
          result.delivery_readiness_status
        ).toBe(
          "ready_for_delivery_approval_review"
        );

        expect(fetchMock).toHaveBeenCalledTimes(1);

        const [
          input,
          init
        ] = fetchMock.mock.calls[0];

        expect(requestUrl(input)).toBe(
          (
            "http://127.0.0.1:8000/" +
            "api/v1/governance-paid-assessments/" +
            "tenant-alpha/client-acme/" +
            "engagement-001/assessment-001/" +
            "delivery-readiness"
          )
        );

        expect(init).toMatchObject({
          method: "GET",
          cache: "no-store",
          headers: {
            "X-Tenant-ID": "tenant-alpha",
            "X-Actor-ID": "console-admin",
            "X-Actor-Roles": "assessment:admin"
          }
        });
      }
    );


    it(
      "encodes hierarchy components in delivery urls",
      async () => {
        const fetchMock = vi.fn<
          (
            input: RequestInfo | URL,
            init?: RequestInit
          ) => Promise<Response>
        >(
          async () =>
            jsonResponse({
              delivery_readiness_status:
                "ready_for_delivery_approval_review"
            })
        );

        vi.stubGlobal("fetch", fetchMock);

        await fetchPaidAssessmentDeliveryReadiness(
          CONFIG,
          {
            tenantId: "tenant alpha",
            clientId: "client/acme",
            engagementId: "engagement 001",
            assessmentId: "assessment#001"
          }
        );

        const [
          input
        ] = fetchMock.mock.calls[0];

        expect(requestUrl(input)).toContain(
          (
            "tenant%20alpha/" +
            "client%2Facme/" +
            "engagement%20001/" +
            "assessment%23001/" +
            "delivery-readiness"
          )
        );
      }
    );


    it(
      "posts explicit human delivery approval",
      async () => {
        const fetchMock = vi.fn<
          (
            input: RequestInfo | URL,
            init?: RequestInit
          ) => Promise<Response>
        >(
          async () =>
            jsonResponse({
              handoff_status:
                "approved_for_human_delivery",
              approved_for_human_delivery: true,
              boundaries: {
                approved_for_human_delivery_is_not_delivery:
                  true
              }
            })
        );

        vi.stubGlobal("fetch", fetchMock);

        const request = approvalRequest();

        const result =
          await approvePaidAssessmentDelivery(
            CONFIG,
            HIERARCHY,
            request
          );

        expect(
          result.approved_for_human_delivery
        ).toBe(true);

        const [
          input,
          init
        ] = fetchMock.mock.calls[0];

        expect(requestUrl(input)).toContain(
          "/delivery-approval"
        );

        expect(init).toMatchObject({
          method: "POST",
          cache: "no-store",
          headers: {
            "Content-Type": "application/json",
            "X-Tenant-ID": "tenant-alpha",
            "X-Actor-ID": "console-admin",
            "X-Actor-Roles": "assessment:admin"
          }
        });

        expect(
          JSON.parse(
            String(init?.body)
          )
        ).toEqual(request);

        expect(
          JSON.parse(
            String(init?.body)
          ).delivery_approved
        ).toBe(true);
      }
    );


    it(
      "posts explicit human delivery confirmation",
      async () => {
        const fetchMock = vi.fn<
          (
            input: RequestInfo | URL,
            init?: RequestInit
          ) => Promise<Response>
        >(
          async () =>
            jsonResponse({
              delivery_status: "delivered",
              delivery_recorded: true,
              boundaries: {
                delivery_is_not_client_receipt: true
              }
            })
        );

        vi.stubGlobal("fetch", fetchMock);

        const request = recordingRequest();

        const result =
          await recordPaidAssessmentDelivery(
            CONFIG,
            HIERARCHY,
            request
          );

        expect(
          result.delivery_recorded
        ).toBe(true);

        const [
          input,
          init
        ] = fetchMock.mock.calls[0];

        expect(requestUrl(input)).toContain(
          "/delivery-recording"
        );

        expect(init).toMatchObject({
          method: "POST",
          cache: "no-store",
          headers: {
            "Content-Type": "application/json",
            "X-Tenant-ID": "tenant-alpha",
            "X-Actor-ID": "console-admin",
            "X-Actor-Roles": "assessment:admin"
          }
        });

        expect(
          JSON.parse(
            String(init?.body)
          )
        ).toEqual(request);

        expect(
          JSON.parse(
            String(init?.body)
          ).delivery_completed
        ).toBe(true);
      }
    );


    it(
      "preserves readiness error status and payload",
      async () => {
        const payload = {
          detail:
            "durable PA015 operator-result snapshot was not found"
        };

        vi.stubGlobal(
          "fetch",
          vi.fn(
            async () =>
              jsonResponse(
                payload,
                404
              )
          )
        );

        try {
          await fetchPaidAssessmentDeliveryReadiness(
            CONFIG,
            HIERARCHY
          );

          throw new Error(
            "expected readiness request to fail"
          );
        } catch (error) {
          expect(error).toBeInstanceOf(
            GovernanceAssessmentApiError
          );

          const apiError =
            error as GovernanceAssessmentApiError;

          expect(apiError.status).toBe(404);
          expect(apiError.payload).toEqual(
            payload
          );
          expect(apiError.message).toContain(
            "Paid assessment delivery readiness request failed"
          );
        }
      }
    );


    it(
      "preserves delivery approval conflict",
      async () => {
        const payload = {
          detail:
            "delivery_approved must be explicitly true"
        };

        vi.stubGlobal(
          "fetch",
          vi.fn(
            async () =>
              jsonResponse(
                payload,
                409
              )
          )
        );

        await expect(
          approvePaidAssessmentDelivery(
            CONFIG,
            HIERARCHY,
            approvalRequest()
          )
        ).rejects.toMatchObject({
          name: "GovernanceAssessmentApiError",
          status: 409,
          payload
        });
      }
    );


    it(
      "preserves delivery recording conflict",
      async () => {
        const payload = {
          detail:
            "approved delivery snapshot was not found"
        };

        vi.stubGlobal(
          "fetch",
          vi.fn(
            async () =>
              jsonResponse(
                payload,
                409
              )
          )
        );

        await expect(
          recordPaidAssessmentDelivery(
            CONFIG,
            HIERARCHY,
            recordingRequest()
          )
        ).rejects.toMatchObject({
          name: "GovernanceAssessmentApiError",
          status: 409,
          payload
        });
      }
    );

    it(
      "fetches restart-safe lifecycle status",
      async () => {
        const fetchMock = vi.fn<
          (
            input: RequestInfo | URL,
            init?: RequestInit
          ) => Promise<Response>
        >(
          async () =>
            jsonResponse({
              tenant_id: "tenant-alpha",
              client_id: "client-acme",
              engagement_id: "engagement-001",
              assessment_id: "assessment-001",
              hierarchy_key:
                "tenant-alpha/client-acme/engagement-001/assessment-001",
              current_stage:
                "client_receipt_acknowledged",
              pending_next_step:
                "record_client_response",
              delivery_recorded: true,
              receipt_acknowledged: true,
              client_response_recorded: false,
              report_id: "report-001",
              findings_disposition: null,
              recommendations_disposition: null,
              lifecycle_artifact_count: 2,
              repository_chain_valid: true
            })
        );

        vi.stubGlobal("fetch", fetchMock);

        const result =
          await fetchPaidAssessmentLifecycleStatus(
            CONFIG,
            HIERARCHY
          );

        expect(result.delivery_recorded).toBe(true);
        expect(result.receipt_acknowledged).toBe(true);
        expect(result.client_response_recorded).toBe(false);
        expect(result.repository_chain_valid).toBe(true);

        const [
          input,
          init
        ] = fetchMock.mock.calls[0];

        expect(requestUrl(input)).toBe(
          (
            "http://127.0.0.1:8000/" +
            "api/v1/governance-paid-assessments/" +
            "tenant-alpha/client-acme/" +
            "engagement-001/assessment-001/" +
            "lifecycle-status"
          )
        );

        expect(init).toMatchObject({
          method: "GET",
          cache: "no-store",
          headers: {
            "X-Tenant-ID": "tenant-alpha",
            "X-Actor-ID": "console-admin",
            "X-Actor-Roles": "assessment:admin"
          }
        });
      }
    );


    it(
      "posts explicit client receipt acknowledgment without lineage authority",
      async () => {
        const fetchMock = vi.fn<
          (
            input: RequestInfo | URL,
            init?: RequestInit
          ) => Promise<Response>
        >(
          async () =>
            jsonResponse({
              acknowledgment_status:
                "client_receipt_acknowledged",
              client_receipt_acknowledged: true,
              report_id: "report-001",
              acknowledgment_id:
                "client-ack-001",
              acknowledged_by:
                "client-representative",
              acknowledged_at:
                "2026-09-07T19:15:00+00:00",
              acknowledgment_method:
                "email_reply",
              acknowledgment_reference:
                "receipt-mail-001"
            })
        );

        vi.stubGlobal("fetch", fetchMock);

        const request = acknowledgmentRequest();

        const result =
          await recordPaidAssessmentClientAcknowledgment(
            CONFIG,
            HIERARCHY,
            request
          );

        expect(
          result.client_receipt_acknowledged
        ).toBe(true);

        const [
          input,
          init
        ] = fetchMock.mock.calls[0];

        expect(requestUrl(input)).toContain(
          "/client-acknowledgment"
        );

        expect(init).toMatchObject({
          method: "POST",
          cache: "no-store",
          headers: {
            "Content-Type": "application/json",
            "X-Tenant-ID": "tenant-alpha",
            "X-Actor-ID": "console-admin",
            "X-Actor-Roles": "assessment:admin"
          }
        });

        const body = JSON.parse(
          String(init?.body)
        );

        expect(body).toEqual(request);

        expect(Object.keys(body).sort()).toEqual(
          [
            "acknowledgment_id",
            "acknowledged_at",
            "acknowledged_by",
            "acknowledgment_method",
            "acknowledgment_reference",
            "client_acknowledged_receipt"
          ].sort()
        );

        expect(body.report_id).toBeUndefined();
        expect(
          body.delivery_event_hash
        ).toBeUndefined();
        expect(body.database_path).toBeUndefined();
        expect(body.repository_path).toBeUndefined();
      }
    );


    it(
      "posts explicit client response without acknowledgment lineage authority",
      async () => {
        const fetchMock = vi.fn<
          (
            input: RequestInfo | URL,
            init?: RequestInit
          ) => Promise<Response>
        >(
          async () =>
            jsonResponse({
              response_status:
                "client_response_recorded",
              client_response_recorded: true,
              report_id: "report-001",
              response_id:
                "client-response-001",
              responded_by:
                "client-representative",
              responded_at:
                "2026-09-07T19:30:00+00:00",
              response_method:
                "email_reply",
              response_reference:
                "response-mail-001",
              findings_disposition:
                "acknowledged",
              recommendations_disposition:
                "accepted",
              response_note:
                "Client accepts recommendations for planning review."
            })
        );

        vi.stubGlobal("fetch", fetchMock);

        const request = clientResponseRequest();

        const result =
          await recordPaidAssessmentClientResponse(
            CONFIG,
            HIERARCHY,
            request
          );

        expect(
          result.client_response_recorded
        ).toBe(true);

        const [
          input,
          init
        ] = fetchMock.mock.calls[0];

        expect(requestUrl(input)).toContain(
          "/client-response"
        );

        expect(init).toMatchObject({
          method: "POST",
          cache: "no-store",
          headers: {
            "Content-Type": "application/json",
            "X-Tenant-ID": "tenant-alpha",
            "X-Actor-ID": "console-admin",
            "X-Actor-Roles": "assessment:admin"
          }
        });

        const body = JSON.parse(
          String(init?.body)
        );

        expect(body).toEqual(request);

        expect(Object.keys(body).sort()).toEqual(
          [
            "response_id",
            "responded_at",
            "responded_by",
            "response_method",
            "response_note",
            "response_reference",
            "findings_disposition",
            "recommendations_disposition"
          ].sort()
        );

        expect(body.report_id).toBeUndefined();
        expect(
          body.acknowledgment_id
        ).toBeUndefined();
        expect(
          body.acknowledgment_hash
        ).toBeUndefined();
        expect(body.database_path).toBeUndefined();
        expect(body.repository_path).toBeUndefined();
      }
    );


    it(
      "preserves client acknowledgment conflict",
      async () => {
        const payload = {
          detail:
            "client acknowledgment lifecycle artifact already exists"
        };

        vi.stubGlobal(
          "fetch",
          vi.fn(
            async () =>
              jsonResponse(
                payload,
                409
              )
          )
        );

        await expect(
          recordPaidAssessmentClientAcknowledgment(
            CONFIG,
            HIERARCHY,
            acknowledgmentRequest()
          )
        ).rejects.toMatchObject({
          name: "GovernanceAssessmentApiError",
          status: 409,
          payload
        });
      }
    );


    it(
      "preserves client response conflict",
      async () => {
        const payload = {
          detail:
            "client response lifecycle artifact already exists"
        };

        vi.stubGlobal(
          "fetch",
          vi.fn(
            async () =>
              jsonResponse(
                payload,
                409
              )
          )
        );

        await expect(
          recordPaidAssessmentClientResponse(
            CONFIG,
            HIERARCHY,
            clientResponseRequest()
          )
        ).rejects.toMatchObject({
          name: "GovernanceAssessmentApiError",
          status: 409,
          payload
        });
      }
    );

  }
);