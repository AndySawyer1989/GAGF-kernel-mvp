import {
  beforeEach,
  describe,
  expect,
  it
} from "vitest";

import {
  clampPageToItems,
  readPositiveIntegerParam,
  readStringParam,
  updateUrlParams
} from "./url-table-state";

describe("URL table state", () => {
  beforeEach(() => {
    window.history.replaceState(
      {},
      "",
      "/audit-integrity"
    );
  });

  it("reads a valid positive page number", () => {
    window.history.replaceState(
      {},
      "",
      "/audit-integrity?auditPage=3"
    );

    expect(
      readPositiveIntegerParam(
        "auditPage"
      )
    ).toBe(3);
  });

  it("uses the fallback for invalid pages", () => {
    window.history.replaceState(
      {},
      "",
      "/audit-integrity?auditPage=-4"
    );

    expect(
      readPositiveIntegerParam(
        "auditPage",
        2
      )
    ).toBe(2);
  });

  it("allows only known string values", () => {
    window.history.replaceState(
      {},
      "",
      "/audit-integrity?outcome=DENIED"
    );

    expect(
      readStringParam(
        "outcome",
        [
          "ALL",
          "ALLOWED",
          "DENIED"
        ],
        "ALL"
      )
    ).toBe("DENIED");
  });

  it("rejects an unknown string value", () => {
    window.history.replaceState(
      {},
      "",
      "/audit-integrity?outcome=UNKNOWN"
    );

    expect(
      readStringParam(
        "outcome",
        [
          "ALL",
          "ALLOWED",
          "DENIED"
        ],
        "ALL"
      )
    ).toBe("ALL");
  });

  it("adds and removes URL parameters", () => {
    updateUrlParams({
      outcome: "DENIED",
      auditPage: 2,
      checkpointPage: 1
    });

    expect(
      window.location.search
    ).toBe(
      "?outcome=DENIED&auditPage=2"
    );

    updateUrlParams({
      outcome: "ALL",
      auditPage: 1
    });

    expect(
      window.location.search
    ).toBe("");
  });

  it("clamps pages to the available item range", () => {
    expect(
      clampPageToItems(
        8,
        22,
        10
      )
    ).toBe(3);

    expect(
      clampPageToItems(
        -2,
        22,
        10
      )
    ).toBe(1);

    expect(
      clampPageToItems(
        4,
        0,
        10
      )
    ).toBe(1);
  });
});
