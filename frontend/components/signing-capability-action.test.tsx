import {
  render,
  screen
} from "@testing-library/react";

import userEvent from "@testing-library/user-event";

import {
  describe,
  expect,
  it,
  vi
} from "vitest";

import {
  SigningCapabilityAction
} from "./signing-capability-action";

import type {
  SigningCapability,
  SigningCapabilityStatus
} from "@/lib/signing-capability";

function capability(
  status: SigningCapabilityStatus
): SigningCapability {
  const available =
    status === "available";

  return {
    status,
    available,
    title:
      available
        ? "Durable signing available"
        : "Signing unavailable",
    message:
      available
        ? "Signing is ready."
        : `Signing state is ${status}.`,
    activeKey:
      available
        ? {
            tenant_id: "tenant-alpha",
            key_id:
              "assessment-local-2026-01",
            secret_reference:
              "env://CHECKPOINT_SECRET",
            active: true,
            created_at:
              "2026-08-02T12:00:00Z",
            retired_at: null
          }
        : null,
    statusCode:
      status === "unauthorized"
        ? 403
        : null,
    reasonCode: null
  };
}

describe("SigningCapabilityAction", () => {
  it("enables creation when signing is available", async () => {
    const user = userEvent.setup();
    const onActivate = vi.fn();

    render(
      <SigningCapabilityAction
        capability={capability("available")}
        onActivate={onActivate}
      />
    );

    const button = screen.getByRole(
      "button",
      {
        name: "Create signed checkpoint"
      }
    );

    expect(button).toBeEnabled();

    await user.click(button);

    expect(
      onActivate
    ).toHaveBeenCalledTimes(1);
  });

  it.each([
    "unconfigured",
    "unauthorized",
    "unreachable",
    "error"
  ] as const)(
    "disables creation when capability is %s",
    (status) => {
      render(
        <SigningCapabilityAction
          capability={capability(status)}
          onActivate={vi.fn()}
        />
      );

      const button =
        screen.getByRole(
          "button",
          {
            name:
              "Create signed checkpoint"
          }
        );

      expect(button).toBeDisabled();

      expect(button).toHaveAttribute(
        "aria-describedby",
        "signed-checkpoint-capability-help"
      );

      expect(button).toHaveAttribute(
        "title",
        `Signing state is ${status}.`
      );
    }
  );

  it("disables creation while capability is loading", () => {
    render(
      <SigningCapabilityAction
        capability={capability("loading")}
        onActivate={vi.fn()}
      />
    );

    expect(
      screen.getByRole(
        "button",
        {
          name: "Checking signing..."
        }
      )
    ).toBeDisabled();
  });

  it("disables creation during record loading", () => {
    render(
      <SigningCapabilityAction
        capability={capability("available")}
        loading
        onActivate={vi.fn()}
      />
    );

    expect(
      screen.getByRole(
        "button",
        {
          name:
            "Create signed checkpoint"
        }
      )
    ).toBeDisabled();
  });

  it("shows a busy operation state", () => {
    render(
      <SigningCapabilityAction
        busy
        capability={capability("available")}
        onActivate={vi.fn()}
      />
    );

    expect(
      screen.getByRole(
        "button",
        {
          name:
            "Creating signed checkpoint..."
        }
      )
    ).toBeDisabled();
  });
});
