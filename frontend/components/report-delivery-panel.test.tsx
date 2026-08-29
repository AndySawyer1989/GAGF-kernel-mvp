import { render, screen } from "@testing-library/react";

import {
  ReportDeliveryPanel
} from "./report-delivery-panel";

describe("ReportDeliveryPanel", () => {
  it("renders delivery guidance and governed verification metadata", () => {
    render(
      <ReportDeliveryPanel
        reportId="report-001"
        packageHash="abc123def456"
        schemaVersion="1.0"
      />
    );

    expect(
      screen.getByRole("heading", {
        name: "Report delivery"
      })
    ).toBeInTheDocument();

    expect(
      screen.getByText("Delivery ready")
    ).toBeInTheDocument();

    expect(
      screen.getByText("Print or save PDF")
    ).toBeInTheDocument();

    expect(
      screen.getByText("report-001")
    ).toBeInTheDocument();

    expect(
      screen.getByText("abc123def456")
    ).toBeInTheDocument();

    expect(
      screen.getByText("1.0")
    ).toBeInTheDocument();

    expect(
      screen.getByText(
        /does not create a new assessment determination/i
      )
    ).toBeInTheDocument();
  });
});