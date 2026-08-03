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

import SignedCheckpointsPage from "./page";

import {
  createSignedAuditCheckpoint,
  fetchSignedAuditCheckpointRecords,
  fetchSignedAuditCheckpointVerificationRecords
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
      fetchSignedAuditCheckpointRecords:
        vi.fn(),
      fetchSignedAuditCheckpointVerificationRecords:
        vi.fn(),
      createSignedAuditCheckpoint:
        vi.fn()
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

const mockedFetchRecords =
  vi.mocked(
    fetchSignedAuditCheckpointRecords
  );

const mockedFetchVerification =
  vi.mocked(
    fetchSignedAuditCheckpointVerificationRecords
  );

const mockedCreateCheckpoint =
  vi.mocked(
    createSignedAuditCheckpoint
  );

const mockedDetectCapability =
  vi.mocked(
    detectSigningCapability
  );

const CHECKPOINT_ID =
  "checkpoint-integration-001";

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

const SIGNED_RECORD = {
  checkpoint: {
    checkpoint_id: CHECKPOINT_ID,
    tenant_id: "tenant-alpha",
    chain_head_hash:
      "chain-head-hash-001",
    checked_count: 459,
    valid: true,
    reason_code: null,
    created_at:
      "2026-08-02T20:00:00Z",
    checkpoint_version: "1.0.0"
  },
  key_id:
    "assessment-local-2026-01",
  signature:
    "signature-value-001",
  signature_algorithm:
    "hmac-sha256",
  signature_version: "1.0.0"
};

function configureHealthyBackend() {
  mockedFetchRecords.mockResolvedValue({
    tenant_id: "tenant-alpha",
    items: [SIGNED_RECORD],
    count: 1,
    limit: 100
  });

  mockedFetchVerification.mockResolvedValue({
    tenant_id: "tenant-alpha",
    items: [
      {
        checkpoint_id: CHECKPOINT_ID,
        key_id:
          "assessment-local-2026-01",
        valid: true,
        reason_code: null
      }
    ],
    count: 1,
    valid_count: 1,
    invalid_count: 0,
    limit: 100
  });

  mockedDetectCapability.mockResolvedValue({
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

  mockedCreateCheckpoint.mockResolvedValue({
    checkpoint: {
      checkpoint_id:
        "checkpoint-integration-002",
      tenant_id: "tenant-alpha",
      chain_head_hash:
        "chain-head-hash-002",
      checked_count: 460,
      valid: true,
      reason_code: null,
      created_at:
        "2026-08-02T20:05:00Z",
      checkpoint_version: "1.0.0"
    },
    key_id:
      "assessment-local-2026-01",
    signature:
      "signature-value-002",
    signature_algorithm:
      "hmac-sha256",
    signature_version: "1.0.0",
    signed: true
  });
}

describe(
  "SignedCheckpointsPage integration",
  () => {
    beforeEach(() => {
      vi.clearAllMocks();

      window.history.replaceState(
        {},
        "",
        "/signed-checkpoints"
      );
    });

    it(
      "loads healthy signing state and creates a signed checkpoint",
      async () => {
        const user = userEvent.setup();

        configureHealthyBackend();

        render(<SignedCheckpointsPage />);

        expect(
          await screen.findByRole(
            "heading",
            {
              name:
                "Durable signing available"
            }
          )
        ).toBeInTheDocument();

        expect(
          screen.getAllByText(
            "assessment-local-2026-01"
          ).length
        ).toBeGreaterThan(0);

        expect(
          await screen.findByText(
            CHECKPOINT_ID
          )
        ).toBeInTheDocument();

        expect(
          screen.getByText(
            "Signature valid"
          )
        ).toBeInTheDocument();

        const createButton =
          screen.getByRole(
            "button",
            {
              name:
                "Create signed checkpoint"
            }
          );

        expect(createButton).toBeEnabled();

        await user.click(createButton);

        expect(
          screen.getByRole(
            "dialog",
            {
              name:
                "Create a signed checkpoint?"
            }
          )
        ).toBeInTheDocument();

        await user.click(
          screen.getByRole(
            "button",
            {
              name: "Create and sign"
            }
          )
        );

        await waitFor(() => {
          expect(
            mockedCreateCheckpoint
          ).toHaveBeenCalledTimes(1);
        });

        expect(
          await screen.findByText(
            "Signed checkpoint created"
          )
        ).toBeInTheDocument();

        expect(
          screen.getByText(
            "checkpoint-integration-002"
          )
        ).toBeInTheDocument();

        expect(
          screen.getByText(
            /was created and signed/i
          )
        ).toBeInTheDocument();

        await waitFor(() => {
          expect(
            mockedFetchRecords
          ).toHaveBeenCalledTimes(2);

          expect(
            mockedFetchVerification
          ).toHaveBeenCalledTimes(2);

          expect(
            mockedDetectCapability
          ).toHaveBeenCalledTimes(2);
        });
      }
    );

    it(
      "preserves signed evidence when durable signing is unconfigured",
      async () => {
        mockedFetchRecords.mockResolvedValue({
          tenant_id: "tenant-alpha",
          items: [SIGNED_RECORD],
          count: 1,
          limit: 100
        });

        mockedFetchVerification.mockResolvedValue({
          tenant_id: "tenant-alpha",
          items: [
            {
              checkpoint_id:
                CHECKPOINT_ID,
              key_id:
                "assessment-local-2026-01",
              valid: true,
              reason_code: null
            }
          ],
          count: 1,
          valid_count: 1,
          invalid_count: 0,
          limit: 100
        });

        mockedDetectCapability.mockResolvedValue({
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

        render(<SignedCheckpointsPage />);

        expect(
          await screen.findByRole(
            "heading",
            {
              name:
                "Durable signing is not configured"
            }
          )
        ).toBeInTheDocument();

        expect(
          screen.getByText(
            "Not configured"
          )
        ).toBeInTheDocument();

        expect(
          screen.getByText(
            /remain available in read-only mode/i
          )
        ).toBeInTheDocument();

        const createButton =
          screen.getByRole(
            "button",
            {
              name:
                "Create signed checkpoint"
            }
          );

        expect(createButton).toBeDisabled();

        expect(createButton).toHaveAttribute(
          "aria-describedby",
          "signed-checkpoint-capability-help"
        );

        expect(createButton).toHaveAttribute(
          "title",
          "No active durable signing key is available for this tenant."
        );

        expect(
          screen.getByText(
            CHECKPOINT_ID
          )
        ).toBeInTheDocument();

        expect(
          screen.getByText(
            "Signature valid"
          )
        ).toBeInTheDocument();

        expect(
          screen.getByText(
            "Signed checkpoint inventory"
          )
        ).toBeInTheDocument();

        expect(
          mockedCreateCheckpoint
        ).not.toHaveBeenCalled();
      }
    );

    it(
      "preserves signed evidence when signing access is unauthorized",
      async () => {
        configureHealthyBackend();

        mockedDetectCapability.mockResolvedValue({
          status: "unauthorized",
          available: false,
          title:
            "Signing access is unauthorized",
          message:
            "Your current identity is not authorized to use durable checkpoint signing.",
          activeKey: null,
          statusCode: 403,
          reasonCode:
            "CHECKPOINT_SIGNING_FORBIDDEN"
        });

        render(<SignedCheckpointsPage />);

        expect(
          await screen.findByRole(
            "heading",
            {
              name:
                "Signing access is unauthorized"
            }
          )
        ).toBeInTheDocument();

        const createButton =
          screen.getByRole(
            "button",
            {
              name:
                "Create signed checkpoint"
            }
          );

        expect(createButton).toBeDisabled();

        expect(createButton).toHaveAttribute(
          "title",
          "Your current identity is not authorized to use durable checkpoint signing."
        );

        expect(
          screen.getByText(
            CHECKPOINT_ID
          )
        ).toBeInTheDocument();

        expect(
          screen.getByText(
            "Signature valid"
          )
        ).toBeInTheDocument();

        expect(
          screen.getByText(
            "Signed checkpoint inventory"
          )
        ).toBeInTheDocument();

        expect(
          screen.queryByText(
            /signed checkpoint data could not be loaded/i
          )
        ).not.toBeInTheDocument();

        expect(
          mockedCreateCheckpoint
        ).not.toHaveBeenCalled();
      }
    );

    it(
      "preserves evidence while unreachable and recovers after a page refresh",
      async () => {
        configureHealthyBackend();

        mockedDetectCapability
          .mockResolvedValueOnce({
            status: "unreachable",
            available: false,
            title:
              "Signing service is unreachable",
            message:
              "The Console could not reach the durable signing service.",
            activeKey: null,
            statusCode: null,
            reasonCode:
              "SIGNING_SERVICE_UNREACHABLE"
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

        const firstRender =
          render(<SignedCheckpointsPage />);

        expect(
          await screen.findByRole(
            "heading",
            {
              name:
                "Signing service is unreachable"
            }
          )
        ).toBeInTheDocument();

        const unavailableButton =
          screen.getByRole(
            "button",
            {
              name:
                "Create signed checkpoint"
            }
          );

        expect(
          unavailableButton
        ).toBeDisabled();

        expect(
          screen.getByText(
            CHECKPOINT_ID
          )
        ).toBeInTheDocument();

        expect(
          screen.getByText(
            "Signature valid"
          )
        ).toBeInTheDocument();

        expect(
          mockedCreateCheckpoint
        ).not.toHaveBeenCalled();

        firstRender.unmount();

        render(<SignedCheckpointsPage />);

        expect(
          await screen.findByRole(
            "heading",
            {
              name:
                "Durable signing available"
            }
          )
        ).toBeInTheDocument();

        const recoveredButton =
          screen.getByRole(
            "button",
            {
              name:
                "Create signed checkpoint"
            }
          );

        expect(recoveredButton).toBeEnabled();

        expect(
          screen.getByText(
            CHECKPOINT_ID
          )
        ).toBeInTheDocument();

        expect(
          screen.queryByRole(
            "heading",
            {
              name:
                "Signing service is unreachable"
            }
          )
        ).not.toBeInTheDocument();

        await waitFor(() => {
          expect(
            mockedDetectCapability
          ).toHaveBeenCalledTimes(2);

          expect(
            mockedFetchRecords
          ).toHaveBeenCalledTimes(2);

          expect(
            mockedFetchVerification
          ).toHaveBeenCalledTimes(2);
        });
      }
    );

  }
);
