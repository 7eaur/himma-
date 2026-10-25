# قالب سجل تشغيل وكيل واحد

**المسار الحصري:** `docs/v2/agent-ops/runs/YYYY-MM-DD/{A|B|C}-YYYYMMDD-HHMM.md`؛ أي تكرار في نفس الدقيقة يضيف `-02`.

| الحقل | القيمة |
|---|---|
| run_id | `YYYYMMDD-HHMM-ROLE` |
| ROLE | A / B / C |
| started_at / finished_at | ISO 8601, Asia/Aden |
| repository / branch | 7eaur/himma- / v2/01-learning-foundation-20261007 |
| base_head / final_head | Git SHAs فعليان |
| previous_handoff_read | path + SHA / missing |
| supervisor_directives_read | path + SHA |
| lease | acquired/released/blocked + النطاق |
| task_id / status | READY/IN_PROGRESS/PENDING_GATES/REWORK/BLOCKED/ACCEPTED |
| changed_paths | القائمة الكاملة أو لا يوجد |
| commits | روابط GitHub أو لا يوجد |
| targeted tests | الأمر/النتيجة/PASS أو FAIL أو NOT_RUN |
| GitHub CI/M04/M09 | run URLs + SHA + status |
| Railway | اسم الخدمة + SHA + status أو NOT_CHECKED |
| browser evidence | لقطات وأداة وتاريخ، أو NOT_AVAILABLE |
| regression/security | ما فحصته، ما لم تفحصه |
| blockers / risks | دليل محدد |
| next_action_for_successor | مهمة محددة قابلة للتنفيذ |
| supervisor_review | PENDING_GATES / ACCEPTED / REWORK ومرجع التوجيه |

## قواعد الكتابة
لا تكتب «تم» دون Commit مع شواهد؛ لا تطبع secrets أو login codes أو private audio keys أو أسماء أطفال فعليين. المشرف يرفع سجلًا مماثلًا، مع مراجعة مستقلة لتسليمَي A وB.
