export function buildOptionalServiceWarning(
  failures: string[]
): string | null {
  const uniqueFailures = Array.from(
    new Set(
      failures
        .map((item) => item.trim())
        .filter(Boolean)
    )
  );

  if (uniqueFailures.length === 0) {
    return null;
  }

  return (
    `Core audit evidence loaded successfully, but ${uniqueFailures.join(
      ", "
    )} ${
      uniqueFailures.length === 1
        ? "is"
        : "are"
    } currently degraded.`
  );
}
