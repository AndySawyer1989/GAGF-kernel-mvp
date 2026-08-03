import {
  expect
} from "vitest";

export function expectSinglePrimaryHeading(
  container: HTMLElement
): void {
  const headings =
    container.querySelectorAll("h1");

  expect(headings).toHaveLength(1);
}

export function expectNavigationLandmark(
  container: HTMLElement
): void {
  const navigation =
    container.querySelector("nav");

  expect(navigation).not.toBeNull();
}

export function expectSkipLinkTarget(
  container: HTMLElement
): void {
  const skipLink =
    container.querySelector<HTMLAnchorElement>(
      'a[href="#console-main-content"]'
    );

  const mainTarget =
    container.querySelector<HTMLElement>(
      "#console-main-content"
    );

  expect(skipLink).not.toBeNull();
  expect(mainTarget).not.toBeNull();

  expect(
    mainTarget?.getAttribute("tabindex")
  ).toBe("-1");
}

export function expectDescribedControl(
  control: HTMLElement,
  container: HTMLElement
): void {
  const descriptionId =
    control.getAttribute(
      "aria-describedby"
    );

  expect(descriptionId).toBeTruthy();

  expect(
    container.querySelector(
      `#${descriptionId}`
    )
  ).not.toBeNull();
}
