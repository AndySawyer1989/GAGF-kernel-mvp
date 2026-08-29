import { render, screen } from "@testing-library/react";

import {
  AssessmentDeliveryStatus
} from "./assessment-delivery-status";

describe("AssessmentDeliveryStatus", () => {
  it("shows delivery-ready state when all governed requirements are ready", () => {
    render(
      <AssessmentDeliveryStatus
        reportReady
        repositoryVerified
        findingsReady
        reportHref="/assessments/test/report"
      />
    );

    expect(
      screen.getByRole("heading", {
        name: "Ready for client delivery"
      })
    ).toBeInTheDocument();

    expect(
      screen.getByText("Delivery ready")
    ).toBeInTheDocument();

    expect(
      screen.getByText("Findings ready")
    ).toBeInTheDocument();

    expect(
      screen.getByText("Repository verified")
    ).toBeInTheDocument();

    expect(
      screen.getByText("Client report ready")
    ).toBeInTheDocument();

    expect(
      screen.getByRole("link", {
        name: "Open delivery report"
      })
    ).toHaveAttribute(
      "href",
      "/assessments/test/report"
    );
  });

  it("blocks delivery when governed requirements are incomplete", () => {
    render(
      <AssessmentDeliveryStatus
        reportReady={false}
        repositoryVerified={false}
        findingsReady={false}
        reportHref="/assessments/test/report"
      />
    );

    expect(
      screen.getByRole("heading", {
        name: "Delivery review required"
      })
    ).toBeInTheDocument();

    expect(
      screen.getByText("Review required")
    ).toBeInTheDocument();

    expect(
      screen.getByText("Findings incomplete")
    ).toBeInTheDocument();

    expect(
      screen.getByText(
        "Repository review required"
      )
    ).toBeInTheDocument();

    expect(
      screen.getByText(
        "Client report unavailable"
      )
    ).toBeInTheDocument();

    expect(
      screen.queryByRole("link", {
        name: "Open delivery report"
      })
    ).not.toBeInTheDocument();

    expect(
      screen.getByText(
        /does not create a new assessment determination/i
      )
    ).toBeInTheDocument();
  });
});