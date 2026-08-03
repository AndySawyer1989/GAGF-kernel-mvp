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
  TEST_SIGNING_KEY_ID,
  createAuditCheckpoint as createAuditCheckpointFixture,
  createAuditCheckpointList,
  createAuditEvent,
  createAuditEventList,
  createAuditIntegrity,
  createAvailableSigningCapability,
  createSignedCheckpointList,
  createTestApiConfig,
  createUnconfiguredSigningCapability
} from "@/test/governance-assessment-fixtures";

import {
  createGovernanceAssessmentMockHarness
} from "@/test/governance-assessment-mock-harness";

import {
  expectNoAccessibilityViolations
} from "@/test/accessibility-harness";

import {
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

const harness =
  createGovernanceAssessmentMockHarness();

const mockedFetchEvents =
  harness.fetchAuditEvents;

const mockedFetchIntegrity =
  harness.fetchAuditIntegrity;

const mockedFetchCheckpoints =
  harness.fetchAuditCheckpoints;

const mockedFetchSignedCheckpoints =
  harness.fetchSignedAuditCheckpoints;

const mockedVerifySignedCheckpoints =
  harness.verifySignedAuditCheckpoints;

const mockedDetectCapability =
  harness.detectSigningCapability;

const mockedCreateCheckpoint =
  harness.createAuditCheckpoint;

const CORE_CHECKPOINT_ID =
  "checkpoint-core-001";

const CORE_EVENT_ID =
  "audit-event-core-001";

function configureCoreAuditData() {
  mockedFetchEvents.mockResolvedValue(
    createAuditEventList({
      items: [
        createAuditEvent({
          event_id: CORE_EVENT_ID,
          request_id:
            "request-core-001",
          actor_id:
            "integration-operator"
        })
      ]
    })
  );

  mockedFetchIntegrity.mockResolvedValue(
    createAuditIntegrity({
      checked_count: 461
    })
  );

  mockedFetchCheckpoints.mockResolvedValue(
    createAuditCheckpointList({
      items: [
        createAuditCheckpointFixture({
          checkpoint_id:
            CORE_CHECKPOINT_ID,
          chain_head_hash:
            "core-chain-head-hash",
          checked_count: 461
        })
      ]
    })
  );
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

  mockedDetectCapability.mockResolvedValue(
    createUnconfiguredSigningCapability()
  );
}

function configureHealthyOptionalServices() {
  mockedFetchSignedCheckpoints
    .mockResolvedValue(
      createSignedCheckpointList({
        items: [
          {
            checkpoint_id:
              "signed-checkpoint-001",
            key_id:
              TEST_SIGNING_KEY_ID
          }
        ]
      })
    );

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

  mockedDetectCapability.mockResolvedValue(
    createAvailableSigningCapability()
  );
}

describe(
  "AuditIntegrityPage integration",
  () => {
    beforeEach(() => {
      harness.clear();

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

        const {
          container: degradedContainer
        } = render(
          <AuditIntegrityPage />
        );

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

        await expectNoAccessibilityViolations(
          degradedContainer
        );

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
          .mockResolvedValue(
            createSignedCheckpointList({
              items: [
                {
                  checkpoint_id:
                    "signed-checkpoint-001",
                  key_id:
                    TEST_SIGNING_KEY_ID
                }
              ]
            })
          );

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
          .mockResolvedValueOnce(
            createUnconfiguredSigningCapability()
          )
          .mockResolvedValue(
            createAvailableSigningCapability()
          );

        const {
          container: recoveredContainer
        } = render(
          <AuditIntegrityPage />
        );

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

        await expectNoAccessibilityViolations(
          recoveredContainer
        );

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

    it(
      "exposes page semantics and announces optional-service degradation",
      async () => {
        configureDegradedOptionalServices();

        const {
          container
        } = render(
          <AuditIntegrityPage />
        );

        const degradationMessage =
          await screen.findByText(
            "Optional cryptographic services degraded"
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

        const statusRegion =
          degradationMessage.closest(
            '[role="status"]'
          );

        expect(statusRegion).not.toBeNull();

        expect(
          screen.getByRole(
            "heading",
            {
              name: "Chain verification"
            }
          )
        ).toBeInTheDocument();

        expect(
          screen.getByText(
            "integration-operator"
          )
        ).toBeInTheDocument();

        await expectNoAccessibilityViolations(
          container
        );
      }
    );

  }
);
