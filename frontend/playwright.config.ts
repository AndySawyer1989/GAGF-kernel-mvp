import {
  defineConfig,
  devices
} from "@playwright/test";

const evidenceRoot =
  "test-evidence/playwright";

export default defineConfig({
  testDir: "./e2e",

  fullyParallel: true,

  /*
   * Two workers is the validated stable concurrency
   * for the local Next.js test server.
   */
  workers: 2,

  forbidOnly:
    Boolean(process.env.CI),

  retries:
    process.env.CI
      ? 1
      : 0,

  /*
   * Reporter outputs provide human-readable,
   * machine-readable, and CI-compatible evidence.
   */
  reporter: [
    [
      "list"
    ],
    [
      "html",
      {
        outputFolder:
          `${evidenceRoot}/html`,
        open: "never"
      }
    ],
    [
      "json",
      {
        outputFile:
          `${evidenceRoot}/results/results.json`
      }
    ],
    [
      "junit",
      {
        outputFile:
          `${evidenceRoot}/results/junit.xml`
      }
    ]
  ],

  outputDir:
    `${evidenceRoot}/traces`,

  use: {
    baseURL:
      "http://127.0.0.1:3000",

    /*
     * Capture enough evidence to diagnose failures
     * without recording every successful browser run.
     */
    trace:
      "retain-on-failure",

    screenshot:
      "only-on-failure",

    video:
      "retain-on-failure"
  },

  projects: [
    {
      name:
        "desktop-chromium",

      use: {
        ...devices[
          "Desktop Chrome"
        ]
      }
    },
    {
      name:
        "mobile-chromium",

      use: {
        ...devices[
          "Pixel 5"
        ]
      }
    }
  ],

  webServer: {
    command:
      "npm run dev",

    url:
      "http://127.0.0.1:3000",

    reuseExistingServer:
      !process.env.CI,

    timeout:
      120_000
  }
});
