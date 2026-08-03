import {
  render
} from "@testing-library/react";

import {
  describe,
  it,
  vi
} from "vitest";

import {
  SigningCapabilityAction
} from "./signing-capability-action";

import {
  createAvailableSigningCapability,
  createUnauthorizedSigningCapability,
  createUnconfiguredSigningCapability,
  createUnreachableSigningCapability
} from "@/test/governance-assessment-fixtures";

import {
  expectNoAccessibilityViolations
} from "@/test/accessibility-harness";

describe(
  "SigningCapabilityAction accessibility",
  () => {
    it(
      "has no automated violations when enabled",
      async () => {
        const { container } = render(
          <SigningCapabilityAction
            capability={
              createAvailableSigningCapability()
            }
            busy={false}
            loading={false}
            onActivate={vi.fn()}
          />
        );

        await expectNoAccessibilityViolations(
          container
        );
      }
    );

    it.each([
      [
        "unconfigured",
        createUnconfiguredSigningCapability()
      ],
      [
        "unauthorized",
        createUnauthorizedSigningCapability()
      ],
      [
        "unreachable",
        createUnreachableSigningCapability()
      ]
    ])(
      "has no automated violations when %s",
      async (_, capability) => {
        const { container } = render(
          <SigningCapabilityAction
            capability={capability}
            busy={false}
            loading={false}
            onActivate={vi.fn()}
          />
        );

        await expectNoAccessibilityViolations(
          container
        );
      }
    );
  }
);
