# مصدر الحقيقة — منصة هِمّة

**Current authority updated:** 2026-09-18

## 1. ترتيب القوة

1. live code على stage/02-content.
2. PostgreSQL schema + Alembic migrations.
3. executable tests + exact-SHA CI.
4. verified Railway runtime.
5. canonical product/content/audio contracts.
6. current documentation set المدرج في docs/ops/DOCUMENTATION_INDEX.md.
7. historical handoffs/checkpoints/audits.

START_HERE_AR.md هو نقطة دخول القراءة وليس بديلًا عن الكود الحي.

## 2. الفرع والإصدار

Official branch: stage/02-content.

Current functional evidence SHA:
512f0a550eb098f0ce904ec4ed526d9e28098a6a

أي docs-only descendant لاحق لا يصبح functional authority تلقائيًا.

## 3. المالك التنفيذي لكل مجال

| المجال | المصدر |
|---|---|
| حالة المشروع | START_HERE_AR.md + docs/ops/STATUS.md + live branch |
| schema | services/api/alembic/versions + models |
| authentication/authorization | current FastAPI auth/security code + tests |
| placement | services/api/placement_scoring.py + tests |
| adaptation | services/api/adaptation.py + adaptation_runtime.py + tests |
| completion/promotion | services/api/level_completion.py + current consumers/tests |
| canonical content | approved/versioned content + canonical_release.py + publisher + PostgreSQL runtime |
| student UX | apps/web/src/app/student + shared student systems + Playwright |
| admin UX | apps/web/src/app/admin + AdminUI/admin-workflow + Playwright |
| audio review | current code + docs/maintenance/AUDIO_RUNTIME_AND_REVIEW_CONTRACT_CURRENT_AR.md |
| rewards | current reward catalog/APIs/tests |
| CI/release | .github/workflows/ci.yml + m04-responsive.yml + m09-release-readiness.yml |
| production | Railway project friendly-dream / production |
| branch state | docs/maintenance/HIMMA_BRANCH_INVENTORY_2026-09-18_AR.md |

## 4. Product contracts

- Placement: <50 L1, 50..<80 L2, >=80 L3.
- Activity: >=80 success; 70..<80 guided retry; <70 reinforcement.
- L1/L2 promotion: >=6 Core + mastery >=85 + critical coverage + critical floor >=70 + no unresolved reinforcement/review.
- L3: 10 Core; no L4.
- Automatic demotion: forbidden.
- Manual override: reason + audit + history preservation.
- Latest 3 valid active-session Core evidences: 50/30/20.

## 5. Content

Approval: HIMMA-CONTENT-APPROVAL-2026-09-08.

Baseline catalog: 105 source items.  
Approved runtime: 125 items:
- 30 pretest
- 30 posttest
- 30 core
- 35 reinforcement
- 44 skills

The 20-item difference is approved versioned reinforcement expansion, not duplicate canonical content.

## 6. Audio

Current academic authority: Human Supervisor Review.

- Pending/uploaded audio is neutral academically.
- Student may continue remaining unanswered assessment questions.
- Finalization waits for required reviews.
- Rerecord is explicit, separate, and history-preserving.
- No audio bypass.
- Production ASR is excluded/deferred and must not silently become academic authority.

## 7. Exact evidence

Functional SHA 512f0a550eb098f0ce904ec4ed526d9e28098a6a:
- QG #933 / 35301572062: SUCCESS.
- M04 #359 / 35299593387: SUCCESS.
- M09 #224 / 35299593312: SUCCESS.
- Railway API/Web deploy: SUCCESS.

Full identifiers are in docs/ops/EVIDENCE_INDEX.md.

## 8. Historical documentation rule

Any dated handoff/checkpoint describing an earlier branch, unfinished merge, old production baseline, Temporary Audio Skip, obsolete deployment topology, or old W/A stage status is chronology only.

When history conflicts with current truth, do not edit product behavior to match history. Follow this file and live evidence.
