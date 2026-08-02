import {
  render,
  screen
} from "@testing-library/react";

import userEvent from "@testing-library/user-event";

import {
  describe,
  expect,
  it
} from "vitest";

import {
  ConsoleSidebar
} from "./console-sidebar";

describe("ConsoleSidebar", () => {
  it("marks the current navigation destination", () => {
    render(
      <ConsoleSidebar
        activePage="signed-checkpoints"
        actorId="console-admin"
        tenantId="tenant-alpha"
      />
    );

    expect(
      screen.getByRole(
        "link",
        {
          name: "Signed Checkpoints"
        }
      )
    ).toHaveAttribute(
      "aria-current",
      "page"
    );
  });

  it("opens the mobile navigation", async () => {
    const user = userEvent.setup();

    render(
      <ConsoleSidebar
        activePage="overview"
        actorId="console-admin"
        tenantId="tenant-alpha"
      />
    );

    const menuButton =
      screen.getByRole(
        "button",
        {
          name: "Open navigation menu"
        }
      );

    expect(menuButton).toHaveAttribute(
      "aria-expanded",
      "false"
    );

    await user.click(menuButton);

    expect(menuButton).toHaveAttribute(
      "aria-expanded",
      "true"
    );

    const navigation =
      screen.getByLabelText(
        "Governance Console navigation"
      );

    expect(navigation).toHaveClass(
      "sidebar-mobile-open"
    );

    expect(navigation).toHaveAttribute(
      "role",
      "dialog"
    );

    expect(
      screen.getAllByRole(
        "button",
        {
          name: "Close navigation menu"
        }
      )
    ).toHaveLength(3);

    expect(
      document.body.style.overflow
    ).toBe("hidden");
  });

  it("closes the mobile navigation with Escape", async () => {
    const user = userEvent.setup();

    render(
      <ConsoleSidebar
        activePage="overview"
        actorId="console-admin"
        tenantId="tenant-alpha"
      />
    );

    const menuButton =
      screen.getByRole(
        "button",
        {
          name: "Open navigation menu"
        }
      );

    await user.click(menuButton);
    await user.keyboard("{Escape}");

    expect(menuButton).toHaveAttribute(
      "aria-expanded",
      "false"
    );

    expect(menuButton).toHaveFocus();

    expect(
      screen.getByLabelText(
        "Governance Console navigation"
      )
    ).not.toHaveClass(
      "sidebar-mobile-open"
    );

    expect(
      document.body.style.overflow
    ).toBe("");
  });

  it("shows tenant and actor identity", () => {
    render(
      <ConsoleSidebar
        activePage="overview"
        actorId="console-admin"
        tenantId="tenant-alpha"
      />
    );

    expect(
      screen.getByText("tenant-alpha")
    ).toBeInTheDocument();

    expect(
      screen.getByText("console-admin")
    ).toBeInTheDocument();
  });
});
