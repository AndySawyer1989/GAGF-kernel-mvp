export type PaidAssessmentAuthorizationEnvelope = {
  authorizedAt: string;
  eventNonce: string;
  contractExecutionEventId: string;
  authorizationId: string;
};


export type BuildPaidAssessmentAuthorizationEnvelopeInput = {
  assessmentId: string;

  now?: () => Date;

  nonce?: () => string;
};


function requiredText(
  value: string,
  name: string
): string {
  const normalized =
    value.trim();

  if (
    normalized.length === 0
  ) {
    throw new Error(
      `${name} is required.`
    );
  }

  return normalized;
}


function defaultNow(): Date {
  return new Date();
}


function defaultNonce(): string {
  return `${Date.now()}`;
}


export function
buildPaidAssessmentAuthorizationEnvelope(
  input:
    BuildPaidAssessmentAuthorizationEnvelopeInput
): PaidAssessmentAuthorizationEnvelope {
  const assessmentId =
    requiredText(
      input.assessmentId,
      "assessmentId"
    );

  const now =
    input.now ??
    defaultNow;

  const nonceFactory =
    input.nonce ??
    defaultNonce;

  const authorizedAtDate =
    now();

  if (
    Number.isNaN(
      authorizedAtDate.getTime()
    )
  ) {
    throw new Error(
      "Authorization timestamp is invalid."
    );
  }

  const eventNonce =
    requiredText(
      nonceFactory(),
      "eventNonce"
    );

  const authorizedAt =
    authorizedAtDate.toISOString();

  return {
    authorizedAt,

    eventNonce,

    contractExecutionEventId:
      (
        `contract-${assessmentId}-`
        + eventNonce
      ),

    authorizationId:
      (
        `paid-work-${assessmentId}-`
        + eventNonce
      )
  };
}