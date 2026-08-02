import "@testing-library/jest-dom/vitest";

import {
  cleanup
} from "@testing-library/react";

import {
  afterEach,
  vi
} from "vitest";

afterEach(() => {
  cleanup();

  document.body.style.overflow = "";

  window.history.replaceState(
    {},
    "",
    "/"
  );
});

Object.defineProperty(
  window,
  "requestAnimationFrame",
  {
    configurable: true,
    writable: true,
    value: (
      callback: FrameRequestCallback
    ) => {
      callback(0);
      return 1;
    }
  }
);

Object.defineProperty(
  window,
  "cancelAnimationFrame",
  {
    configurable: true,
    writable: true,
    value: vi.fn()
  }
);
