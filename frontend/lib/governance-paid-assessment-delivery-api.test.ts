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
  fetchPaidAssessmentDeliveryReadiness,
  recordPaidAssessmentDelivery,
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
  }
);