import {
  render,
  screen
} from "@testing-library/react";
import {
  describe,
  expect,
  it
} from "vitest";

import {
  CustomerTrialStatusPanel
} from "./customer-trial-status-panel";


const preflight = {
  status: "ok",
  api_version: "1.0.0",
  authority: "READ_ONLY" as const,
  result: {
    receipt_found: true,
    receipt: {
      package_hash: "package-hash-001",
      receipt_hash: "preflight-receipt-001"
    }
  },
  boundaries: {
    status_is_read_only: true
  }
};


const handoff = {
  status: "ok",
  api_version: "1.0.0",
  authority: "READ_ONLY" as const,
  result: {
    receipt_found: true,
    receipt: {
      receipt_hash:
        "handoff-receipt-001",
      lineage_hash:
        "handoff-lineage-001",
      execution_handoff_lineage: {
        handoff_hash:
          "paid-handoff-001"
      }
    }
  },
  boundaries: {
    status_is_read_only: true,
    status_is_not_execution_authority:
      true,
    status_is_not_recovery_authority:
      true,
    status_is_not_delivery_authority:
      true,
    status_is_not_closeout_authority:
      true,
    status_is_not_intervention_authority:
      true
  }
};


describe(
  "CustomerTrialStatusPanel",
  () => {
    it(
      "shows governed trial readiness and handoff evidence",
      () => {
        render(
          <CustomerTrialStatusPanel
            preflight={preflight}
            handoff={handoff}
          />
        );

        expect(
          screen.getByText(
            "Trial readiness and execution handoff"
          )
        ).toBeInTheDocument();

        expect(
          screen.getByText(
            "Trial ready"
          )
        ).toBeInTheDocument();

        expect(
          screen.getAllByText(
            "Handoff prepared"
          ).length
        ).toBeGreaterThan(0);

        expect(
          screen.getByText(
            "package-hash-001"
          )
        ).toBeInTheDocument();

        expect(
          screen.getByText(
            "preflight-receipt-001"
          )
        ).toBeInTheDocument();

        expect(
          screen.getByText(
            "paid-handoff-001"
          )
        ).toBeInTheDocument();

        expect(
          screen.getByText(
            "handoff-lineage-001"
          )
        ).toBeInTheDocument();
      }
    );


    it(
      "shows a preflight-required state",
      () => {
        render(
          <CustomerTrialStatusPanel
            preflight={{
              ...preflight,
              result: {
                receipt_found: false,
                receipt: null
              }
            }}
            handoff={{
              ...handoff,
              result: {
                receipt_found: false,
                receipt: null
              }
            }}
          />
        );

        expect(
          screen.getByText(
            "Preflight required"
          )
        ).toBeInTheDocument();

        expect(
          screen.getByText(
            "Preflight not recorded"
          )
        ).toBeInTheDocument();

        expect(
          screen.getByText(
            "Handoff unavailable"
          )
        ).toBeInTheDocument();
      }
    );


    it(
      "states the authority boundary explicitly",
      () => {
        render(
          <CustomerTrialStatusPanel
            preflight={preflight}
            handoff={handoff}
          />
        );

        expect(
          screen.getByText(
            /Trial readiness is not execution authority/
          )
        ).toBeInTheDocument();

        expect(
          screen.getByText(
            /prepared handoff is not an executed assessment/
          )
        ).toBeInTheDocument();
      }
    );


    it(
      "renders restoration state without inventing authority",
      () => {
        render(
          <CustomerTrialStatusPanel
            preflight={null}
            handoff={null}
            loading
          />
        );

        expect(
          screen.getByText(
            "Restoring trial state"
          )
        ).toBeInTheDocument();

        expect(
          screen.queryByText(
            "Handoff prepared"
          )
        ).not.toBeInTheDocument();
      }
    );
  }
);