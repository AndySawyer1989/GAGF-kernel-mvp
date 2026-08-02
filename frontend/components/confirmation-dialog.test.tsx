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
  ConfirmationDialog
} from "./confirmation-dialog";

describe("ConfirmationDialog", () => {
  it("renders an accessible modal dialog", () => {
    render(
      <ConfirmationDialog
        confirmLabel="Create checkpoint"
        description="Create an immutable checkpoint."
        onCancel={vi.fn()}
        onConfirm={vi.fn()}
        open
        title="Create a checkpoint?"
      />
    );

    const dialog =
      screen.getByRole("dialog");

    expect(dialog).toHaveAttribute(
      "aria-modal",
      "true"
    );

    expect(
      screen.getByRole(
        "heading",
        {
          name: "Create a checkpoint?"
        }
      )
    ).toBeInTheDocument();
  });

  it("focuses the safe cancel action first", () => {
    render(
      <ConfirmationDialog
        confirmLabel="Create checkpoint"
        description="Create an immutable checkpoint."
        onCancel={vi.fn()}
        onConfirm={vi.fn()}
        open
        title="Create a checkpoint?"
      />
    );

    expect(
      screen.getByRole(
        "button",
        {
          name: "Cancel"
        }
      )
    ).toHaveFocus();
  });

  it("calls the confirm handler", async () => {
    const user = userEvent.setup();
    const onConfirm = vi.fn();

    render(
      <ConfirmationDialog
        confirmLabel="Create checkpoint"
        description="Create an immutable checkpoint."
        onCancel={vi.fn()}
        onConfirm={onConfirm}
        open
        title="Create a checkpoint?"
      />
    );

    await user.click(
      screen.getByRole(
        "button",
        {
          name: "Create checkpoint"
        }
      )
    );

    expect(
      onConfirm
    ).toHaveBeenCalledTimes(1);
  });

  it("closes through Escape when not busy", async () => {
    const user = userEvent.setup();
    const onCancel = vi.fn();

    render(
      <ConfirmationDialog
        confirmLabel="Create checkpoint"
        description="Create an immutable checkpoint."
        onCancel={onCancel}
        onConfirm={vi.fn()}
        open
        title="Create a checkpoint?"
      />
    );

    await user.keyboard("{Escape}");

    expect(
      onCancel
    ).toHaveBeenCalledTimes(1);
  });

  it("does not close through Escape while busy", async () => {
    const user = userEvent.setup();
    const onCancel = vi.fn();

    render(
      <ConfirmationDialog
        busy
        confirmLabel="Create checkpoint"
        description="Create an immutable checkpoint."
        onCancel={onCancel}
        onConfirm={vi.fn()}
        open
        title="Create a checkpoint?"
      />
    );

    await user.keyboard("{Escape}");

    expect(
      onCancel
    ).not.toHaveBeenCalled();
  });

  it("cycles focus within the dialog", async () => {
    const user = userEvent.setup();

    render(
      <ConfirmationDialog
        confirmLabel="Create checkpoint"
        description="Create an immutable checkpoint."
        onCancel={vi.fn()}
        onConfirm={vi.fn()}
        open
        title="Create a checkpoint?"
      />
    );

    const cancel = screen.getByRole(
      "button",
      {
        name: "Cancel"
      }
    );

    const confirm = screen.getByRole(
      "button",
      {
        name: "Create checkpoint"
      }
    );

    expect(cancel).toHaveFocus();

    await user.tab();
    expect(confirm).toHaveFocus();

    await user.tab();
    expect(cancel).toHaveFocus();

    await user.tab({
      shift: true
    });
    expect(confirm).toHaveFocus();
  });
});
