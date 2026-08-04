export type DiagnosticLocation = {
  url?: string;
  lineNumber?: number;
  columnNumber?: number;
};

export type PolicyDiagnostic = {
  event_index?: number;
  source:
    | "console"
    | "pageerror";
  level:
    | "warning"
    | "error";
  message: string;
  location?: DiagnosticLocation;
  stack?: string;
};

export type DiagnosticPolicyResult = {
  expected_warnings: number;
  unexpected_warnings: number;
  unexpected_errors: number;
  page_errors: number;
  release_blocking: boolean;
  expected_warning_events:
    PolicyDiagnostic[];
  unexpected_warning_events:
    PolicyDiagnostic[];
  unexpected_error_events:
    PolicyDiagnostic[];
  page_error_events:
    PolicyDiagnostic[];
};

export function redactSensitiveText(
  input: unknown
): string;

export function sanitizeDiagnostic(
  diagnostic: PolicyDiagnostic,
  eventIndex: number
): PolicyDiagnostic;

export function isExpectedWarning(
  message: string
): boolean;

export function evaluateDiagnosticPolicy(
  diagnostics:
    PolicyDiagnostic[]
): DiagnosticPolicyResult;
