import {
  render
} from "@testing-library/react";

import {
  describe,
  it
} from "vitest";

import {
  SigningCapabilityPanel
} from "./signing-capability-panel";

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
  "SigningCapabilityPanel accessibility",
  () => {
    it(
      "has no automated violations in the available state",
      async () => {
        const { container } = render(
          <SigningCapabilityPanel
            capability={
              createAvailableSigningCapability()
            }
          />
        );

        await expectNoAccessibilityViolations(
          container
        );
      }
    );

    it(
      "has no automated violations in the unconfigured state",
      async () => {
        const { container } = render(
          <SigningCapabilityPanel
            capability={
              createUnconfiguredSigningCapability()
            }
          />
        );

        await expectNoAccessibilityViolations(
          container
        );
      }
    );

    it(
      "has no automated violations in the unauthorized state",
      async () => {
        const { container } = render(
          <SigningCapabilityPanel
            capability={
              createUnauthorizedSigningCapability()
            }
          />
        );

        await expectNoAccessibilityViolations(
          container
        );
      }
    );

    it(
      "has no automated violations in the unreachable state",
      async () => {
        const { container } = render(
          <SigningCapabilityPanel
            capability={
              createUnreachableSigningCapability()
            }
          />
        );

        await expectNoAccessibilityViolations(
          container
        );
      }
    );
  }
);
