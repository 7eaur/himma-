<div align="center">

<img src="apps/web/public/brand/logo-gradient.svg" alt="Himma Logo" width="180" />

# هِمّة | Himma
### أتعلم، أتطور، أصل إلى القمة

**منصة تعليمية تفاعلية لتنمية مهارات القراءة باللغة العربية لدى طلاب الصف الثالث في سلطنة عُمان، من خلال مسارات تعلم تتكيف مع مستوى الطالب.**

[![Next.js](https://img.shields.io/badge/Next.js-000000?style=for-the-badge&logo=nextdotjs&logoColor=white)](https://nextjs.org/)
[![React](https://img.shields.io/badge/React-149ECA?style=for-the-badge&logo=react&logoColor=white)](https://react.dev/)
[![TypeScript](https://img.shields.io/badge/TypeScript-3178C6?style=for-the-badge&logo=typescript&logoColor=white)](https://www.typescriptlang.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-4169E1?style=for-the-badge&logo=postgresql&logoColor=white)](https://www.postgresql.org/)

**[🌐 زيارة المنصة](https://himma-om.com)**

</div>

---

## 📱 Screenshots | صور المنصة

ستُضاف صور واجهات الطالب ولوحة المشرف هنا.

---

## ✨ Key Features | المميزات الرئيسية

- 📚 **تعلم تكيفي:** اختبار قبلي لتحديد مستوى الطالب وتخصيص مساره التعليمي.
- 🎯 **دروس تفاعلية:** فيديو تمهيدي وتدريب موجه واختبار للتحقق من اكتساب المهارة.
- 🧩 **أنشطة متنوعة:** اختيار من متعدد، استماع، صور، ترتيب أحداث، تركيب كلمات، وقراءة صوتية.
- 🎙️ **تقييم القراءة:** تسجيل نطق الحروف والكلمات والجمل، مع تقييم مدعوم بخدمة Azure Speech.
- 💡 **دعم تعليمي مخصص:** تلميحات وأنشطة تقوية وفق الصعوبات التي يواجهها الطالب.
- 📊 **لوحة المشرف:** إدارة الطلاب والدروس والأسئلة والوسائط ومراجعة التسجيلات ومتابعة النتائج.
- 📱 **واجهة متجاوبة:** تصميم عربي يدعم اتجاه RTL ويعمل على الهاتف والحاسوب.

---

## 🛠️ Tech Stack | التقنيات

| الجانب | التقنيات |
|---|---|
| **Frontend** | Next.js, React, TypeScript |
| **Backend** | Python, FastAPI |
| **Database** | PostgreSQL |
| **Caching** | Redis |
| **Speech Assessment** | Azure Speech |
| **Deployment** | Docker, Railway |

---

## 📂 Project Structure | هيكل المشروع

```text
himma-/
├── apps/
│   └── web/              # واجهة المنصة
├── services/
│   └── api/              # الخادم ومنطق التعلم والتقييم
├── packages/
│   └── content/          # المحتوى والعقود المشتركة
├── assets/               # الصور والصوتيات وفيديوهات الدروس
├── docs/                 # بنك المحتوى
├── deploy/               # إعدادات النشر
└── scripts/              # أدوات التشغيل
```

---

## 🚀 Getting Started | التشغيل المحلي

**المتطلبات:** Node.js 22، وPython 3.12، وPostgreSQL، وRedis، وخدمة تخزين متوافقة مع S3.

1. استنساخ المستودع:

   ```bash
   git clone https://github.com/7eaur/himma-.git
   cd himma-
   ```

2. تجهيز ملف `.env` من `.env.example` وضبط إعدادات بيئة التطوير، ثم تشغيل الخدمات اللازمة:

   ```bash
   docker compose up -d
   python -m venv .venv
   python -m pip install -r requirements.txt
   ```

   فعّل البيئة الافتراضية وفق نظام التشغيل قبل تثبيت الاعتماديات.

3. تشغيل الخادم بعد تجهيز قاعدة بيانات التطوير:

   ```bash
   cd services/api
   python -m alembic upgrade head
   python seed_all.py
   python -m db.seed
   python -m uvicorn main:app --reload
   ```

4. تشغيل الواجهة في طرفية منفصلة من جذر المستودع:

   ```bash
   cd apps/web
   npm ci
   npm run dev
   ```

الواجهة: `http://localhost:3000` — الخادم: `http://localhost:8000`.

> **ملاحظة:** أوامر التهيئة مخصصة لقاعدة بيانات تطوير محلية فقط. تحتاج ميزات التقييم الصوتي إلى إعداد الخدمة والتخزين المناسبين؛ لا ترفع المفاتيح السرية إلى المستودع.

---

## 👨‍💻 Developer | المطور

**Eng. Elyas Al Shaebi — المهندس إلياس الشعيبي**

📱 **Phone / WhatsApp:** [+967 775 377 979](https://wa.me/967775377979)

[GitHub](https://github.com/7eaur)
