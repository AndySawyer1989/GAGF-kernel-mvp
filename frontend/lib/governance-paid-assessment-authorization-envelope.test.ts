import {
  describe,
  expect,
  it
} from "vitest";

import {
  buildPaidAssessmentAuthorizationEnvelope
} from "./governance-paid-assessment-authorization-envelope";


describe(
  "paid assessment authorization envelope",
  () => {
    it(
      "builds one shared authorization lineage",
      () => {
        const envelope =
          buildPaidAssessmentAuthorizationEnvelope({
            assessmentId:
              "assessment-001",

            now:
              () =>
                new Date(
                  "2026-09-11T22:15:00.000Z"
                ),

            nonce:
              () =>
                "123456789"
          });

        expect(
          envelope
        ).toEqual({
          authorizedAt:
            "2026-09-11T22:15:00.000Z",

          eventNonce:
            "123456789",

          contractExecutionEventId:
            (
              "contract-assessment-001-"
              + "123456789"
            ),

          authorizationId:
            (
              "paid-work-assessment-001-"
              + "123456789"
            )
        });
      }
    );


    it(
      "binds contract and paid authorization to the same nonce",
      () => {
        const envelope =
          buildPaidAssessmentAuthorizationEnvelope({
            assessmentId:
              "assessment-alpha",

            now:
              () =>
                new Date(
                  "2026-09-11T22:30:00.000Z"
                ),

            nonce:
              () =>
                "nonce-001"
          });

        expect(
          envelope
            .contractExecutionEventId
        ).toBe(
          (
            "contract-assessment-alpha-"
            + "nonce-001"
          )
        );

        expect(
          envelope
            .authorizationId
        ).toBe(
          (
            "paid-work-assessment-alpha-"
            + "nonce-001"
          )
        );
      }
    );


    it(
      "preserves one authorization timestamp",
      () => {
        const envelope =
          buildPaidAssessmentAuthorizationEnvelope({
            assessmentId:
              "assessment-001",

            now:
              () =>
                new Date(
                  "2026-09-11T23:00:00.000Z"
                ),

            nonce:
              () =>
                "nonce-002"
          });

        expect(
          envelope.authorizedAt
        ).toBe(
          "2026-09-11T23:00:00.000Z"
        );
      }
    );


    it(
      "rejects an empty assessment identifier",
      () => {
        expect(
          () =>
            buildPaidAssessmentAuthorizationEnvelope({
              assessmentId:
                "   ",

              nonce:
                () =>
                  "nonce-001"
            })
        ).toThrow(
          "assessmentId is required"
        );
      }
    );


    it(
      "rejects an empty nonce",
      () => {
        expect(
          () =>
            buildPaidAssessmentAuthorizationEnvelope({
              assessmentId:
                "assessment-001",

              nonce:
                () =>
                  "   "
            })
        ).toThrow(
          "eventNonce is required"
        );
      }
    );


    it(
      "rejects an invalid authorization timestamp",
      () => {
        expect(
          () =>
            buildPaidAssessmentAuthorizationEnvelope({
              assessmentId:
                "assessment-001",

              now:
                () =>
                  new Date(
                    "not-a-date"
                  ),

              nonce:
                () =>
                  "nonce-001"
            })
        ).toThrow(
          "Authorization timestamp is invalid"
        );
      }
    );


    it(
      "creates a fresh envelope on each invocation",
      () => {
        let nonce =
          100;

        const nonceFactory =
          () => {
            nonce += 1;

            return `${nonce}`;
          };

        const first =
          buildPaidAssessmentAuthorizationEnvelope({
            assessmentId:
              "assessment-001",

            now:
              () =>
                new Date(
                  "2026-09-11T23:15:00.000Z"
                ),

            nonce:
              nonceFactory
          });

        const second =
          buildPaidAssessmentAuthorizationEnvelope({
            assessmentId:
              "assessment-001",

            now:
              () =>
                new Date(
                  "2026-09-11T23:16:00.000Z"
                ),

            nonce:
              nonceFactory
          });

        expect(
          first.eventNonce
        ).not.toBe(
          second.eventNonce
        );

        expect(
          first.authorizationId
        ).not.toBe(
          second.authorizationId
        );

        expect(
          first.contractExecutionEventId
        ).not.toBe(
          second.contractExecutionEventId
        );
      }
    );
  }
);