import axe, {
  type AxeResults,
  type RunOptions
} from "axe-core";

const DEFAULT_OPTIONS: RunOptions = {
  resultTypes: [
    "violations",
    "incomplete"
  ],
  rules: {
    region: {
      enabled: false
    },
    "color-contrast": {
      enabled: false
    }
  }
};

export async function runAccessibilityAudit(
  container: HTMLElement,
  options: RunOptions = {}
): Promise<AxeResults> {
  return axe.run(
    container,
    {
      ...DEFAULT_OPTIONS,
      ...options,
      rules: {
        ...DEFAULT_OPTIONS.rules,
        ...options.rules
      }
    }
  );
}

export function formatAccessibilityViolations(
  results: AxeResults
): string {
  if (results.violations.length === 0) {
    return "";
  }

  return results.violations
    .map((violation) => {
      const nodes = violation.nodes
        .map((node) => {
          const target =
            node.target.join(", ");

          const failure =
            node.failureSummary ??
            "No failure summary provided.";

          return (
            `  Target: ${target}\n`
            + `  ${failure}`
          );
        })
        .join("\n");

      return (
        `${violation.id}: `
        + `${violation.help}\n`
        + `${nodes}`
      );
    })
    .join("\n\n");
}

export async function expectNoAccessibilityViolations(
  container: HTMLElement,
  options: RunOptions = {}
): Promise<void> {
  const results =
    await runAccessibilityAudit(
      container,
      options
    );

  if (results.violations.length > 0) {
    throw new Error(
      "Accessibility violations detected:\n\n"
      + formatAccessibilityViolations(
        results
      )
    );
  }
}
