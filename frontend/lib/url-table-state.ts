export function readPositiveIntegerParam(
  name: string,
  fallback = 1
): number {
  if (typeof window === "undefined") {
    return fallback;
  }

  const raw = new URL(
    window.location.href
  ).searchParams.get(name);

  if (!raw) {
    return fallback;
  }

  const parsed = Number.parseInt(
    raw,
    10
  );

  return Number.isFinite(parsed) &&
    parsed >= 1
    ? parsed
    : fallback;
}

export function readStringParam(
  name: string,
  allowedValues: readonly string[],
  fallback: string
): string {
  if (typeof window === "undefined") {
    return fallback;
  }

  const value = new URL(
    window.location.href
  ).searchParams.get(name);

  return value &&
    allowedValues.includes(value)
    ? value
    : fallback;
}

export function updateUrlParams(
  values: Record<
    string,
    string | number | null
  >
): void {
  if (typeof window === "undefined") {
    return;
  }

  const url = new URL(
    window.location.href
  );

  for (const [name, value] of Object.entries(
    values
  )) {
    if (
      value === null ||
      value === "" ||
      value === 1 ||
      value === "ALL"
    ) {
      url.searchParams.delete(name);
    } else {
      url.searchParams.set(
        name,
        String(value)
      );
    }
  }

  window.history.replaceState(
    window.history.state,
    "",
    `${url.pathname}${url.search}${url.hash}`
  );
}

export function clampPageToItems(
  page: number,
  totalItems: number,
  pageSize: number
): number {
  const totalPages = Math.max(
    Math.ceil(totalItems / pageSize),
    1
  );

  return Math.min(
    Math.max(page, 1),
    totalPages
  );
}
