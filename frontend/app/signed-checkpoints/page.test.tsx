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
  TEST_SIGNING_KEY_ID,
  createAvailableSigningCapability,
  createAuditCheckpoint,
  createSignedCheckpointList,
  createSignedCheckpointRecord,
  createSignedVerificationList,
  createTestApiConfig,
  createUnauthorizedSigningCapability,
  createUnconfiguredSigningCapability,
  createUnreachableSigningCapability
} from "@/test/governance-assessment-fixtures";

import {
  createGovernanceAssessmentMockHarness
} from "@/test/governance-assessment-mock-harness";

import {
  expectNoAccessibilityViolations
} from "@/test/accessibility-harness";

import {
  expectDescribedControl,
  expectNavigationLandmark,
  expectSinglePrimaryHeading,
  expectSkipLinkTarget
} from "@/test/page-accessibility-assertions";

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
        vi.fn(() =>
          createTestApiConfig()
        ),
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

const harness =
  createGovernanceAssessmentMockHarness();

const mockedFetchRecords =
  harness.fetchSignedAuditCheckpointRecords;

const mockedFetchVerification =
  harness.fetchSignedAuditCheckpointVerificationRecords;

const mockedCreateCheckpoint =
  harness.createSignedAuditCheckpoint;

const mockedDetectCapability =
  harness.detectSigningCapability;

const CHECKPOINT_ID =
  "checkpoint-integration-001";

const SIGNED_RECORD =
  createSignedCheckpointRecord({
    checkpoint: createAuditCheckpoint({
      checkpoint_id: CHECKPOINT_ID,
      checked_count: 459,
      created_at:
        "2026-08-02T20:00:00Z"
    })
  });

function configureHealthyBackend() {
  mockedFetchRecords.mockResolvedValue(
    createSignedCheckpointList({
      items: [SIGNED_RECORD]
    })
  );

  mockedFetchVerification.mockResolvedValue(
    createSignedVerificationList({
      items: [
        {
          checkpoint_id: CHECKPOINT_ID,
          key_id:
            TEST_SIGNING_KEY_ID,
          valid: true,
          reason_code: null
        }
      ]
    })
  );

  mockedDetectCapability.mockResolvedValue(
    createAvailableSigningCapability()
  );

  mockedCreateCheckpoint.mockResolvedValue({
    checkpoint: createAuditCheckpoint({
      checkpoint_id:
        "checkpoint-integration-002",
      chain_head_hash:
        "chain-head-hash-002",
      checked_count: 460,
      created_at:
        "2026-08-02T20:05:00Z"
    }),
    key_id: TEST_SIGNING_KEY_ID,
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
      harness.clear();

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

        const {
          container: healthyContainer
        } = render(
          <SignedCheckpointsPage />
        );

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

        await expectNoAccessibilityViolations(
          healthyContainer
        );

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
        mockedFetchRecords.mockResolvedValue(
          createSignedCheckpointList({
            items: [SIGNED_RECORD]
          })
        );

        mockedFetchVerification.mockResolvedValue(
          createSignedVerificationList({
            items: [
              {
                checkpoint_id:
                  CHECKPOINT_ID,
                key_id:
                  TEST_SIGNING_KEY_ID,
                valid: true,
                reason_code: null
              }
            ]
          })
        );

        mockedDetectCapability.mockResolvedValue(
          createUnconfiguredSigningCapability()
        );

        const {
          container: degradedContainer
        } = render(
          <SignedCheckpointsPage />
        );

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

        await expectNoAccessibilityViolations(
          degradedContainer
        );

        expect(
          mockedCreateCheckpoint
        ).not.toHaveBeenCalled();
      }
    );

    it(
      "preserves signed evidence when signing access is unauthorized",
      async () => {
        configureHealthyBackend();

        mockedDetectCapability.mockResolvedValue(
          createUnauthorizedSigningCapability()
        );

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
          .mockResolvedValueOnce(
            createUnreachableSigningCapability()
          )
          .mockResolvedValue(
            createAvailableSigningCapability()
          );

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


    it(
      "supports an accessible keyboard-only confirmation workflow",
      async () => {
        const user = userEvent.setup();

        configureHealthyBackend();

        const {
          container
        } = render(
          <SignedCheckpointsPage />
        );

        await screen.findByRole(
          "heading",
          {
            name:
              "Durable signing available"
          }
        );

        const createButton =
          screen.getByRole(
            "button",
            {
              name:
                "Create signed checkpoint"
            }
          );

        createButton.focus();

        expect(createButton).toHaveFocus();

        await user.keyboard("{Enter}");

        const dialog =
          await screen.findByRole(
            "dialog",
            {
              name:
                "Create a signed checkpoint?"
            }
          );

        expect(dialog).toBeInTheDocument();

        expect(
          dialog.contains(
            document.activeElement
          )
        ).toBe(true);

        await expectNoAccessibilityViolations(
          container
        );

        await user.keyboard("{Escape}");

        await waitFor(() => {
          expect(
            screen.queryByRole(
              "dialog",
              {
                name:
                  "Create a signed checkpoint?"
              }
            )
          ).not.toBeInTheDocument();
        });

        expect(createButton).toHaveFocus();

        await user.keyboard("{Enter}");

        const reopenedDialog =
          await screen.findByRole(
            "dialog",
            {
              name:
                "Create a signed checkpoint?"
            }
          );

        expect(
          reopenedDialog.contains(
            document.activeElement
          )
        ).toBe(true);

        const confirmButton =
          screen.getByRole(
            "button",
            {
              name: "Create and sign"
            }
          );

        confirmButton.focus();

        expect(confirmButton).toHaveFocus();

        await user.keyboard("{Enter}");

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
          screen.queryByRole(
            "dialog",
            {
              name:
                "Create a signed checkpoint?"
            }
          )
        ).not.toBeInTheDocument();
      }
    );


    it(
      "exposes page semantics and explains disabled signing actions",
      async () => {
        mockedFetchRecords.mockResolvedValue(
          createSignedCheckpointList({
            items: [SIGNED_RECORD]
          })
        );

        mockedFetchVerification.mockResolvedValue(
          createSignedVerificationList({
            items: [
              {
                checkpoint_id:
                  CHECKPOINT_ID,
                key_id:
                  TEST_SIGNING_KEY_ID,
                valid: true,
                reason_code: null
              }
            ]
          })
        );

        mockedDetectCapability.mockResolvedValue(
          createUnconfiguredSigningCapability()
        );

        const {
          container
        } = render(
          <SignedCheckpointsPage />
        );

        await screen.findByRole(
          "heading",
          {
            name:
              "Durable signing is not configured"
          }
        );

        expectSinglePrimaryHeading(
          container
        );

        expectNavigationLandmark(
          container
        );

        expectSkipLinkTarget(
          container
        );

        const createButton =
          screen.getByRole(
            "button",
            {
              name:
                "Create signed checkpoint"
            }
          );

        expect(createButton).toBeDisabled();

        expectDescribedControl(
          createButton,
          container
        );

        await expectNoAccessibilityViolations(
          container
        );
      }
    );

  }
);
