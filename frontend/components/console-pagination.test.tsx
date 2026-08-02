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
  ConsolePagination
} from "./console-pagination";

describe("ConsolePagination", () => {
  it("shows the current visible range", () => {
    render(
      <ConsolePagination
        currentPage={2}
        label="Audit events"
        onPageChange={vi.fn()}
        pageSize={15}
        totalItems={40}
      />
    );

    expect(
      screen.getByText(
        "Showing 16 to 30 of 40"
      )
    ).toBeInTheDocument();

    expect(
      screen.getByText(
        "Page 2 of 3"
      )
    ).toBeInTheDocument();
  });

  it("moves to the previous and next pages", async () => {
    const user = userEvent.setup();
    const onPageChange = vi.fn();

    render(
      <ConsolePagination
        currentPage={2}
        label="Audit events"
        onPageChange={onPageChange}
        pageSize={15}
        totalItems={40}
      />
    );

    await user.click(
      screen.getByRole(
        "button",
        {
          name: "Previous Audit events page"
        }
      )
    );

    expect(
      onPageChange
    ).toHaveBeenCalledWith(1);

    await user.click(
      screen.getByRole(
        "button",
        {
          name: "Next Audit events page"
        }
      )
    );

    expect(
      onPageChange
    ).toHaveBeenCalledWith(3);
  });

  it("disables unavailable directions", () => {
    render(
      <ConsolePagination
        currentPage={1}
        label="Checkpoints"
        onPageChange={vi.fn()}
        pageSize={5}
        totalItems={3}
      />
    );

    expect(
      screen.getByRole(
        "button",
        {
          name: "Previous Checkpoints page"
        }
      )
    ).toBeDisabled();

    expect(
      screen.getByRole(
        "button",
        {
          name: "Next Checkpoints page"
        }
      )
    ).toBeDisabled();
  });

  it("shows an empty-state range", () => {
    render(
      <ConsolePagination
        currentPage={1}
        label="Signed checkpoints"
        onPageChange={vi.fn()}
        pageSize={5}
        totalItems={0}
      />
    );

    expect(
      screen.getByText(
        "No signed checkpoints"
      )
    ).toBeInTheDocument();
  });
});
