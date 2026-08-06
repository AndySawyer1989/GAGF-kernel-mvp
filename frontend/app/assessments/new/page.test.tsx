import {
  render,
  screen,
  waitFor
} from "@testing-library/react";

import userEvent from "@testing-library/user-event";

import {
  beforeEach,
  describe,
  expect,
  it,
  vi
} from "vitest";

import NewAssessmentPage from "./page";

import {
  executeAssessment
} from "@/lib/governance-assessment-api";

import {
  createTestApiConfig
} from "@/test/governance-assessment-fixtures";

vi.mock(
  "@/lib/governance-assessment-api",
  async (importOriginal) => {
    const actual =
      await importOriginal<
        typeof import(
          "@/lib/governance-assessment-api"
        )
      >();

    return {
      ...actual,
      getGovernanceAssessmentApiConfig:
        vi.fn(() => createTestApiConfig()),
      executeAssessment: vi.fn()
    };
  }
);

const mockedExecuteAssessment =
  vi.mocked(executeAssessment);

describe(
  "NewAssessmentPage delivery actions",
  () => {
    beforeEach(() => {
      vi.clearAllMocks();

      window.history.replaceState(
        {},
        "",
        "/assessments/new"
      );

      mockedExecuteAssessment.mockResolvedValue({
        hierarchy_key:
          "tenant-alpha/client-acme/engagement-001/assessment-001",
        artifact_count: 6
      } as Awaited<
        ReturnType<typeof executeAssessment>
      >);
    });

    it(
      "opens the completed assessment and client report from the submitted hierarchy",
      async () => {
        const user = userEvent.setup();

        render(<NewAssessmentPage />);

        await user.click(
          screen.getByRole(
            "button",
            {
              name: "Execute assessment"
            }
          )
        );

        await waitFor(() => {
          expect(
            mockedExecuteAssessment
          ).toHaveBeenCalledTimes(1);
        });

        expect(
          await screen.findByText(
            "Assessment complete"
          )
        ).toBeInTheDocument();

        expect(
          screen.getByText(
            "6 governed artifacts were persisted."
          )
        ).toBeInTheDocument();

        const assessmentLink =
          screen.getByRole(
            "link",
            {
              name: "Open assessment"
            }
          );

        const reportLink =
          screen.getByRole(
            "link",
            {
              name: "View client report"
            }
          );

        expect(assessmentLink).toHaveAttribute(
          "href",
          "/assessments/tenant-alpha/client-acme/engagement-001/assessment-001"
        );

        expect(reportLink).toHaveAttribute(
          "href",
          "/assessments/tenant-alpha/client-acme/engagement-001/assessment-001/report"
        );

        expect(
          screen.getByRole(
            "link",
            {
              name: "View all assessments"
            }
          )
        ).toHaveAttribute(
          "href",
          "/assessments"
        );
      }
    );

    it(
      "binds delivery links to the submitted identity rather than later form edits",
      async () => {
        const user = userEvent.setup();

        render(<NewAssessmentPage />);

        await user.click(
          screen.getByRole(
            "button",
            {
              name: "Execute assessment"
            }
          )
        );

        await screen.findByText(
          "Assessment complete"
        );

        const clientInput =
          screen.getByRole(
            "textbox",
            {
              name: "Client ID"
            }
          );

        await user.clear(clientInput);
        await user.type(
          clientInput,
          "client-changed"
        );

        expect(
          screen.getByRole(
            "link",
            {
              name: "Open assessment"
            }
          )
        ).toHaveAttribute(
          "href",
          "/assessments/tenant-alpha/client-acme/engagement-001/assessment-001"
        );

        expect(
          screen.getByRole(
            "link",
            {
              name: "View client report"
            }
          )
        ).toHaveAttribute(
          "href",
          "/assessments/tenant-alpha/client-acme/engagement-001/assessment-001/report"
        );
      }
    );
  }
);
