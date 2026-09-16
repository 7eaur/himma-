# Himma Browser Test Ownership — W6

This file owns the release classification for `apps/web/tests/e2e`. A test may remain useful without being a release-gate test. Loose historical flows must never be treated as proof of a current product contract.

## Release gate

These are deterministic executable acceptance tests and must be named explicitly in the final W6 Quality Gate:

- `vertical-slice.spec.ts` — real browser/MinIO/human-review vertical slice from student creation through pretest and adaptive learning.
- `w6-same-student-journey.spec.ts` — one persistent student identity through live pretest, canonical longitudinal learning evidence, supervisor posttest authorization and live posttest completion. The bounded middle-learning accelerator persists only canonical completion evidence; production learning transitions remain independently exercised by M09 and adaptation/level-completion tests.
- `reward-lifecycle.spec.ts` — canonical reward award → asset → Student/Admin → refresh/idempotency acceptance.
- `accessibility-integration.spec.ts` — keyboard, reduced motion, zoom, contrast and progress semantics.
- `w6-axe.spec.ts` — broad automated WCAG A/AA serious/critical scan on public entry routes.
- `student-detail-responsive-matrix.spec.ts` — deterministic Admin Student Detail 320/360/390/430/768/desktop matrix.
- `w6-responsive.spec.ts` — deterministic Student home/assessment 320/360/390/430/768/desktop matrix.
- `admin-dialog-keyboard.spec.ts` — modal focus/Escape/return-focus lifecycle.
- `media-fidelity.spec.ts` — approved media fidelity.
- `question-experience.spec.ts` — current question experience contract.
- `admin-responsive.spec.ts` — Admin shell critical responsive acceptance.

## Targeted regression

These remain executable for focused changes but are not individually required in every release gate because their contracts are represented by the release set above:

- `audio-review-filtered-context.spec.ts`
- `font-loading.spec.ts`
- `home-login.spec.ts`
- `responsive-smoke.spec.ts`
- `student-detail-cross-device-integrity.spec.ts`
- `student-detail-journey-states.spec.ts`
- `student-detail-partial-source-errors.spec.ts`
- `student-viewport-safety.spec.ts`

## Visual evidence / review support

- `p03-screenshots.spec.ts` — screenshot/review support; screenshots alone are not a release assertion.

## Superseded legacy flow

- `browser-flow.spec.ts` — **LEGACY / NOT RELEASE EVIDENCE**. It contains optional selectors and fallback clicks that can finish without proving the intended assessment journey. It is retained as historical debugging material and is not part of W6 release evidence. `w6-same-student-journey.spec.ts` + `vertical-slice.spec.ts` are its deterministic current-contract replacements; deletion remains optional and is not required to prove W6.

## Gate rule

The final W6 Quality Gate must run the explicit release-gate set, with Backend + Frontend + Security + Integration/Playwright all on the same exact SHA. No `skip`, `xpass`, optional success branch, screenshot-only path, or arbitrary fallback click may substitute for a required acceptance assertion.
