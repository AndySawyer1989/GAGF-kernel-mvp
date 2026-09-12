import {
  afterEach,
  describe,
  expect,
  it,
  vi
} from "vitest";

import {
  fetchCustomerTrialExecutionHandoffStatus,
  fetchCustomerTrialPreflightStatus,
  GovernanceCustomerTrialApiError,
  prepareCustomerTrialExecutionHandoff
} from "./governance-customer-trial-api";


const config = {
  baseUrl:
    "http://127.0.0.1:8000",

  tenantId:
    "tenant-alpha",

  actorId:
    "console-admin",

  actorRoles:
    "assessment_operator"
};


const hierarchy = {
  tenantId:
    "tenant-alpha",

  clientId:
    "client-001",

  engagementId:
    "engagement-001",

  assessmentId:
    "assessment-001"
};


function jsonResponse(
  payload: unknown,
  status = 200
): Response {
  return new Response(
    JSON.stringify(
      payload
    ),
    {
      status,

      headers: {
        "Content-Type":
          "application/json"
      }
    }
  );
}


function handoffRequest() {
  return {
    tenant_id:
      "tenant-alpha",

    client_id:
      "client-001",

    engagement_id:
      "engagement-001",

    assessment_id:
      "assessment-001",

    execution_input_binding_hash:
      "a".repeat(64),

    contract_execution_event: {
      contract_execution_event_id:
        "contract-assessment-001-1",

      contract_executed:
        true,

      contract_execution_review_ready:
        true,

      contract_execution_confirmed:
        true,

      executed_contract_reference_recorded:
        true,

      executed_at_recorded:
        true,

      all_required_signatures_recorded:
        true,

      human_operator_confirmed_execution:
        true,

      requires_final_paid_work_authorization:
        true,

      human_boundary_required:
        true,

      gagf_kernel_authoritative:
        true,

      ai_override_allowed:
        false
    },

    paid_work_authorization: {
      authorization_id:
        "paid-work-assessment-001-1",

      tenant_id:
        "tenant-alpha",

      client_id:
        "client-001",

      engagement_id:
        "engagement-001",

      assessment_id:
        "assessment-001",

      contract_execution_event_id:
        "contract-assessment-001-1",

      authorized_by:
        "console-admin",

      authorized_at:
        "2026-09-11T22:00:00.000Z",

      paid_assessment_authorized:
        true
    }
  };
}


afterEach(
  () => {
    vi.restoreAllMocks();
  }
);


describe(
  "governance customer trial API",
  () => {
    it(
      "loads read-only preflight status",
      async () => {
        const fetchMock =
          vi
            .spyOn(
              globalThis,
              "fetch"
            )
            .mockResolvedValue(
              jsonResponse({
                status:
                  "ok",

                api_version:
                  "1.0.0",

                authority:
                  "READ_ONLY",

                result: {
                  receipt_found:
                    true,

                  receipt: {
                    hierarchy_key:
                      (
                        "tenant-alpha/"
                        + "client-001/"
                        + "engagement-001/"
                        + "assessment-001"
                      ),

                    package_hash:
                      "package-hash-001",

                    receipt_hash:
                      "preflight-receipt-001"
                  }
                },

                boundaries: {
                  status_is_read_only:
                    true
                }
              })
            );

        const result =
          await fetchCustomerTrialPreflightStatus(
            config,
            hierarchy
          );

        expect(
          result.result
            .receipt_found
        ).toBe(
          true
        );

        expect(
          result.result
            .receipt
            ?.receipt_hash
        ).toBe(
          "preflight-receipt-001"
        );

        const [
          requestUrl,
          requestInit
        ] =
          fetchMock.mock.calls[0];

        expect(
          String(
            requestUrl
          )
        ).toBe(
          (
            "http://127.0.0.1:8000/"
            + "api/v1/"
            + "governance-customer-trials/"
            + "tenant-alpha/"
            + "client-001/"
            + "engagement-001/"
            + "assessment-001/"
            + "preflight-status"
          )
        );

        expect(
          requestInit
        ).toMatchObject({
          method:
            "GET",

          cache:
            "no-store",

          headers: {
            "X-Tenant-ID":
              "tenant-alpha",

            "X-Actor-ID":
              "console-admin",

            "X-Actor-Roles":
              "assessment_operator"
          }
        });
      }
    );


    it(
      "loads read-only execution handoff status",
      async () => {
        vi
          .spyOn(
            globalThis,
            "fetch"
          )
          .mockResolvedValue(
            jsonResponse({
              status:
                "ok",

              api_version:
                "1.0.0",

              authority:
                "READ_ONLY",

              result: {
                receipt_found:
                  true,

                receipt: {
                  hierarchy_key:
                    (
                      "tenant-alpha/"
                      + "client-001/"
                      + "engagement-001/"
                      + "assessment-001"
                    ),

                  lineage_hash:
                    "lineage-001",

                  receipt_hash:
                    "handoff-receipt-001",

                  execution_handoff_lineage: {
                    handoff_hash:
                      "handoff-001"
                  }
                }
              },

              boundaries: {
                status_is_read_only:
                  true,

                status_is_not_execution_authority:
                  true,

                status_is_not_recovery_authority:
                  true,

                status_is_not_delivery_authority:
                  true,

                status_is_not_closeout_authority:
                  true,

                status_is_not_intervention_authority:
                  true
              }
            })
          );

        const result =
          await fetchCustomerTrialExecutionHandoffStatus(
            config,
            hierarchy
          );

        expect(
          result.result
            .receipt_found
        ).toBe(
          true
        );

        expect(
          result.result
            .receipt
            ?.execution_handoff_lineage
            ?.handoff_hash
        ).toBe(
          "handoff-001"
        );

        expect(
          result.boundaries
            .status_is_not_execution_authority
        ).toBe(
          true
        );
      }
    );


    it(
      "preserves an empty governed status",
      async () => {
        vi
          .spyOn(
            globalThis,
            "fetch"
          )
          .mockResolvedValue(
            jsonResponse({
              status:
                "ok",

              api_version:
                "1.0.0",

              authority:
                "READ_ONLY",

              result: {
                receipt_found:
                  false,

                receipt:
                  null
              },

              boundaries: {
                status_is_read_only:
                  true,

                status_is_not_execution_authority:
                  true,

                status_is_not_recovery_authority:
                  true,

                status_is_not_delivery_authority:
                  true,

                status_is_not_closeout_authority:
                  true,

                status_is_not_intervention_authority:
                  true
              }
            })
          );

        const result =
          await fetchCustomerTrialExecutionHandoffStatus(
            config,
            hierarchy
          );

        expect(
          result.result
            .receipt_found
        ).toBe(
          false
        );

        expect(
          result.result
            .receipt
        ).toBeNull();
      }
    );


    it(
      "fails closed when status claims authority",
      async () => {
        vi
          .spyOn(
            globalThis,
            "fetch"
          )
          .mockResolvedValue(
            jsonResponse({
              status:
                "ok",

              api_version:
                "1.0.0",

              authority:
                "EXECUTION_AUTHORITY",

              result: {
                receipt_found:
                  false,

                receipt:
                  null
              },

              boundaries: {}
            })
          );

        await expect(
          fetchCustomerTrialExecutionHandoffStatus(
            config,
            hierarchy
          )
        ).rejects.toThrow(
          GovernanceCustomerTrialApiError
        );
      }
    );


    it(
      "fails closed on malformed receipt state",
      async () => {
        vi
          .spyOn(
            globalThis,
            "fetch"
          )
          .mockResolvedValue(
            jsonResponse({
              status:
                "ok",

              api_version:
                "1.0.0",

              authority:
                "READ_ONLY",

              result: {
                receipt_found:
                  false,

                receipt: {
                  receipt_hash:
                    "should-not-exist"
                }
              }
            })
          );

        await expect(
          fetchCustomerTrialPreflightStatus(
            config,
            hierarchy
          )
        ).rejects.toThrow(
          (
            "Preflight receipt must "
            + "be null"
          )
        );
      }
    );


    it(
      "surfaces governed API failure messages",
      async () => {
        vi
          .spyOn(
            globalThis,
            "fetch"
          )
          .mockResolvedValue(
            jsonResponse(
              {
                detail: {
                  code:
                    "CUSTOMER_TRIAL_STATUS_ERROR",

                  message:
                    (
                      "customer trial "
                      + "status unavailable"
                    )
                }
              },
              409
            )
          );

        await expect(
          fetchCustomerTrialPreflightStatus(
            config,
            hierarchy
          )
        ).rejects.toThrow(
          (
            "customer trial "
            + "status unavailable"
          )
        );
      }
    );


    it(
      "prepares execution handoff without claiming execution authority",
      async () => {
        const fetchMock =
          vi
            .spyOn(
              globalThis,
              "fetch"
            )
            .mockResolvedValue(
              jsonResponse({
                status:
                  "ok",

                api_version:
                  "1.0.0",

                authority:
                  "HANDOFF_PREPARATION_ONLY",

                binding_metadata: {
                  binding_hash:
                    "a".repeat(64)
                },

                result: {
                  hierarchy_key:
                    (
                      "tenant-alpha/"
                      + "client-001/"
                      + "engagement-001/"
                      + "assessment-001"
                    ),

                  receipt: {
                    receipt_hash:
                      "handoff-receipt-001"
                  }
                },

                boundaries: {
                  preparation_is_not_execution_authority:
                    true
                }
              })
            );

        const request =
          handoffRequest();

        const result =
          await prepareCustomerTrialExecutionHandoff(
            config,
            request
          );

        expect(
          result.authority
        ).toBe(
          "HANDOFF_PREPARATION_ONLY"
        );

        const [
          requestUrl,
          requestInit
        ] =
          fetchMock.mock.calls[0];

        expect(
          String(
            requestUrl
          )
        ).toBe(
          (
            "http://127.0.0.1:8000/"
            + "api/v1/"
            + "governance-customer-trials/"
            + "execution-handoff"
          )
        );

        expect(
          requestInit
        ).toMatchObject({
          method:
            "POST",

          cache:
            "no-store",

          headers: {
            "Content-Type":
              "application/json",

            "X-Tenant-ID":
              "tenant-alpha",

            "X-Actor-ID":
              "console-admin",

            "X-Actor-Roles":
              "assessment_operator"
          }
        });

        expect(
          JSON.parse(
            String(
              requestInit?.body
            )
          )
        ).toEqual(
          request
        );
      }
    );


    it(
      "fails closed when handoff preparation claims execution authority",
      async () => {
        vi
          .spyOn(
            globalThis,
            "fetch"
          )
          .mockResolvedValue(
            jsonResponse({
              status:
                "ok",

              api_version:
                "1.0.0",

              authority:
                "EXECUTION_AUTHORITY",

              binding_metadata: {},

              result: {},

              boundaries: {}
            })
          );

        await expect(
          prepareCustomerTrialExecutionHandoff(
            config,
            handoffRequest()
          )
        ).rejects.toThrow(
          (
            "claimed unexpected "
            + "authority"
          )
        );
      }
    );


    it(
      "surfaces governed handoff preparation rejection",
      async () => {
        vi
          .spyOn(
            globalThis,
            "fetch"
          )
          .mockResolvedValue(
            jsonResponse(
              {
                detail: {
                  code:
                    (
                      "CUSTOMER_TRIAL_"
                      + "EXECUTION_HANDOFF_"
                      + "VALIDATION_ERROR"
                    ),

                  message:
                    (
                      "customer trial "
                      + "preflight receipt "
                      + "required"
                    )
                }
              },
              422
            )
          );

        await expect(
          prepareCustomerTrialExecutionHandoff(
            config,
            handoffRequest()
          )
        ).rejects.toThrow(
          (
            "customer trial "
            + "preflight receipt "
            + "required"
          )
        );
      }
    );
  }
);