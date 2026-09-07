import {
  fireEvent,
  render,
  screen,
  waitFor
} from "@testing-library/react";

import {
  afterEach,
  beforeEach,
  describe,
  expect,
  it,
  vi
} from "vitest";

import {
  PaidAssessmentDeliveryControls
} from "./paid-assessment-delivery-controls";

import {
  fetchPaidAssessmentLifecycleStatus,
  recordPaidAssessmentClientAcknowledgment,
  recordPaidAssessmentClientResponse
} from "@/lib/governance-paid-assessment-delivery-api";


vi.mock(
  "@/lib/governance-paid-assessment-delivery-api",
  async (importOriginal) => {
    const actual =
      await importOriginal<
        typeof import(
          "@/lib/governance-paid-assessment-delivery-api"
        )
      >();

    return {
      ...actual,
      fetchPaidAssessmentLifecycleStatus:
        vi.fn(),
      fetchPaidAssessmentDeliveryReadiness:
        vi.fn(),
      approvePaidAssessmentDelivery:
        vi.fn(),
      recordPaidAssessmentDelivery:
        vi.fn(),
      recordPaidAssessmentClientAcknowledgment:
        vi.fn(),
      recordPaidAssessmentClientResponse:
        vi.fn()
    };
  }
);


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


const fetchLifecycleMock =
  vi.mocked(
    fetchPaidAssessmentLifecycleStatus
  );


const recordAcknowledgmentMock =
  vi.mocked(
    recordPaidAssessmentClientAcknowledgment
  );


const recordResponseMock =
  vi.mocked(
    recordPaidAssessmentClientResponse
  );


function lifecycleStatus(
  overrides: Record<string, unknown> = {}
) {
  return {
    tenant_id: "tenant-alpha",
    client_id: "client-acme",
    engagement_id: "engagement-001",
    assessment_id: "assessment-001",
    hierarchy_key:
      "tenant-alpha/client-acme/engagement-001/assessment-001",
    current_stage: "delivered",
    pending_next_step:
      "record_client_acknowledgment",
    delivery_recorded: true,
    receipt_acknowledged: false,
    client_response_recorded: false,
    report_id: "report-001",
    findings_disposition: null,
    recommendations_disposition: null,
    lifecycle_artifact_count: 1,
    repository_chain_valid: true,
    boundaries: {
      delivery_is_not_receipt: true
    },
    ...overrides
  };
}


function renderControls(
  overrides: Record<string, unknown> = {}
) {
  const props = {
    config: CONFIG,
    hierarchy: HIERARCHY,
    reportId: "report-001",
    reportReady: true,
    repositoryVerified: true,
    findingsReady: true,
    onDeliveryRecorded: vi.fn(),
    ...overrides
  };

  return render(
    <PaidAssessmentDeliveryControls
      {...props}
    />
  );
}


describe(
  "PaidAssessmentDeliveryControls receipt lifecycle",
  () => {
    beforeEach(() => {
      fetchLifecycleMock.mockResolvedValue(
        lifecycleStatus()
      );

      recordAcknowledgmentMock.mockResolvedValue({
        acknowledgment_status:
          "client_receipt_acknowledged",
        client_receipt_acknowledged: true,
        report_id: "report-001",
        acknowledgment_id:
          "client-acknowledgment-assessment-001-1",
        acknowledged_by: "console-admin",
        acknowledged_at:
          "2026-09-07T19:30:00.000Z",
        acknowledgment_method:
          "email_reply",
        acknowledgment_reference:
          "receipt-mail-001",
        boundaries: {
          receipt_is_not_findings_acceptance: true
        }
      });


      recordResponseMock.mockResolvedValue({
        response_status:
          "client_response_recorded",
        client_response_recorded: true,
        report_id: "report-001",
        response_id:
          "client-response-assessment-001-1",
        responded_by: "console-admin",
        responded_at:
          "2026-09-07T19:45:00.000Z",
        response_method: "email_reply",
        response_reference:
          "response-mail-001",
        findings_disposition: "acknowledged",
        recommendations_disposition: "accepted",
        response_note:
          "Client accepts recommendations for planning review.",
        boundaries: {
          findings_acknowledgment_is_not_validation:
            true,
          recommendation_acceptance_is_not_implementation:
            true
        }
      });
    });


    afterEach(() => {
      vi.clearAllMocks();
    });


    it(
      "restores governed delivered lifecycle on mount",
      async () => {
        renderControls();

        await waitFor(() => {
          expect(
            fetchLifecycleMock
          ).toHaveBeenCalledTimes(1);
        });

        expect(
          fetchLifecycleMock
        ).toHaveBeenCalledWith(
          CONFIG,
          HIERARCHY,
          expect.any(AbortSignal)
        );

        expect(
          await screen.findByText(
            "Client receipt acknowledgment"
          )
        ).toBeInTheDocument();

        expect(
          screen.getByText(
            /Record this only after the client explicitly confirms receipt/i
          )
        ).toBeInTheDocument();
      }
    );


    it(
      "restores acknowledged receipt and hides receipt recorder",
      async () => {
        fetchLifecycleMock.mockResolvedValue(
          lifecycleStatus({
            current_stage:
              "client_receipt_acknowledged",
            pending_next_step:
              "record_client_response",
            receipt_acknowledged: true,
            lifecycle_artifact_count: 2
          })
        );

        renderControls();

        expect(
          await screen.findByText(
            "Client receipt acknowledged."
          )
        ).toBeInTheDocument();

        expect(
          screen.queryByText(
            "Client receipt acknowledgment"
          )
        ).not.toBeInTheDocument();

        expect(
          screen.getByText(
            /Receipt is recorded independently from findings acceptance/i
          )
        ).toBeInTheDocument();
      }
    );


    it(
      "does not expose receipt controls before governed delivery",
      async () => {
        fetchLifecycleMock.mockResolvedValue(
          lifecycleStatus({
            current_stage:
              "post_assessment_lifecycle_not_started",
            pending_next_step:
              "record_delivery",
            delivery_recorded: false,
            receipt_acknowledged: false,
            lifecycle_artifact_count: 0
          })
        );

        renderControls();

        await waitFor(() => {
          expect(
            fetchLifecycleMock
          ).toHaveBeenCalledTimes(1);
        });

        expect(
          screen.queryByText(
            "Client receipt acknowledgment"
          )
        ).not.toBeInTheDocument();

        expect(
          screen.queryByRole(
            "button",
            {
              name: "Record client receipt"
            }
          )
        ).not.toBeInTheDocument();
      }
    );


    it(
      "requires explicit receipt confirmation and reference",
      async () => {
        renderControls();

        const button =
          await screen.findByRole(
            "button",
            {
              name: "Record client receipt"
            }
          );

        expect(button).toBeDisabled();

        fireEvent.change(
          screen.getByPlaceholderText(
            "Message ID, portal record, or receipt reference"
          ),
          {
            target: {
              value: "receipt-mail-001"
            }
          }
        );

        expect(button).toBeDisabled();

        fireEvent.click(
          screen.getByRole(
            "checkbox",
            {
              name:
                /I confirm that the client explicitly acknowledged receipt/i
            }
          )
        );

        expect(button).toBeEnabled();
      }
    );


    it(
      "records only explicit receipt evidence",
      async () => {
        renderControls();

        const reference =
          await screen.findByPlaceholderText(
            "Message ID, portal record, or receipt reference"
          );

        fireEvent.change(
          reference,
          {
            target: {
              value: "receipt-mail-001"
            }
          }
        );

        fireEvent.click(
          screen.getByRole(
            "checkbox",
            {
              name:
                /I confirm that the client explicitly acknowledged receipt/i
            }
          )
        );

        fireEvent.click(
          screen.getByRole(
            "button",
            {
              name: "Record client receipt"
            }
          )
        );

        await waitFor(() => {
          expect(
            recordAcknowledgmentMock
          ).toHaveBeenCalledTimes(1);
        });

        const [
          config,
          hierarchy,
          request
        ] =
          recordAcknowledgmentMock.mock.calls[0];

        expect(config).toBe(CONFIG);
        expect(hierarchy).toBe(HIERARCHY);

        expect(request).toMatchObject({
          acknowledged_by: "console-admin",
          acknowledgment_method:
            "email_reply",
          acknowledgment_reference:
            "receipt-mail-001",
          client_acknowledged_receipt: true
        });

        expect(
          typeof request.acknowledgment_id
        ).toBe("string");

        expect(
          request.acknowledgment_id
        ).toContain(
          "client-acknowledgment-assessment-001-"
        );

        expect(
          typeof request.acknowledged_at
        ).toBe("string");

        expect(
          Object.keys(request).sort()
        ).toEqual(
          [
            "acknowledgment_id",
            "acknowledged_at",
            "acknowledged_by",
            "acknowledgment_method",
            "acknowledgment_reference",
            "client_acknowledged_receipt"
          ].sort()
        );

        expect(
          (
            request as Record<string, unknown>
          ).report_id
        ).toBeUndefined();

        expect(
          (
            request as Record<string, unknown>
          ).delivery_event_id
        ).toBeUndefined();

        expect(
          (
            request as Record<string, unknown>
          ).delivery_event_hash
        ).toBeUndefined();

        expect(
          (
            request as Record<string, unknown>
          ).database_path
        ).toBeUndefined();

        expect(
          (
            request as Record<string, unknown>
          ).repository_path
        ).toBeUndefined();
      }
    );


    it(
      "transitions to acknowledged state after successful recording",
      async () => {
        renderControls();

        fireEvent.change(
          await screen.findByPlaceholderText(
            "Message ID, portal record, or receipt reference"
          ),
          {
            target: {
              value: "receipt-mail-001"
            }
          }
        );

        fireEvent.click(
          screen.getByRole(
            "checkbox",
            {
              name:
                /I confirm that the client explicitly acknowledged receipt/i
            }
          )
        );

        fireEvent.click(
          screen.getByRole(
            "button",
            {
              name: "Record client receipt"
            }
          )
        );

        expect(
          await screen.findByText(
            "Client receipt acknowledged."
          )
        ).toBeInTheDocument();

        expect(
          screen.queryByRole(
            "button",
            {
              name: "Record client receipt"
            }
          )
        ).not.toBeInTheDocument();
      }
    );


    it(
      "does not infer delivery or receipt when lifecycle restoration fails",
      async () => {
        fetchLifecycleMock.mockRejectedValue(
          new Error(
            "lifecycle unavailable"
          )
        );

        renderControls();

        expect(
          await screen.findByText(
            "Lifecycle restoration failed"
          )
        ).toBeInTheDocument();

        expect(
          screen.queryByText(
            "Client receipt acknowledged."
          )
        ).not.toBeInTheDocument();

        expect(
          screen.queryByText(
            "Client receipt acknowledgment"
          )
        ).not.toBeInTheDocument();
      }
    );


    it(
      "preserves receipt semantic boundaries",
      async () => {
        renderControls();

        expect(
          await screen.findByText(
            /Receipt acknowledgment does not mean that the client accepts the findings/i
          )
        ).toBeInTheDocument();

        fireEvent.change(
          screen.getByPlaceholderText(
            "Message ID, portal record, or receipt reference"
          ),
          {
            target: {
              value: "receipt-mail-001"
            }
          }
        );

        fireEvent.click(
          screen.getByRole(
            "checkbox",
            {
              name:
                /I confirm that the client explicitly acknowledged receipt/i
            }
          )
        );

        fireEvent.click(
          screen.getByRole(
            "button",
            {
              name: "Record client receipt"
            }
          )
        );

        expect(
          await screen.findByText(
            /Receipt is recorded independently from findings acceptance, recommendation acceptance, response, closeout, or intervention authority/i
          )
        ).toBeInTheDocument();
      }
    );


    it(
      "does not refetch lifecycle for equivalent hierarchy object identities",
      async () => {
        const rendered =
          renderControls();

        await waitFor(() => {
          expect(
            fetchLifecycleMock
          ).toHaveBeenCalledTimes(1);
        });

        rendered.rerender(
          <PaidAssessmentDeliveryControls
            config={{ ...CONFIG }}
            hierarchy={{ ...HIERARCHY }}
            reportId="report-001"
            reportReady
            repositoryVerified
            findingsReady
            onDeliveryRecorded={vi.fn()}
          />
        );

        await waitFor(() => {
          expect(
            fetchLifecycleMock
          ).toHaveBeenCalledTimes(1);
        });
      }
    );

    it(
      "shows client response controls after acknowledged receipt",
      async () => {
        fetchLifecycleMock.mockResolvedValue(
          lifecycleStatus({
            current_stage:
              "client_receipt_acknowledged",
            pending_next_step:
              "record_client_response",
            receipt_acknowledged: true,
            client_response_recorded: false,
            lifecycle_artifact_count: 2
          })
        );

        renderControls();

        expect(
          await screen.findByText(
            "Client response"
          )
        ).toBeInTheDocument();

        expect(
          screen.getByText(
            /Receipt alone does not establish findings or recommendation disposition/i
          )
        ).toBeInTheDocument();

        expect(
          screen.getByRole(
            "button",
            {
              name: "Record client response"
            }
          )
        ).toBeDisabled();
      }
    );


    it(
      "restores already-recorded client response and hides response form",
      async () => {
        fetchLifecycleMock.mockResolvedValue(
          lifecycleStatus({
            current_stage:
              "client_response_recorded",
            pending_next_step: null,
            receipt_acknowledged: true,
            client_response_recorded: true,
            findings_disposition:
              "acknowledged",
            recommendations_disposition:
              "accepted",
            lifecycle_artifact_count: 3
          })
        );

        renderControls();

        expect(
          await screen.findByText(
            "Client response recorded."
          )
        ).toBeInTheDocument();

        expect(
          screen.queryByRole(
            "button",
            {
              name: "Record client response"
            }
          )
        ).not.toBeInTheDocument();

        expect(
          screen.getByText(
            /persisted independently from findings validation/i
          )
        ).toBeInTheDocument();
      }
    );


    it(
      "records independent findings and recommendation dispositions",
      async () => {
        fetchLifecycleMock.mockResolvedValue(
          lifecycleStatus({
            current_stage:
              "client_receipt_acknowledged",
            receipt_acknowledged: true
          })
        );

        renderControls();

        await screen.findByText(
          "Client response"
        );

        fireEvent.change(
          screen.getByPlaceholderText(
            "Message ID, meeting note, or response reference"
          ),
          {
            target: {
              value: "response-mail-001"
            }
          }
        );

        fireEvent.change(
          screen.getByLabelText(
            "Findings disposition"
          ),
          {
            target: {
              value: "disputed"
            }
          }
        );

        fireEvent.change(
          screen.getByLabelText(
            "Recommendations disposition"
          ),
          {
            target: {
              value: "partially_accepted"
            }
          }
        );

        fireEvent.change(
          screen.getByPlaceholderText(
            "Optional client response note"
          ),
          {
            target: {
              value:
                "Client disputes findings but accepts part of the recommendation set."
            }
          }
        );

        const button =
          screen.getByRole(
            "button",
            {
              name: "Record client response"
            }
          );

        expect(button).toBeEnabled();

        fireEvent.click(button);

        await waitFor(() => {
          expect(
            recordResponseMock
          ).toHaveBeenCalledTimes(1);
        });

        const request =
          recordResponseMock.mock.calls[0][2];

        expect(
          request.findings_disposition
        ).toBe("disputed");

        expect(
          request.recommendations_disposition
        ).toBe("partially_accepted");
      }
    );


    it(
      "records only explicit client response evidence",
      async () => {
        fetchLifecycleMock.mockResolvedValue(
          lifecycleStatus({
            current_stage:
              "client_receipt_acknowledged",
            receipt_acknowledged: true
          })
        );

        renderControls();

        fireEvent.change(
          await screen.findByPlaceholderText(
            "Message ID, meeting note, or response reference"
          ),
          {
            target: {
              value: "response-mail-001"
            }
          }
        );

        fireEvent.change(
          screen.getByLabelText(
            "Recommendations disposition"
          ),
          {
            target: {
              value: "accepted"
            }
          }
        );

        fireEvent.change(
          screen.getByPlaceholderText(
            "Optional client response note"
          ),
          {
            target: {
              value:
                "Client accepts recommendations for planning review."
            }
          }
        );

        fireEvent.click(
          screen.getByRole(
            "button",
            {
              name: "Record client response"
            }
          )
        );

        await waitFor(() => {
          expect(
            recordResponseMock
          ).toHaveBeenCalledTimes(1);
        });

        const [
          config,
          hierarchy,
          request
        ] = recordResponseMock.mock.calls[0];

        expect(config).toBe(CONFIG);
        expect(hierarchy).toBe(HIERARCHY);

        expect(
          Object.keys(request).sort()
        ).toEqual(
          [
            "response_id",
            "responded_by",
            "responded_at",
            "response_method",
            "response_reference",
            "findings_disposition",
            "recommendations_disposition",
            "response_note"
          ].sort()
        );

        expect(request.responded_by).toBe(
          "console-admin"
        );

        expect(request.response_method).toBe(
          "email_reply"
        );

        expect(
          request.response_reference
        ).toBe("response-mail-001");

        expect(
          (
            request as Record<string, unknown>
          ).report_id
        ).toBeUndefined();

        expect(
          (
            request as Record<string, unknown>
          ).acknowledgment_id
        ).toBeUndefined();

        expect(
          (
            request as Record<string, unknown>
          ).acknowledgment_hash
        ).toBeUndefined();

        expect(
          (
            request as Record<string, unknown>
          ).delivery_event_hash
        ).toBeUndefined();

        expect(
          (
            request as Record<string, unknown>
          ).database_path
        ).toBeUndefined();

        expect(
          (
            request as Record<string, unknown>
          ).repository_path
        ).toBeUndefined();
      }
    );


    it(
      "transitions to recorded-response state after success",
      async () => {
        fetchLifecycleMock.mockResolvedValue(
          lifecycleStatus({
            current_stage:
              "client_receipt_acknowledged",
            receipt_acknowledged: true
          })
        );

        renderControls();

        fireEvent.change(
          await screen.findByPlaceholderText(
            "Message ID, meeting note, or response reference"
          ),
          {
            target: {
              value: "response-mail-001"
            }
          }
        );

        fireEvent.click(
          screen.getByRole(
            "button",
            {
              name: "Record client response"
            }
          )
        );

        expect(
          await screen.findByText(
            "Client response recorded."
          )
        ).toBeInTheDocument();

        expect(
          screen.queryByRole(
            "button",
            {
              name: "Record client response"
            }
          )
        ).not.toBeInTheDocument();
      }
    );


    it(
      "preserves client response semantic boundaries",
      async () => {
        fetchLifecycleMock.mockResolvedValue(
          lifecycleStatus({
            current_stage:
              "client_receipt_acknowledged",
            receipt_acknowledged: true
          })
        );

        renderControls();

        expect(
          await screen.findByText(
            /Findings acknowledgment is not validation/i
          )
        ).toBeInTheDocument();

        expect(
          screen.getByText(
            /Recommendation acceptance does not authorize implementation or intervention/i
          )
        ).toBeInTheDocument();

        fireEvent.change(
          screen.getByPlaceholderText(
            "Message ID, meeting note, or response reference"
          ),
          {
            target: {
              value: "response-mail-001"
            }
          }
        );

        fireEvent.click(
          screen.getByRole(
            "button",
            {
              name: "Record client response"
            }
          )
        );

        expect(
          await screen.findByText(
            /response is persisted independently from findings validation, implementation authorization, intervention authority, closeout, ROI verification, or verified customer outcomes/i
          )
        ).toBeInTheDocument();
      }
    );

  }
);
