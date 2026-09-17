# خريطة مصدر الحقيقة — منصة هِمّة

**آخر تحديث تنفيذي:** 2026-09-17  
**المستودع:** `7eaur/himma-`  
**فرع التنفيذ:** `audit/comprehensive-repository-review-2026-09-10`  
**الحالة:** `A00–A09 CLOSED; W1–W6 GREEN; STOP`

## 1) ترتيب القوة

1. live code + PostgreSQL schema/Alembic migrations.
2. executable tests + exact-SHA GitHub Actions.
3. canonical contracts and approved decisions.
4. current `START_HERE_AR.md`, STATUS, progress, RESUME, NEXT prompt, latest continuity handoff.
5. current specs/status overlays.
6. assets/manifests.
7. historical/original/derived documentation.

الوثيقة وحدها لا تغلق Gap، وdocs-only SHA لا يحل محل tested functional SHA.

## 2) W6 exact-SHA authority

Tested functional SHA:

`c5174f33b11be80500fdd72c0456efbef062f5ad`

| Evidence | Result |
|---|---|
| Quality Gate #902 / Run `35198824643` | SUCCESS |
| Security / Frontend / Backend / Integration | all SUCCESS |
| Backend | 893 passed, 5 warnings |
| Integration Playwright | 20 passed |
| M09 #211 / Run `35198824646` / job `105128375595` | SUCCESS |
| M09 declared Playwright suite | 19 passed |
| PostgreSQL restore verification | PASS |
| Object-store restore | 43 objects verified |
| Backup artifact handling | ephemeral; no data backup uploaded |

W6 is GREEN. Historical SHA `565ba...`, `c67aaad...` and M09 #207/#210 evidence remain chronology only and are not the current authority.

## 3) Current source owners

| المجال | المصدر التنفيذي |
|---|---|
| الحالة والاستئناف | live branch + current entrypoints + latest W6 GREEN handoff |
| gap history/status | Master Gap Register for historical finding; latest status overlay for execution |
| academic behavior | current services + tests + effective ADR/decisions |
| canonical content | approval contract + compiler/release/publisher + PostgreSQL runtime |
| Placement | `services/api/placement_scoring.py` + tests |
| Adaptation | `services/api/adaptation.py`, `adaptation_runtime.py` + tests |
| Completion/Promotion | `services/api/level_completion.py` + consumers/tests |
| audio/review | current audio/review contract and code; Human Supervisor Review authority |
| Production ASR | `services/api/asr_governance.py` + `AUD-A03-008` boundary |
| rewards | `services/api/reward_catalog.py` + APIs/manifests/E2E |
| frontend | current Next.js app + shared components + E2E |
| security | current config/middleware/auth limiter + Security tests + Quality Gate |
| CI/release | `.github/workflows/ci.yml`, M09 workflow, `TEST_OWNERSHIP.md`, exact-SHA runs |

## 4) Product contracts

- Placement: `<50 → L1`, `50..<80 → L2`, `80..100 → L3`.
- Activity: `>=80` success, `70..<80` guided retry, `<70` reinforcement.
- L1/L2 early promotion after >=6 Core only with canonical mastery/critical evidence.
- L3 requires 10 Core.
- No automatic demotion.
- Manual override does not imply completion or badge.
- Latest three valid active-session Core evidences use 50/30/20 weights.

## 5) Canonical content

Approval: `HIMMA-CONTENT-APPROVAL-2026-09-08`.

Runtime: 30 Pretest + 30 Posttest + 30 Core + 35 Reinforcement = 125 items; 44 skills.

`approved/versioned contracts → canonical compile/release → deterministic publication → PostgreSQL runtime → structured APIs → deterministic UI`

Runtime patches/overlays or historical seeders are not truth owners.

## 6) Audio

- No Student Audio Skip.
- Submissions/rerecord are append-only; latest submission is active.
- Human Supervisor Review is the academic authority.
- Automated ASR is advisory.
- Production ASR `AUD-A03-008` remains blocked pending provider, calibration, privacy, cost, and governance approval.

## 7) Closed W6 root cause

Protected-runtime auth rate limiting previously incremented IP and identifier counters before credential validation. Success cleared only the identifier counter, so legitimate shared-IP logins exhausted the IP failure budget and caused deterministic `429` responses in M09 Playwright.

Current authority: pre-auth checks counters; only invalid credentials record IP/identifier failures; rotating invalid identifiers still share the IP budget; success clears identifier failures; Redis remains fail-closed. Tests and exact-SHA CI prove both availability and abuse protection.

## 8) External/later boundaries

- `AUD-A03-008`: external approval blocked.
- `AUD-SEC-006`: deployed-header verification is A11/later.
- `AUD-A11Y-005`: manual human screen-reader verification not claimed.
- `AUD-GIT-001`: final merge not executed.
- A11, Deploy, Railway, Production require explicit new authorization.

## 9) Current stop rule

W6 closure is complete. **STOP.** Do not begin any later boundary without a new explicit assignment.
