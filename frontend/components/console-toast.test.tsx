import {
  act,
  render,
  screen
} from "@testing-library/react";

import userEvent from "@testing-library/user-event";

import {
  afterEach,
  beforeEach,
  describe,
  expect,
  it,
  vi
} from "vitest";

import {
  ConsoleToast
} from "./console-toast";

describe("ConsoleToast", () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("renders success feedback as a status", () => {
    render(
      <ConsoleToast
        message="Checkpoint created."
        onDismiss={vi.fn()}
        tone="success"
      />
    );

    expect(
      screen.getByRole("status")
    ).toHaveTextContent(
      "Checkpoint created."
    );
  });

  it("renders error feedback as an alert", () => {
    render(
      <ConsoleToast
        message="Checkpoint failed."
        onDismiss={vi.fn()}
        tone="error"
      />
    );

    expect(
      screen.getByRole("alert")
    ).toHaveTextContent(
      "Checkpoint failed."
    );
  });

  it("dismisses automatically", () => {
    const onDismiss = vi.fn();

    render(
      <ConsoleToast
        durationMs={2500}
        message="Checkpoint created."
        onDismiss={onDismiss}
      />
    );

    act(() => {
      vi.advanceTimersByTime(2500);
    });

    expect(
      onDismiss
    ).toHaveBeenCalledTimes(1);
  });

  it("supports manual dismissal", async () => {
    vi.useRealTimers();

    const user = userEvent.setup();
    const onDismiss = vi.fn();

    render(
      <ConsoleToast
        message="Checkpoint created."
        onDismiss={onDismiss}
      />
    );

    await user.click(
      screen.getByRole(
        "button",
        {
          name: "Dismiss notification"
        }
      )
    );

    expect(
      onDismiss
    ).toHaveBeenCalledTimes(1);
  });
});
