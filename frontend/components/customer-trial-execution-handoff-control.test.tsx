import {
  fireEvent,
  render,
  screen
} from "@testing-library/react";

import {
  describe,
  expect,
  it,
  vi
} from "vitest";

import {
  CustomerTrialExecutionHandoffControl
} from "./customer-trial-execution-handoff-control";


function renderControl(
  overrides: Partial<
    React.ComponentProps<
      typeof CustomerTrialExecutionHandoffControl
    >
  > = {}
) {
  const onPrepare =
    vi.fn();

  const props = {
    trialReady:
      true,

    authorizationComplete:
      true,

    bindingAvailable:
      true,

    handoffPrepared:
      false,

    preparing:
      false,

    error:
      null,

    onPrepare,

    ...overrides
  };

  render(
    <CustomerTrialExecutionHandoffControl
      {...props}
    />
  );

  return {
    onPrepare
  };
}


describe(
  "CustomerTrialExecutionHandoffControl",
  () => {
    it(
      "enables explicit preparation when all prerequisites are satisfied",
      () => {
        renderControl();

        const button =
          screen.getByRole(
            "button",
            {
              name:
                "Prepare execution handoff"
            }
          );

        expect(
          button
        ).toBeEnabled();

        expect(
          screen.getByText(
            "Ready to prepare"
          )
        ).toBeInTheDocument();
      }
    );


    it(
      "invokes the explicit operator action",
      () => {
        const {
          onPrepare
        } =
          renderControl();

        fireEvent.click(
          screen.getByRole(
            "button",
            {
              name:
                "Prepare execution handoff"
            }
          )
        );

        expect(
          onPrepare
        ).toHaveBeenCalledTimes(
          1
        );
      }
    );


    it(
      "blocks preparation without trial readiness",
      () => {
        renderControl({
          trialReady:
            false
        });

        expect(
          screen.getByRole(
            "button"
          )
        ).toBeDisabled();

        expect(
          screen.getByText(
            "Controlled-trial preflight is required."
          )
        ).toBeInTheDocument();
      }
    );


    it(
      "blocks preparation without completed authorization",
      () => {
        renderControl({
          authorizationComplete:
            false
        });

        expect(
          screen.getByRole(
            "button"
          )
        ).toBeDisabled();

        expect(
          screen.getByText(
            (
              "Complete contract execution and "
              + "paid-work authorization before "
              + "preparing the handoff."
            )
          )
        ).toBeInTheDocument();
      }
    );


    it(
      "blocks preparation without the governed binding",
      () => {
        renderControl({
          bindingAvailable:
            false
        });

        expect(
          screen.getByRole(
            "button"
          )
        ).toBeDisabled();

        expect(
          screen.getByText(
            (
              "The governed execution-input "
              + "binding must be available."
            )
          )
        ).toBeInTheDocument();
      }
    );


    it(
      "locks the control after the handoff is prepared",
      () => {
        renderControl({
          handoffPrepared:
            true
        });

        expect(
          screen.getByRole(
            "button",
            {
              name:
                "Handoff prepared"
            }
          )
        ).toBeDisabled();

        expect(
          screen.getAllByText(
            "Handoff prepared"
          ).length
        ).toBeGreaterThan(
          0
        );
      }
    );


    it(
      "locks the control while preparation is in progress",
      () => {
        renderControl({
          preparing:
            true
        });

        expect(
          screen.getByRole(
            "button",
            {
              name:
                "Preparing handoff..."
            }
          )
        ).toBeDisabled();
      }
    );


    it(
      "shows governed preparation failures",
      () => {
        renderControl({
          error:
            (
              "customer trial preflight "
              + "receipt required"
            )
        });

        expect(
          screen.getByRole(
            "alert"
          )
        ).toHaveTextContent(
          (
            "customer trial preflight "
            + "receipt required"
          )
        );
      }
    );


    it(
      "states that preparation is not execution authority",
      () => {
        renderControl();

        expect(
          screen.getByText(
            /does not execute the assessment/i
          )
        ).toBeInTheDocument();

        expect(
          screen.getByText(
            /handoff preparation is not execution authority/i
          )
        ).toBeInTheDocument();
      }
    );
  }
);