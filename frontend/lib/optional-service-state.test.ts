import {
  describe,
  expect,
  it
} from "vitest";

import {
  buildOptionalServiceWarning
} from "./optional-service-state";

describe("optional service state", () => {
  it("returns no warning when all optional services load", () => {
    expect(
      buildOptionalServiceWarning([])
    ).toBeNull();
  });

  it("describes one degraded optional service", () => {
    expect(
      buildOptionalServiceWarning([
        "durable signing"
      ])
    ).toBe(
      "Core audit evidence loaded successfully, but durable signing is currently degraded."
    );
  });

  it("describes multiple degraded services", () => {
    expect(
      buildOptionalServiceWarning([
        "signed checkpoint inventory",
        "signed checkpoint verification"
      ])
    ).toBe(
      "Core audit evidence loaded successfully, but signed checkpoint inventory, signed checkpoint verification are currently degraded."
    );
  });

  it("removes duplicate failures", () => {
    expect(
      buildOptionalServiceWarning([
        "durable signing",
        "durable signing"
      ])
    ).toBe(
      "Core audit evidence loaded successfully, but durable signing is currently degraded."
    );
  });

  it("ignores empty failure names", () => {
    expect(
      buildOptionalServiceWarning([
        "",
        " ",
        "signed checkpoint verification"
      ])
    ).toBe(
      "Core audit evidence loaded successfully, but signed checkpoint verification is currently degraded."
    );
  });
});
