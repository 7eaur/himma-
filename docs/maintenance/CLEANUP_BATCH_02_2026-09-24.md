# Cleanup Batch 02 — disconnected frontend implementation

**Date:** 2026-09-24

**Branch:** `improvement/himma-unified-v2-20260921`

**Production impact:** none

## Scope

This batch removes three disconnected frontend files and their now-unused direct dependency:

- `apps/web/src/components/StudentAudioReviewOverlay.tsx`
- `apps/web/src/hooks/useAudioRecorder.ts`
- `apps/web/src/lib/idb.ts`
- npm dependency `idb`, including its lockfile entry

## Evidence before deletion

- Repository-wide source search found no import, render, or function call for the three files.
- Git history shows commit `da9f7ab` intentionally unmounted `StudentAudioReviewOverlay` to remove the pending-review navigation overlay; the component file was left behind.
- Active recording remains implemented directly in both:
  - `apps/web/src/app/student/activity/[id]/page.tsx`
  - `apps/web/src/app/student/session/[id]/page.tsx`
- The active activity hold is `StudentAdaptiveHoldOverlay`, mounted by the activity layout.
- `idb` was imported only by the removed `lib/idb.ts`; its outbox functions had no consumers.
- Removed implementation: 226 source lines plus 9 package/lockfile lines.

## Local verification after deletion

| Check | Result |
|---|---|
| Removed-symbol and dependency reference guard | PASS |
| `npm ls idb --depth=0` | empty / removed |
| TypeScript `tsc --noEmit` | PASS |
| ESLint with zero warnings | PASS |
| Jest frontend unit tests | 10 suites / 40 tests PASS |
| Next.js production build | PASS; 20 routes generated |
| Git whitespace checks | PASS |

## Acceptance boundary

The batch is not fully accepted until its commit passes the complete Quality Gate, including Backend and Playwright Integration. No production deployment or merge is part of this batch.
