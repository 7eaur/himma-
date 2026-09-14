# W4 Owner/Client Approval — 2026-09-14

**Status:** ACCEPTED — canonical owner/client decision for W4 execution.

## Approved badge assets
The official Himma reward/badge package is approved as the canonical visual source for `BDG-01..BDG-06`.

Canonical runtime SVG files:
- `BDG-01` — نجمة واحدة — `/assets/rewards/svg/hem-bdg-01-star-one.svg`
- `BDG-02` — نجمتان — `/assets/rewards/svg/hem-bdg-02-stars-two.svg`
- `BDG-03` — ثلاث نجوم — `/assets/rewards/svg/hem-bdg-03-stars-three.svg`
- `BDG-04` — مستكشف الحروف — `/assets/rewards/svg/hem-bdg-04-letter-explorer.svg`
- `BDG-05` — بطل الكلمات — `/assets/rewards/svg/hem-bdg-05-word-hero.svg`
- `BDG-06` — نجم الفهم — `/assets/rewards/svg/hem-bdg-06-comprehension-star.svg`

The canonical mapping remains owned by `services/api/reward_catalog.py`; historical `recorded_label` remains immutable history.

## Approved media semantic rule
For educational media:
- `lexical_stimulus`: the image MUST directly represent the meaning of the target word, not merely an associated contextual object.
- `story_context`: contextual/supporting imagery; it MUST NOT be treated as a direct lexical stimulus.

Approved examples:
- `سَمَك` → a direct fish image.
- `نُور` → a direct representation of light/illumination. A lamp is acceptable only when the item contract explicitly makes the intended meaning direct and unambiguous; a merely associated object is not sufficient.

## Gap effects
- The external approval blocker for `AUD-BADGE-003` is removed. Its implementation is verified GREEN by exact code SHA `8736372f855e55646ce50712615b6274af94a9a8`, Quality Gate #854 / Run ID `34803602294`.
- The external academic/owner approval blocker for `AUD-MEDIA-002` is removed. The gap is NOT closed by this decision alone; implementation + tests + exact-SHA CI evidence are still required.
- `AUD-BADGE-001` and `AUD-BADGE-002` are now actionable W4 implementation work.

## Guardrails
This approval does not authorize A11, deployment, Railway, Production, final merge, Docker, fake ASR, Temporary Audio Skip, history deletion, weakened tests, or Speech/Pronunciation Lab merges.
