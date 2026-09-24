# Cleanup Batch 01 — duplicate and template assets

**Date:** 2026-09-24  
**Branch:** `improvement/himma-unified-v2-20260921`  
**Production impact:** none

## Scope

This batch removes only ten files proven to have no runtime references:

- Five untouched Next.js template assets: `file.svg`, `globe.svg`, `next.svg`, `vercel.svg`, and `window.svg`.
- Five flat-name boy character images. Each removed image had a byte-identical canonical copy under `apps/web/public/characters/boy/`.

The canonical files remain in place. In particular, `/characters/boy/welcome.png`, which is used by the student login page, was not removed.

## Evidence before deletion

- Exact-path search found zero references outside historical documentation, the reference prototype, and the old repository checksum baseline.
- SHA-256 proved all five flat-name images matched their canonical counterparts exactly.
- No code, API, database, content catalog, or production configuration changed.
- Removed binary payload: approximately `706 KiB`.

## Local verification after deletion

| Check | Result |
|---|---|
| Runtime reference guard for all ten removed paths | PASS |
| `git diff --cached --check` | PASS |
| TypeScript `tsc --noEmit` | PASS |
| ESLint with zero warnings | PASS |
| Jest frontend unit tests | 10 suites / 40 tests PASS |
| Next.js production build | PASS; 20 routes generated |

## Acceptance boundary

The batch is not considered fully accepted until the branch Quality Gate completes Security, Frontend, Backend, and Playwright Integration successfully at the batch commit SHA. No merge or deployment is authorized by this record.
