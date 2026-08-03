import {
  render,
  screen,
  waitFor
} from "@testing-library/react";

import userEvent from "@testing-library/user-event";

import {
  beforeEach,
  describe,
  expect,
  it,
  vi
} from "vitest";

import AuditIntegrityPage from "./page";

import {
  createAuditCheckpoint,
  fetchAuditCheckpoints,
  fetchAuditEvents,
  fetchAuditIntegrity,
  fetchSignedAuditCheckpoints,
  verifySignedAuditCheckpoints
} from "@/lib/governance-assessment-api";

import {
  detectSigningCapability
} from "@/lib/signing-capability";

vi.mock(
  "@/lib/governance-assessment-api",
  async (importOriginal) => {
    const actual =
      await importOriginal<
        typeof import(
          "@/lib/governance-assessment-api"
        )
      >();

    return {
      ...actual,
      getGovernanceAssessmentApiConfig:
        vi.fn(() => ({
          baseUrl:
            "http://127.0.0.1:8000",
          tenantId: "tenant-alpha",
          actorId: "console-admin",
          actorRoles: "assessment:admin"
        })),
      fetchAuditEvents: vi.fn(),
      fetchAuditIntegrity: vi.fn(),
      fetchAuditCheckpoints: vi.fn(),
      fetchSignedAuditCheckpoints:
        vi.fn(),
      verifySignedAuditCheckpoints:
        vi.fn(),
      createAuditCheckpoint: vi.fn()
    };
  }
);

vi.mock(
  "@/lib/signing-capability",
  async (importOriginal) => {
    const actual =
      await importOriginal<
        typeof import(
          "@/lib/signing-capability"
        )
      >();

    return {
      ...actual,
      detectSigningCapability:
        vi.fn()
    };
  }
);

const mockedFetchEvents =
  vi.mocked(fetchAuditEvents);

const mockedFetchIntegrity =
  vi.mocked(fetchAuditIntegrity);

const mockedFetchCheckpoints =
  vi.mocked(fetchAuditCheckpoints);

const mockedFetchSignedCheckpoints =
  vi.mocked(fetchSignedAuditCheckpoints);

const mockedVerifySignedCheckpoints =
  vi.mocked(verifySignedAuditCheckpoints);

const mockedDetectCapability =
  vi.mocked(detectSigningCapability);

const mockedCreateCheckpoint =
  vi.mocked(createAuditCheckpoint);

const CORE_CHECKPOINT_ID =
  "checkpoint-core-001";

const CORE_EVENT_ID =
  "audit-event-core-001";

const ACTIVE_KEY = {
  tenant_id: "tenant-alpha",
  key_id: "assessment-local-2026-01",
  secret_reference:
    "env://GAGF_ASSESSMENT_CHECKPOINT_SECRET",
  active: true,
  created_at:
    "2026-08-02T12:00:00Z",
  retired_at: null
};

function configureCoreAuditData() {
  mockedFetchEvents.mockResolvedValue({
    tenant_id: "tenant-alpha",
    items: [
      {
        event_id: CORE_EVENT_ID,
        request_id:
          "request-core-001",
        tenant_id: "tenant-alpha",
        actor_id:
          "integration-operator",
        actor_roles: [
          "assessment:admin"
        ],
        method: "POST",
        route:
          "/api/v1/governance-assessments/execute",
        outcome: "allowed",
        status_code: 200,
        reason_code: null,
        occurred_at:
          "2026-08-03T00:00:00Z",
        previous_hash:
          "previous-audit-hash",
        event_hash:
          "current-audit-event-hash",
        hash_version: "1.0.0"
      }
    ],
    count: 1,
    limit: 100
  });

  mockedFetchIntegrity.mockResolvedValue({
    tenant_id: "tenant-alpha",
    valid: true,
    checked_count: 461,
    failure_index: null,
    failure_event_id: null,
    reason_code: null
  });

  mockedFetchCheckpoints.mockResolvedValue({
    tenant_id: "tenant-alpha",
    items: [
      {
        checkpoint_id:
          CORE_CHECKPOINT_ID,
        tenant_id: "tenant-alpha",
        chain_head_hash:
          "core-chain-head-hash",
        checked_count: 461,
        valid: true,
        reason_code: null,
        created_at:
          "2026-08-03T00:01:00Z",
        checkpoint_version: "1.0.0"
      }
    ],
    count: 1,
    limit: 100
  });
}

function configureDegradedOptionalServices() {
  mockedFetchSignedCheckpoints
    .mockRejectedValue(
      new TypeError(
        "Signed inventory unavailable"
      )
    );

  mockedVerifySignedCheckpoints
    .mockResolvedValue({
      available: false,
      status: 503,
      code:
        "SIGNED_VERIFICATION_UNAVAILABLE",
      message:
        "The signature verifier is temporarily unavailable."
    });

  mockedDetectCapability
    .mockResolvedValue({
      status: "unconfigured",
      available: false,
      title:
        "Durable signing is not configured",
      message:
        "No active durable signing key is available for this tenant.",
      activeKey: null,
      statusCode: 503,
      reasonCode:
        "CHECKPOINT_SIGNING_UNAVAILABLE"
    });
}

function configureHealthyOptionalServices() {
  mockedFetchSignedCheckpoints
    .mockResolvedValue({
      tenant_id: "tenant-alpha",
      items: [
        {
          checkpoint_id:
            "signed-checkpoint-001",
          key_id:
            "assessment-local-2026-01"
        }
      ],
      count: 1,
      limit: 100
    });

  mockedVerifySignedCheckpoints
    .mockResolvedValue({
      available: true,
      payload: {
        tenant_id: "tenant-alpha",
        count: 1,
        valid_count: 1,
        invalid_count: 0
      }
    });

  mockedDetectCapability
    .mockResolvedValue({
      status: "available",
      available: true,
      title:
        "Durable signing available",
      message:
        "Checkpoint signing is available through active key assessment-local-2026-01.",
      activeKey: ACTIVE_KEY,
      statusCode: 200,
      reasonCode: null
    });
}

describe(
  "AuditIntegrityPage integration",
  () => {
    beforeEach(() => {
      vi.clearAllMocks();

      window.history.replaceState(
        {},
        "",
        "/audit-integrity"
      );

      configureCoreAuditData();
    });

    it(
      "preserves core audit evidence when optional cryptographic services degrade",
      async () => {
        configureDegradedOptionalServices();

        render(<AuditIntegrityPage />);

        expect(
          await screen.findByText(
            "Optional cryptographic services degraded"
          )
        ).toBeInTheDocument();

        expect(
          screen.getByRole(
            "heading",
            {
              name: "Chain verification"
            }
          )
        ).toBeInTheDocument();

        expect(
          screen.getByText("Verified")
        ).toBeInTheDocument();

        expect(
          screen.getByText(
            "integration-operator"
          )
        ).toBeInTheDocument();

        expect(
          screen.getByText(
            "/api/v1/governance-assessments/execute"
          )
        ).toBeInTheDocument();

        expect(
          screen.getByRole(
            "heading",
            {
              name:
                "Checkpoint inventory"
            }
          )
        ).toBeInTheDocument();

        expect(
          screen.getByText(
            new RegExp(
              CORE_CHECKPOINT_ID
            )
          )
        ).toBeInTheDocument();

        expect(
          screen.getByRole(
            "heading",
            {
              name:
                "Durable signing is not configured"
            }
          )
        ).toBeInTheDocument();

        expect(
          screen.getByText(
            /ordinary checkpoint history remain available/i
          )
        ).toBeInTheDocument();

        expect(
          screen.queryByText(
            "Audit console unavailable"
          )
        ).not.toBeInTheDocument();

        expect(
          mockedCreateCheckpoint
        ).not.toHaveBeenCalled();
      }
    );

    it(
      "recovers optional services after an operator retry",
      async () => {
        const user = userEvent.setup();

        mockedFetchSignedCheckpoints
          .mockRejectedValueOnce(
            new TypeError(
              "Signed inventory unavailable"
            )
          )
          .mockResolvedValue({
            tenant_id: "tenant-alpha",
            items: [
              {
                checkpoint_id:
                  "signed-checkpoint-001",
                key_id:
                  "assessment-local-2026-01"
              }
            ],
            count: 1,
            limit: 100
          });

        mockedVerifySignedCheckpoints
          .mockResolvedValueOnce({
            available: false,
            status: 503,
            code:
              "SIGNED_VERIFICATION_UNAVAILABLE",
            message:
              "The signature verifier is temporarily unavailable."
          })
          .mockResolvedValue({
            available: true,
            payload: {
              tenant_id: "tenant-alpha",
              count: 1,
              valid_count: 1,
              invalid_count: 0
            }
          });

        mockedDetectCapability
          .mockResolvedValueOnce({
            status: "unconfigured",
            available: false,
            title:
              "Durable signing is not configured",
            message:
              "No active durable signing key is available for this tenant.",
            activeKey: null,
            statusCode: 503,
            reasonCode:
              "CHECKPOINT_SIGNING_UNAVAILABLE"
          })
          .mockResolvedValue({
            status: "available",
            available: true,
            title:
              "Durable signing available",
            message:
              "Checkpoint signing is available through active key assessment-local-2026-01.",
            activeKey: ACTIVE_KEY,
            statusCode: 200,
            reasonCode: null
          });

        render(<AuditIntegrityPage />);

        const retryButton =
          await screen.findByRole(
            "button",
            {
              name:
                "Retry optional services"
            }
          );

        expect(
          screen.getByText(
            "integration-operator"
          )
        ).toBeInTheDocument();

        await user.click(retryButton);

        expect(
          await screen.findByRole(
            "heading",
            {
              name:
                "Durable signing available"
            }
          )
        ).toBeInTheDocument();

        await waitFor(() => {
          expect(
            screen.queryByText(
              "Optional cryptographic services degraded"
            )
          ).not.toBeInTheDocument();
        });

        expect(
          screen.getByText(
            "integration-operator"
          )
        ).toBeInTheDocument();

        expect(
          screen.getByText(
            new RegExp(
              CORE_CHECKPOINT_ID
            )
          )
        ).toBeInTheDocument();

        await waitFor(() => {
          expect(
            mockedFetchEvents
          ).toHaveBeenCalledTimes(2);

          expect(
            mockedFetchIntegrity
          ).toHaveBeenCalledTimes(2);

          expect(
            mockedFetchCheckpoints
          ).toHaveBeenCalledTimes(2);

          expect(
            mockedFetchSignedCheckpoints
          ).toHaveBeenCalledTimes(2);

          expect(
            mockedVerifySignedCheckpoints
          ).toHaveBeenCalledTimes(2);

          expect(
            mockedDetectCapability
          ).toHaveBeenCalledTimes(2);
        });
      }
    );
  }
);
