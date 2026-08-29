import { render, screen } from "@testing-library/react";

import {
  GovernanceFrictionMap,
  type GovernanceFrictionMapItem
} from "./governance-friction-map";

const evidenceHref =
  "/evidence/test-tenant/test-client/test-engagement/test-assessment";

const items: GovernanceFrictionMapItem[] = [
  {
    category: "APPROVAL_DELAYED",
    eventCount: 14,
    uniqueWorkItemCount: 9,
    firstOccurredAt: "2026-08-01T10:00:00Z",
    lastOccurredAt: "2026-08-15T14:30:00Z",
    weight: 1.5,
    frictionScore: 18.4,
    eventShare: 0.7,
    band: "high",
    isDominant: true
  },
  {
    category: "DEPENDENCY_WAIT",
    eventCount: 6,
    uniqueWorkItemCount: 4,
    firstOccurredAt: "2026-08-03T09:15:00Z",
    lastOccurredAt: "2026-08-14T17:45:00Z",
    weight: 1.2,
    frictionScore: 7.2,
    eventShare: 0.3,
    band: "moderate",
    isDominant: false
  }
];

describe("GovernanceFrictionMap", () => {
  it("renders the governed friction summary", () => {
    render(
      <GovernanceFrictionMap
        items={items}
        totalFrictionScore={25.6}
        recognizedEventCount={20}
        uniqueWorkItemCount={13}
        dominantConstraint="APPROVAL_DELAYED"
        evidenceHref={evidenceHref}
      />
    );

    expect(
      screen.getByRole("heading", {
        name: "Governance friction map"
      })
    ).toBeInTheDocument();

    expect(
      screen.getByText("Dominant: Approval Delayed")
    ).toBeInTheDocument();

    expect(
      screen.getAllByText("Approval Delayed").length
    ).toBeGreaterThan(0);

    expect(
      screen.getAllByText("Dependency Wait").length
    ).toBeGreaterThan(0);
  });

  it("links each measured constraint to its supporting evidence", () => {
    render(
      <GovernanceFrictionMap
        items={items}
        totalFrictionScore={25.6}
        recognizedEventCount={20}
        uniqueWorkItemCount={13}
        dominantConstraint="APPROVAL_DELAYED"
        evidenceHref={evidenceHref}
      />
    );

    const evidenceLinks = screen.getAllByRole("link", {
      name: "View supporting evidence"
    });

    expect(evidenceLinks).toHaveLength(2);

    expect(evidenceLinks[0]).toHaveAttribute(
      "href",
      `${evidenceHref}?constraint=APPROVAL_DELAYED`
    );

    expect(evidenceLinks[1]).toHaveAttribute(
      "href",
      `${evidenceHref}?constraint=DEPENDENCY_WAIT`
    );
  });

  it("renders the interpretation boundary", () => {
    render(
      <GovernanceFrictionMap
        items={items}
        totalFrictionScore={25.6}
        recognizedEventCount={20}
        uniqueWorkItemCount={13}
        dominantConstraint="APPROVAL_DELAYED"
        evidenceHref={evidenceHref}
      />
    );

    expect(
      screen.getByText(
        /They do not assert workflow sequence, causality, or authority relationships/
      )
    ).toBeInTheDocument();
  });
});
