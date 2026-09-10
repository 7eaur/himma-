# منصة هِمّة — Master Gap Register بعد A00–A09

**التاريخ:** 2026-09-10  
**الحالة:** `AUDIT A00–A09 COMPLETE — A10 READY — NO MERGE / NO DEPLOY`  
**المستودع:** `7eaur/himma-`  
**فرع العمل:** `audit/comprehensive-repository-review-2026-09-10`

هذا السجل هو نقطة التحويل من التدقيق إلى التنفيذ الجذري. لا يستخدم كقائمة ترقيعات؛ كل صف يحدد المالك الصحيح للحقيقة وسبب المشكلة ومخاطر التاريخ والاختبارات المطلوبة.

## قواعد التنفيذ

- P0 قبل P1 قبل P2 ما لم توجد dependency واضحة.
- لا حذف History أو تسجيلات أو Reward evidence.
- لا Repair/Overlay runtime جديد.
- Canonical Content 125 وعقود 2026-09-08 محفوظة.
- pending/uploaded audio محايد أكاديميًا ولا يمنع same-level navigation/support.
- early promotion في L1/L2 لا يُلغى لتسهيل الاختبارات أو الشارات.
- لا Production ASR قبل اعتماد provider + calibration + privacy/cost/governance.
- لا Docker.
- لا Merge/Deploy حتى Final Gates.

---

## Master Gap Register

| ID | Severity | Status | Evidence | Symptom | Root Cause / Historical Layer | Dependencies | Correct Owner of Truth | Root Fix | Migration / History Risk | Required Tests | Release Risk | Execution Wave |
|---|---:|---|---|---|---|---|---|---|---|---|---|---|
| AUD-CI-001 | P1 | VERIFIED | run `34419490966` | 823/825 backend؛ Integration skipped | two backend failures block downstream E2E | BE-003/004 | CI + test ownership | close real bug + reclassify legacy test world ثم rerun exact SHA | Low | full backend→integration | HIGH | W6/Gate |
| AUD-BE-001 | P2 | VERIFIED | import graph | runtime ownership موزع بين `activity_runtime`, `activities_v4`, `activities` | historical service generations | activity parity | Learning runtime service | extract shared primitives/owners then retire only proven dead layer | Medium | route ownership + behavior parity | MEDIUM | W5 |
| AUD-BE-002 | P2 | VERIFIED | seed/import inventory | correction/projection seeds كثيرة بعد canonical publisher | historical migration/repair layers | canonical publisher | Canonical compiler/publisher + migration archive | classify runtime/migration/test/dead; remove only dependency-free code | HIGH if careless | canonical seed twice + history migration | MEDIUM | W5 |
| AUD-BE-003 | P1 | VERIFIED | baseline failed test | `pending_audio_reviews` قد يصبح 0 مع pending audio وactionable sibling | navigation resolver يخلط next action مع review summary | audio lifecycle | shared latest-audio session summary | separate navigation target from pending-review aggregate | Low | pending + sibling actionable + promotion gate | HIGH | W1 |
| AUD-BE-004 | P2 | VERIFIED | baseline failed recovery test | PRE-Q05 legacy test sees 3 images vs canonical 4 | recovery test seeds 105-world via old seed | BE-002 | test ownership/canonical publisher | migration compatibility test منفصل عن current-runtime contract | None | legacy fixture + canonical fixture explicit | MEDIUM | W5 |
| AUD-A03-001 | **P0** | VERIFIED | `assessment.py` | rerecord overwrites same AudioSubmission | legacy reopen/replace assessment lifecycle | A03-002/003 | canonical audio-review lifecycle | append-only rerecord after explicit open؛ previous immutable | **HIGH** | invalid→task→open→new submission→old retained | **CRITICAL** | **W1** |
| AUD-A03-002 | P1 | VERIFIED | assessment/profile/completion queries | old submission can drive state after append-only | non-unified `first()/all()` historical reads | A03-001 | shared latest-submission selector/session summary | all assessment consumers use latest submission only | Medium | old rerecord + new uploaded/graded across APIs | HIGH | W1 |
| AUD-A03-003 | P1 | VERIFIED | `review.py` | invalid review reopens Attempt immediately | old review state machine | A03-001/002 | canonical rerecord lifecycle | review marks latest `rerecord_required`; explicit learner open controls actionability | Medium | invalid review does not auto-reopen | HIGH | W1 |
| AUD-A03-009 | **P0** | VERIFIED | adaptation evidence | any `rubric_score > 0` becomes boolean correct; 0.10≈1.00 | booleanized legacy evidence | scoring/adaptation | normalized evidence/mastery service | preserve numeric rubric semantics and explicit threshold/weight contract | **HIGH academic** | 0/0.1/0.7/1.0 evidence + promotion regression | **CRITICAL** | **W1** |
| AUD-A03-004 | P1 | VERIFIED | SpeechAnalysis vs AudioReview | machine evidence and human adjudication are parallel/unlinked | P07 added beside older human review | A03-008 | unified review/adjudication service | advisory immutable analysis shown/linked to human decision | Medium | no-provider human path + machine fixture + override audit | HIGH | W2 |
| AUD-A03-005 | P1 | VERIFIED | calibration env logic | arbitrary env threshold/version can label machine `auto_accepted` | config string treated as governance | A03-008 | approved ASR registry | attested provider/model/calibration registry; machine remains advisory | Medium | random env cannot grant academic acceptance | HIGH | W2 |
| AUD-A03-006 | P1 | VERIFIED | speech worker | non-atomic claim may duplicate provider calls | select-then-process queue protocol | DB/worker | speech queue owner | transactional claim/lease (`SKIP LOCKED` or equivalent) + idempotent enqueue | Medium | multi-worker concurrency/retry | HIGH if ASR enabled | W2 |
| AUD-A03-007 | P2 | VERIFIED | queue retry/dead-letter | operator recovery contract incomplete | worker built before operational runbook | A03-006 | speech ops | explicit retry/dead-letter/requeue policy and audit trail | Low | exhaustion/recovery tests | MEDIUM | W2 |
| AUD-A03-008 | P1 | BLOCKED EXTERNAL APPROVAL | provider boundary | no approved Production ASR provider | intentional safety boundary | provider/privacy/cost/calibration decision | Product + Speech governance | do not integrate experimental branches until independent approval | N/A | provider contract/calibration/privacy when approved | HIGH | DEFERRED |
| AUD-A04-001 | P1 | VERIFIED | Admin source audit | Student Details/Settings/Account use parallel presentation layers | historical page-local CSS | A04-004/007 | AdminUI + global tokens | rebuild composition on AdminUI; local CSS only for unique patterns | Low | visual parity/mobile/keyboard | HIGH UX | W3 |
| AUD-A04-002 | P1 | VERIFIED | Student Details fetch composition | failed history/rewards shown as empty/0 | client swallows partial failures | API/view-model | Student Detail data contract | explicit loaded/empty/error per source or aggregated endpoint | Low | history500/reward500/retry | HIGH trust | W3 |
| AUD-A04-003 | P1 | VERIFIED | Journey tab | `level < current_level` shown completed | UI infers history from pointer | BADGE-005 | canonical Journey/completion service | expose per-level evidence state; UI renders it directly | Medium academic | override 1→3, downgrade, early promotion | HIGH | W1/W3 |
| AUD-A04-004 | P2 | VERIFIED | `/admin/account` | legacy duplicate of Settings | pre-Settings account surface | dependency scan | Settings/account owner | prove no unique dependency then redirect/archive | Low | route/backlink/auth redirect | LOW/MEDIUM | W5 |
| AUD-A04-005 | P1 | VERIFIED | responsive E2E | Student Detail not deterministically gated on 320/360/390/430/768/Desktop | historical fragmented responsive tests | A08-005 | QA + Admin responsive contract | deterministic student fixture + full viewport matrix | None | no-overflow/touch/forms/tabs/actions | HIGH | W3/W6 |
| AUD-A04-006 | P2 | VERIFIED | mobile Admin dialog | no explicit focus trap/Escape/return focus | visual shell before keyboard lifecycle | A11Y-004 | Admin shell | shared accessible dialog lifecycle | None | keyboard-only open/tab/escape/return | MEDIUM | W3 |
| AUD-A04-007 | P2 | VERIFIED | Settings tabs/styles | no clear tab ARIA semantics + second style system | page-local implementation | A04-001 | AdminUI/accessibility patterns | shared tabs/navigation semantics + tokens | None | keyboard/SR selected state | MEDIUM | W3 |
| AUD-A04-008 | P2 | VERIFIED | Student Detail recordings | generic audio-review loses student context | no student-filtered review contract | review queue | review API/deep-link | student filter/summary without fake counters | Low | pending/graded/rerecord back-nav | MEDIUM | W3 |
| AUD-BADGE-001 | P1 | VERIFIED | Student Home | badges fetched but not rendered | reward persistence preceded visual layer | BADGE-003/008 | Reward UI + catalog | render canonical badge assets/states | Low | student reward refresh/error | HIGH product | W4 |
| AUD-BADGE-002 | P2 | VERIFIED | Admin Student Detail | badge is text chip only | visual catalog absent | BADGE-003/008 | Reward UI | shared reward presentation component | Low | admin visual/state tests | MEDIUM | W4 |
| AUD-BADGE-003 | P1 | VERIFIED | public assets vs approved kit | approved badge assets not integrated | asset kit outside runtime catalog | BADGE-004/008 | canonical Reward Catalog | import approved SVGs with stable IDs/metadata | Low | asset 200/semantic mapping | HIGH | W4 |
| AUD-BADGE-004 | P1 | VERIFIED | backend vs kit | L3 `قارئ متميز` vs approved `نجم الفهم` | duplicate reward truth | BADGE-008 | canonical Reward Catalog | one catalog controls key/label/asset/version | Medium historical labels | migration-compatible label display/history | HIGH | W4 |
| AUD-BADGE-005 | P1 | VERIFIED | adaptation + journey + rewards | L1/L2 can complete by promotion at 6–9 but badge requires 10 | two completion definitions | A04-003 | Level Completion owner | canonical completion event/state consumed by Journey+Rewards | **HIGH academic/history** | early promotion badge + 10/10 + manual cases | HIGH | W1/W4 |
| AUD-BADGE-006 | P1 | OPEN | E2E inventory | no award→asset→Student/Admin→refresh/idempotency journey | fragmented tests | W4 implementation | QA/reward acceptance | add complete reward lifecycle E2E | None | full reward E2E | HIGH | W6 |
| AUD-BADGE-007 | P2 | VERIFIED | Student Home | reward API failure shown as zero | swallowed fetch error | BADGE-001 | Student reward state | unavailable/error state distinct from 0 | None | 500/empty/success | MEDIUM | W4 |
| AUD-BADGE-008 | P1 | VERIFIED | reward API | no stable asset/catalog identity/version | persistence schema used as presentation API | BADGE-003/004 | canonical Reward Catalog/API | expose reward key + catalog version + asset identity | Medium | API contract/version tests | HIGH | W4 |
| AUD-BADGE-009 | P2 | VERIFIED RISK | RewardEvent FK | stars can cascade with Attempt deletion | history tied to mutable operational row | cleanup/reset paths | reward history model | prohibit destructive attempt cleanup or preserve reward history independently | **HIGH if cleanup** | delete/reset safety | MEDIUM | W5 |
| AUD-MEDIA-002 | P1 | ACADEMIC REVIEW REQUIRED | L2-CORE-09 | lexical stimulus `سَمَك`→سمكة image; `نُور`→lamp/light image not strictly guarded | media validator keyed mainly by `usage=choice` | academic approval | role-aware media semantic contract | introduce `lexical_stimulus/story_context/...` roles and validate accordingly; change asset only after approval | Medium content release | lexical-stimulus regression | HIGH academic | W4 |
| AUD-MEDIA-003 | P2 | VERIFIED POLICY | 23 approved unused images | risk of deleting/reusing solely because unused | unused conflated with orphan | content/media | approved asset inventory | keep reserve; use only where semantic improvement proven | Low | asset inventory | LOW | W5 |
| AUD-MEDIA-004 | P2 | VERIFIED | 5 duplicate character SHA groups | duplicate public binaries | historical path copies | dependency scan | public asset ownership | choose canonical URL only after dynamic/external ref proof | Medium URL compatibility | 404/path scan | LOW | W5 |
| AUD-MEDIA-005 | P2 | VERIFIED | 17 public files no direct refs | textual scan cannot prove dead asset | dynamic URLs/build assets possible | dependency scan | public asset ownership | runtime/network + source dependency proof before delete | Medium | 404/build/E2E | LOW | W5 |
| AUD-SEC-001 | P1 | VERIFIED | auth routes/main | no rate limit on 6-digit student code or supervisor login | auth built without abuse control | Redis/proxy IP | auth security boundary | centralized per-IP + identifier/backoff rate limiting | Low | burst→429, recovery, no enumeration | HIGH | W2 |
| AUD-SEC-002 | P1 | VERIFIED | JWT/credential rotation | access code/password change leaves old JWT valid | stateless JWT lacks auth epoch/session version | migration | auth/session owner | auth_epoch/session version checked each request; bump on rotation/revoke | Medium active sessions | revoke/rotation tests | HIGH | W2 |
| AUD-SEC-003 | P1 | VERIFIED | cookie + readiness | ready can pass with ENV not production and cookie not Secure | security mode not part of readiness contract | A11 deploy | runtime config/readiness | production startup/readiness fails unless security mode correct | Low | prod config negative/positive | HIGH | W2/A11 |
| AUD-SEC-004 | P1 | VERIFIED | legacy `/recordings/init` | presigned PUT has no max upload length | old recording path remains mounted | dependency proof | recording/storage owner | remove route if dead or enforce content-length policy + cleanup | Medium stored objects | oversized upload rejection | HIGH | W2/W5 |
| AUD-SEC-005 | P2 | VERIFIED | recordings errors | raw storage exception text may reach client | inconsistent error sanitization | OBS-001 | API error boundary | generic client errors + correlated internal logs | None | injected storage error response | MEDIUM | W2 |
| AUD-SEC-006 | P2 | OPEN DEPLOY VERIFY | Next/API config | no explicit app security headers | ownership left to platform | A11 | edge/web security owner | define CSP/frame/nosniff/referrer policy once and verify deployed headers | None | header smoke | MEDIUM | W6/A11 |
| AUD-PERF-001 | P1 | VERIFIED | BFF proxy | immutable `/api/media/*` becomes `private,no-store` | generic BFF response policy | media serving | BFF cache policy | route-aware safe cache for approved media; private JSON stays no-store | None | repeated media/network cache | HIGH low-bandwidth | W3 |
| AUD-PERF-002 | P2 | VERIFIED | `/researcher/students` | N+1 queries per student/session | payload composes many domain queries | Journey API | admin projection service | batched aggregates/query projection | Low | query budget 1/10/50 | MEDIUM | W5 |
| AUD-PERF-003 | P2 | VERIFIED | notifications GET | polling GET performs sync/upserts/commit | reconciliation embedded in read route | notification transitions | Notification domain | materialize on events/jobs; GET read-only | Low | polling/idempotency | MEDIUM | W5 |
| AUD-PERF-004 | P2 | VERIFIED | globals CSS | runtime Google Fonts dependency | historical stylesheet import | font licensing/assets | web typography | self-host/build-time optimized font strategy | None | offline/network/perf smoke | MEDIUM | W3 |
| AUD-A11Y-001 | P1 | VERIFIED PRE-RUN | CSS + E2E | reduced-motion test contract exists but no global reduce policy | animation system lacks accessibility override | W3 | global design system | disable decorative motion/smooth-scroll under preference | None | existing Playwright reduce-motion | HIGH gate | W3 |
| AUD-A11Y-002 | P1 | VERIFIED PRE-RUN | tokens + E2E | primary/green text contrast below 4.5 in tested usage | brand/display tokens reused as semantic text colors | design tokens | accessible semantic color tokens | keep brand colors, add accessible text/action variants | None | contrast gate | HIGH gate | W3 |
| AUD-A11Y-003 | P2 | VERIFIED | progress UI | div progress lacks full progressbar semantics | visual component lacks ARIA contract | shared student UI | progress component | role/min/max/now + visible label | None | SR semantics | MEDIUM | W3 |
| AUD-A11Y-004 | P2 | VERIFIED | Admin mobile dialog | keyboard lifecycle incomplete | same as A04-006 | A04-006 | Admin shell | one fix shared with A04-006 | None | keyboard E2E | MEDIUM | W3 |
| AUD-A11Y-005 | P2 | OPEN GATE | QA inventory | no broad automated axe/manual SR acceptance proven | accessibility checks fragmented | W3 fixes | QA | axe + keyboard/SR smoke on major routes | None | major-route a11y | MEDIUM | W6 |
| AUD-OBS-001 | P2 | VERIFIED | API/BFF | no request correlation/structured logging contract | AuditLog confused with ops telemetry | SEC-005 | API/BFF ops | request-id end-to-end + sanitized structured logs | Privacy sensitive | request/error trace | MEDIUM | W2 |
| AUD-OBS-002 | P1 | BLOCKED WITH ASR | speech worker | only printed cycle counts; no queue depth/age/failure metrics | experimental worker ops | A03-006/008 | Speech ops | metrics/alerts after queue/provider approval | None | worker reliability metrics | HIGH if ASR | W2/DEFERRED |
| AUD-OBS-003 | P2 | VERIFIED | auth | failed auth not counted as security signal | no abuse telemetry | SEC-001 | auth ops | failed-auth counters/events without sensitive logging | Privacy low | burst detection | MEDIUM | W2 |
| AUD-A08-001 | P1 | VERIFIED | workflow triggers/Actions | no exact-head CI for audit branch | branch filters | W6 | release CI orchestration | final exact-SHA gate after A10 | None | all gates exact SHA | HIGH | W6 |
| AUD-A08-002 | P1 | VERIFIED | vertical slice + M09 backend test | full live browser journey split across two tests | test layers evolved separately | all W1–W4 | journey acceptance | deterministic same-student live journey through posttest | Test-data only | full student journey | HIGH | W6 |
| AUD-A08-003 | P1 | VERIFIED | `m09-release-readiness.yml` | readiness workflow runs infra/backup but no pytest/Playwright | operational readiness mislabeled as full release evidence | W6 | release orchestration | compose product regression + readiness + backup gates explicitly | None | exact-SHA final suite | HIGH | W6/A11 |
| AUD-A08-004 | P2 | VERIFIED | E2E inventory | tests scattered across main CI/M04/manual/legacy | no test ownership manifest | BE-004 | QA | classify release/targeted/visual/legacy tests | None | gate membership check | MEDIUM | W5/W6 |
| AUD-A08-005 | P1 | VERIFIED | responsive tests | authenticated mobile matrix incomplete; detail conditional | historical viewport suites | A04-005 | responsive acceptance | deterministic 320/360/390/430/768/Desktop matrix | None | Admin+Student critical routes | HIGH | W3/W6 |
| AUD-A08-006 | P2 | VERIFIED | `browser-flow.spec.ts` | loose fallbacks can pass without proving flow | obsolete contract/selectors | A08-004 | QA | archive/supersede after replacement proof | None | replacement coverage | MEDIUM | W5 |
| AUD-A08-007 | P1 | VERIFIED PRE-RUN | accessibility E2E | known source mismatches never executed in baseline because integration skipped | CI dependency chain | A11Y-001/002 | QA/design | fix then run, do not waive | None | accessibility integration | HIGH | W3/W6 |
| AUD-A08-008 | P1 | OPEN | reward E2E | full badge lifecycle absent | A05 visual/catalog gap | W4 | reward acceptance | full lifecycle E2E | None | reward E2E | HIGH | W6 |
| AUD-A08-009 | P1 | VERIFIED | baseline CI | unrelated legacy/current backend failures block all browser integration | monolithic dependency gate + stale test | BE-003/004 | CI/test ownership | fix current bug, reclassify stale test, rerun | None | backend then integration | HIGH | W5/W6 |
| AUD-GIT-001 | P1 | VERIFIED | A09 branch compare | default/old branches do not represent final release truth automatically | long branch history | A09 complete | release branch governance | create/promote final branch only after A10+Green; no blind merge | Medium history | compare/ancestry/exact-SHA gates | HIGH | W6/A11 |
| AUD-GIT-002 | P1 | VERIFIED | A09 | 4 speech/pronunciation branches carry unique experimental providers/labs | unapproved parallel experiments | A03-008 | Speech governance | **exclude from merge**; research reference only | High if merged | none until independent approval | HIGH | HOLD |
| AUD-GIT-003 | P2 | VERIFIED | A09 deployment compare | sandbox branch unique but Docker/temp-audio-skip/multi-platform assumptions obsolete | old deployment experiment | A11 | deployment architecture | reference only; rebuild Railway final from current truth, no Docker/bypass | Medium | final deploy smoke/rollback | MEDIUM | A11 |

---

## Execution Waves

### W1 — Academic / History Integrity

أول موجة لأنها تحتوي P0 وتؤثر على معنى البيانات:

`AUD-A03-001/002/003/009`, `AUD-BE-003`, `AUD-A04-003`, `AUD-BADGE-005`.

الهدف: canonical audio latest/history lifecycle + numeric academic evidence + one level-completion truth. لا UI تجميلي قبل إغلاق هذه الحدود.

### W2 — Security / Speech Infrastructure Boundaries

`AUD-A03-004/005/006/007`, `AUD-SEC-001..005`, `AUD-OBS-001/003`.  
`AUD-A03-008` و`AUD-OBS-002` يبقيان HOLD حتى اعتماد ASR.

### W3 — Admin / Student UX / Accessibility / Web Reliability

`AUD-A04-001/002/005/006/007/008`, `AUD-PERF-001/004`, `AUD-A11Y-001..004`, مع توحيد AdminUI وعدم بناء Design System ثانٍ.

### W4 — Rewards / Badges / Media Semantics

`AUD-BADGE-001..008`, `AUD-MEDIA-002` بعد قرار أكاديمي. دمج الحزمة البصرية يتم عبر Reward Catalog واحد لا mapping موازي في كل صفحة.

### W5 — Historical Cleanup / Performance / Test Ownership

`AUD-BE-001/002/004`, `AUD-A04-004`, `AUD-BADGE-009`, `AUD-MEDIA-003/004/005`, `AUD-PERF-002/003`, `AUD-A08-004/006`. لا حذف قبل dependency proof.

### W6 — Final Quality Gates

`AUD-CI-001`, `AUD-A11Y-005`, `AUD-A08-001/002/003/005/007/008/009`, `AUD-SEC-006`, `AUD-GIT-001`.

يجب أن تشمل: Backend، Frontend، Security، Migrations، Drift، Seed-twice، Media، Audio، Integration، E2E، Mobile، Badges، Full Student Journey على exact SHA.

### A11 — Production / Railway

فقط بعد W6 Green: Backup/Rollback، Railway PostgreSQL/runtime/storage/worker حسب الاعتماد، migrations، canonical publication، readiness/smoke، post-deploy E2E. لا استخدام Docker أو Temporary Audio Skip من sandbox القديم.

---

## قرار بدء A10

**A00–A09 مكتملة كتدقيق، وMaster Gap Register موجود. يبدأ A10 من W1 فقط.**

لا يتم Merge لأي فرع تاريخي قبل الصيانة. فروع Speech Lab مستبعدة. أي commit في A10 يجب أن يعالج root cause ويضيف/يحدث regression tests بدل إضافة repair layer جديدة.
