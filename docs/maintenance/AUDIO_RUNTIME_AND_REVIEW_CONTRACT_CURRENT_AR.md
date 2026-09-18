# عقد الصوت الحالي ومراجعة المشرف — هِمّة

**Authority updated:** 2026-09-18  
**Status:** CURRENT / AUTHORITATIVE

## 1. الأصول الثابتة

Source:
assets/audio/HIMMA_AUDIO_V1/manifest.csv

Current inventory:
- 54 IDs.
- 54 WAV.
- 54 MP3.
- 108 binaries total.
- 4 feedback.
- 6 letter sounds.
- 13 syllables.
- 29 words.
- 2 auditory stories.

INS-01 وINS-02 هما القصتان المعتمدتان.  
المصدر SYL-15 منشور تحت runtime ID المستقر LET-01 بصوت مَ.

## 2. سلطة القرار

Human Supervisor Review هي السلطة الأكاديمية الحالية لأي تسجيل طالب يحتاج مراجعة.

لا ASR آلي يملك سلطة score/mastery/promotion في الإصدار الحالي.

## 3. دورة التسجيل

capture → persist/upload → pending supervisor review → supervisor decision

قرار المشرف:
- approve/grade
أو
- request rerecord

## 4. السلوك الأكاديمي الدقيق

- pending/uploaded/rerecord_required محايد أكاديميًا حتى القرار الصحيح.
- رفع تسجيل داخل قبلي/بعدي لا يمنع الطالب من إكمال الأسئلة غير المجابة التالية.
- بعد انتهاء الأسئلة، final academic completion لا يتم حتى تُحسم المراجعات المطلوبة.
- Request Rerecord مهمة مستقلة وصريحة.
- لا hijack تلقائي للسؤال أو النشاط الحالي.
- الطالب يفتح مهمة إعادة التسجيل صراحة.
- التسجيل السابق يبقى history/evidence؛ لا حذف ولا استبدال صامت.
- لا duplicate academic answer بسبب rerecord.

## 5. ممنوع

- Student Audio Skip.
- Temporary Audio Skip.
- Fake ASR.
- bypass.
- حذف التسجيل السابق لإخفاء التاريخ.
- تحويل low confidence إلى خطأ أكاديمي تلقائي.

## 6. المزود الصوتي الآلي

Production ASR/provider خارج هذا التسليم ومؤجل لاعتماد مستقل يشمل:
- provider contract.
- representative calibration.
- confidence rules.
- privacy/retention.
- human override/audit.
- cost/governance.

حتى ذلك الوقت لا يغير وجود أي branch تجريبي سلطة المراجعة البشرية.

## 7. التحقق

M09 #224 أثبت:
- deleted student audio bypass route is absent.
- ready checks approved_audio/storage = ok.
- object-store backup/restore = 35 objects verified.

QG/Playwright الحالي يثبت رحلة الطالب والمشرف على Functional SHA الحالي.
