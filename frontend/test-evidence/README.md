# Browser Test Evidence

This directory contains generated Playwright evidence.

Generated artifacts may include:

- HTML reports
- JSON result reports
- JUnit XML reports
- Screenshots
- Traces
- Videos retained for failed tests

## Security rules

Generated evidence must not contain:

- signing secrets
- API credentials
- access tokens
- private tenant data
- production evidence payloads
- protected personal information

The E2E harness uses deterministic synthetic tenant and assessment data.

Generated report files are excluded from Git. This README remains tracked.

## Integrity manifest

The release workflow generates:

- `results/evidence-manifest.json`

The manifest records:

- normalized artifact path
- media type
- size in bytes
- SHA-256 digest
- story identifier
- release gate
- Git branch and commit

Run:

```text
npm run test:e2e:verify
```

to detect missing, modified, or unexpected evidence artifacts.

## Evidence bundles

The release workflow creates a portable ZIP bundle under:

- `playwright/bundles/`

Each bundle has a JSON digest record containing:

- SHA-256 digest
- story identifier
- release-gate result
- Git branch and commit
- artifact count
- aggregate source size
- retention period

The default bundle retention period is 30 days.

Run `npm run test:e2e:verify-bundle` to verify the newest bundle.

## Continuous integration

The GitHub Actions browser release gate runs:

- dependency installation with `npm ci`
- TypeScript validation
- production frontend build
- diagnostic-policy tests
- evidence-integrity tests
- retention-policy tests
- the full Playwright browser matrix
- release-summary generation
- evidence-manifest generation and verification
- evidence-bundle generation and verification

The workflow uploads the generated browser evidence even when a gate fails.

## Required status check

The stable branch-protection check is:

- `Browser Release Required`

This final job runs with `always()` and fails unless the governed browser-evidence job succeeds.

The workflow includes `pull_request`, `push`, `merge_group`, and manual triggers without path filters so the required check is consistently created.

CI triage produces:

- `results/ci-triage.json`
- `results/ci-triage.md`
- GitHub error, warning, or notice annotations
