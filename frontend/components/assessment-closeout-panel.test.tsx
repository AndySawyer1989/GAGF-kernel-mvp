import {
  fireEvent,
  render,
  screen,
  waitFor
} from "@testing-library/react";
import {
  afterEach,
  describe,
  expect,
  it,
  vi
} from "vitest";

import {
  AssessmentCloseoutPanel
} from "./assessment-closeout-panel";


const CONFIG = {
  baseUrl: "http://127.0.0.1:8000",
  tenantId: "tenant-alpha",
  actorId: "console-admin",
  actorRoles: "assessment:admin"
};

const HIERARCHY = {
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


function lifecyclePayload(
  clientResponseRecorded: boolean
) {
  return {
    tenant_id: "tenant-alpha",
    client_id: "client-acme",
    engagement_id: "engagement-001",
    assessment_id: "assessment-001",
    hierarchy_key:
      "tenant-alpha/client-acme/engagement-001/assessment-001",
    current_stage:
      clientResponseRecorded
        ? "client_response_recorded"
        : "client_receipt_acknowledged",
    pending_next_step:
      clientResponseRecorded
        ? "none"
        : "client_response",
    delivery_recorded: true,
    receipt_acknowledged: true,
    client_response_recorded:
      clientResponseRecorded,
    report_id: "report-001",
    findings_disposition:
      clientResponseRecorded
        ? "acknowledged"
        : null,
    recommendations_disposition:
      clientResponseRecorded
        ? "under_review"
        : null,
    lifecycle_artifact_count:
      clientResponseRecorded
        ? 3
        : 2,
    repository_chain_valid: true,
    boundaries: {}
  };
}


function notClosedPayload() {
  return {
    status_type:
      "governance-commercial-paid-assessment-closeout-status",
    version: "0.1.0",
    schema_version: "1.0.0",
    tenant_id: "tenant-alpha",
    client_id: "client-acme",
    engagement_id: "engagement-001",
    assessment_id: "assessment-001",
    hierarchy_key:
      "tenant-alpha/client-acme/engagement-001/assessment-001",
    found: false,
    closeout_recorded: false,
    closeout_status: null,
    report_id: null,
    closed_by: null,
    closed_at: null,
    closeout_reason: null,
    repository_chain_valid: true,
    boundaries: {}
  };
}


function closedPayload() {
  return {
    status_type:
      "governance-commercial-paid-assessment-closeout-status",
    version: "0.1.0",
    schema_version: "1.0.0",
    tenant_id: "tenant-alpha",
    client_id: "client-acme",
    engagement_id: "engagement-001",
    assessment_id: "assessment-001",
    hierarchy_key:
      "tenant-alpha/client-acme/engagement-001/assessment-001",
    found: true,
    closeout_recorded: true,
    closeout_status: "assessment_closed",
    report_id: "report-001",
    closed_by: "console-admin",
    closed_at: "2026-09-08T18:00:00Z",
    closeout_reason:
      "Administrative processing complete.",
    repository_chain_valid: true,
    boundaries: {}
  };
}


describe(
  "AssessmentCloseoutPanel",
  () => {
    afterEach(() => {
      vi.unstubAllGlobals();
    });


    it(
      "does not allow closeout before client response",
      async () => {
        vi.stubGlobal(
          "fetch",
          vi.fn<typeof fetch>(
            async (input) => {
              const url = String(input);

              if (
                url.endsWith(
                  "/lifecycle-status"
                )
              ) {
                return jsonResponse(
                  lifecyclePayload(false)
                );
              }

              return jsonResponse(
                notClosedPayload()
              );
            }
          )
        );

        render(
          <AssessmentCloseoutPanel
            config={CONFIG}
            hierarchy={HIERARCHY}
          />
        );

        expect(
          await screen.findByRole(
            "heading",
            {
              name: "Client response required"
            }
          )
        ).toBeInTheDocument();

        expect(
          screen.getByText(
            /Delivery or receipt acknowledgment alone does not authorize closeout/i
          )
        ).toBeInTheDocument();

        expect(
          screen.queryByRole(
            "button",
            {
              name:
                "Record administrative closeout"
            }
          )
        ).not.toBeInTheDocument();
      }
    );


    it(
      "enables explicit closeout after client response",
      async () => {
        const fetchMock =
          vi.fn<typeof fetch>(
            async (input) => {
              const url = String(input);

              if (
                url.endsWith(
                  "/lifecycle-status"
                )
              ) {
                return jsonResponse(
                  lifecyclePayload(true)
                );
              }

              if (
                url.endsWith(
                  "/closeout-status"
                )
              ) {
                return jsonResponse(
                  notClosedPayload()
                );
              }

              return jsonResponse({
                closeout_type:
                  "governance-commercial-paid-assessment-closeout",
                version: "0.1.0",
                schema_version: "1.0.0",
                tenant_id: "tenant-alpha",
                client_id: "client-acme",
                engagement_id:
                  "engagement-001",
                assessment_id:
                  "assessment-001",
                hierarchy_key:
                  "tenant-alpha/client-acme/engagement-001/assessment-001",
                report_id: "report-001",
                closeout_status:
                  "assessment_closed",
                administrative_closeout_recorded:
                  true,
                closed_by:
                  "console-admin",
                closeout_reason:
                  "Administrative processing complete.",
                closeout_artifact_id:
                  "closeout-artifact-001",
                closeout_artifact_hash:
                  "closeout-hash-001",
                repository_chain_valid: true,
                boundaries: {}
              });
            }
          );

        vi.stubGlobal(
          "fetch",
          fetchMock
        );

        render(
          <AssessmentCloseoutPanel
            config={CONFIG}
            hierarchy={HIERARCHY}
          />
        );

        expect(
          await screen.findByRole(
            "heading",
            {
              name:
                "Administrative closeout available"
            }
          )
        ).toBeInTheDocument();

        const button =
          screen.getByRole(
            "button",
            {
              name:
                "Record administrative closeout"
            }
          );

        expect(button).toBeDisabled();

        fireEvent.change(
          screen.getByLabelText(
            "Closeout reason"
          ),
          {
            target: {
              value:
                "Administrative processing complete."
            }
          }
        );

        fireEvent.click(
          screen.getByLabelText(
            /I explicitly confirm administrative closeout/i
          )
        );

        expect(button).toBeEnabled();

        fireEvent.click(button);

        await waitFor(() => {
          expect(
            screen.getByRole(
              "heading",
              {
                name:
                  "Assessment administratively closed"
              }
            )
          ).toBeInTheDocument();
        });

        const postCall =
          fetchMock.mock.calls.find(
            ([input, init]) =>
              String(input).endsWith(
                "/administrative-closeout"
              ) &&
              init?.method === "POST"
          );

        expect(postCall).toBeDefined();

        const body = JSON.parse(
          String(postCall?.[1]?.body)
        );

        expect(body).toEqual({
          closed_by:
            "console-admin",
          closeout_reason:
            "Administrative processing complete.",
          administrative_closeout_confirmed:
            true
        });

        expect(body).not.toHaveProperty(
          "report_id"
        );

        expect(body).not.toHaveProperty(
          "response_id"
        );

        expect(body).not.toHaveProperty(
          "closeout_status"
        );
      }
    );


    it(
      "restores persisted administrative closeout after restart",
      async () => {
        vi.stubGlobal(
          "fetch",
          vi.fn<typeof fetch>(
            async (input) => {
              const url = String(input);

              if (
                url.endsWith(
                  "/lifecycle-status"
                )
              ) {
                return jsonResponse(
                  lifecyclePayload(true)
                );
              }

              return jsonResponse(
                closedPayload()
              );
            }
          )
        );

        render(
          <AssessmentCloseoutPanel
            config={CONFIG}
            hierarchy={HIERARCHY}
          />
        );

        expect(
          await screen.findByRole(
            "heading",
            {
              name:
                "Assessment administratively closed"
            }
          )
        ).toBeInTheDocument();

        expect(
          screen.getByText(
            "assessment_closed"
          )
        ).toBeInTheDocument();

        expect(
          screen.getByText(
            "2026-09-08T18:00:00Z"
          )
        ).toBeInTheDocument();

        expect(
          screen.getByText(
            "Administrative processing complete."
          )
        ).toBeInTheDocument();

        expect(
          screen.queryByRole(
            "button",
            {
              name:
                "Record administrative closeout"
            }
          )
        ).not.toBeInTheDocument();
      }
    );


    it(
      "does not infer closeout when restoration fails",
      async () => {
        vi.stubGlobal(
          "fetch",
          vi.fn<typeof fetch>(
            async () =>
              jsonResponse(
                {
                  detail:
                    "repository verification failed"
                },
                409
              )
          )
        );

        render(
          <AssessmentCloseoutPanel
            config={CONFIG}
            hierarchy={HIERARCHY}
          />
        );

        expect(
          await screen.findByRole(
            "alert"
          )
        ).toHaveTextContent(
          "repository verification failed"
        );

        expect(
          screen.queryByText(
            "Assessment closed"
          )
        ).not.toBeInTheDocument();

        expect(
          screen.queryByRole(
            "button",
            {
              name:
                "Record administrative closeout"
            }
          )
        ).not.toBeInTheDocument();
      }
    );


    it(
      "preserves administrative closeout authority boundaries",
      async () => {
        vi.stubGlobal(
          "fetch",
          vi.fn<typeof fetch>(
            async (input) => {
              if (
                String(input).endsWith(
                  "/lifecycle-status"
                )
              ) {
                return jsonResponse(
                  lifecyclePayload(false)
                );
              }

              return jsonResponse(
                notClosedPayload()
              );
            }
          )
        );

        render(
          <AssessmentCloseoutPanel
            config={CONFIG}
            hierarchy={HIERARCHY}
          />
        );

        expect(
          await screen.findByText(
            /Administrative closeout does not validate findings/i
          )
        ).toBeInTheDocument();

        expect(
          screen.getByText(
            /request or authorize an intervention/i
          )
        ).toBeInTheDocument();

        expect(
          screen.getByText(
            /establish causation or ROI/i
          )
        ).toBeInTheDocument();

        expect(
          screen.getByText(
            /verified customer outcome/i
          )
        ).toBeInTheDocument();
      }
    );
  }
);