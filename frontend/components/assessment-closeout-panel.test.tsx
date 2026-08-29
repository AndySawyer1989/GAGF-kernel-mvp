import { render, screen } from "@testing-library/react";

import {
  AssessmentCloseoutPanel
} from "./assessment-closeout-panel";

describe("AssessmentCloseoutPanel", () => {
  it("shows pending state when no delivery receipt exists", () => {
    render(
      <AssessmentCloseoutPanel
        deliveryRecorded={false}
        reportId="report-001"
        packageHash="abc123"
      />
    );

    expect(
      screen.getByRole("heading", {
        name: "Delivery confirmation pending"
      })
    ).toBeInTheDocument();

    expect(
      screen.getByText("Confirmation pending")
    ).toBeInTheDocument();

    expect(
     screen.getAllByText("Not recorded")
    ).toHaveLength(2);

    expect(
      screen.getByText(
        /No governed delivery receipt has been persisted/i
      )
    ).toBeInTheDocument();

    expect(
      screen.getByText(
        /does not modify the governed assessment determination/i
      )
    ).toBeInTheDocument();
  });

  it("shows recorded delivery metadata when a receipt exists", () => {
    render(
      <AssessmentCloseoutPanel
        deliveryRecorded
        reportId="report-002"
        packageHash="def456"
        deliveredAt="2026-08-29T13:00:00Z"
        deliveredBy="operator@example.com"
      />
    );

    expect(
      screen.getByRole("heading", {
        name: "Client delivery recorded"
      })
    ).toBeInTheDocument();

    expect(
      screen.getByText("Delivery recorded")
    ).toBeInTheDocument();

    expect(
      screen.getByText("report-002")
    ).toBeInTheDocument();

    expect(
      screen.getByText("def456")
    ).toBeInTheDocument();

    expect(
      screen.getByText("2026-08-29T13:00:00Z")
    ).toBeInTheDocument();

    expect(
      screen.getByText("operator@example.com")
    ).toBeInTheDocument();
  });
});