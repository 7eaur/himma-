"use client";

import Image from "next/image";
import Link from "next/link";

export default function WelcomePage() {
  return (
    <div className="welcome-root" dir="rtl">

      <div className="amb-shape amb-1" />
      <div className="amb-shape amb-2" />
      <div className="amb-shape amb-3" />

      <header className="w-header">
        <div className="w-logo-wrap">
          <Image src="/brand/logo-navy.svg" alt="منصة هِمّة" width={130} height={44} priority />
        </div>
        <nav className="w-nav">
          <a href="#about" className="w-nav-link">عن المنصة</a>
          <a href="#how" className="w-nav-link">كيف تعمل</a>
          <a href="#features" className="w-nav-link">المزايا</a>
          <Link href="/student/login" className="w-nav-cta">ابدأ الآن</Link>
        </nav>
      </header>

      <section className="w-hero">
        <div className="w-hero-copy">
          <span className="w-eyebrow">
            <span className="w-eyebrow-dot" />
            منصة بحثية لتعليم القراءة — سلطنة عُمان
          </span>
          <h1 className="w-h1">
            نتعلّم بهدوء،
            <br />
            <span className="w-h1-accent">ونتقدّم بثقة.</span>
          </h1>
          <p className="w-lead">
            هِمّة منصة تعليمية تكيّفية مصممة لمساعدة طلاب الصف الثالث على تطوير مهارات القراءة
            خطوةً خطوة، من خلال أنشطة ممتعة وتقييم دقيق.
          </p>
          <div className="w-actions">
            <Link href="/student/login" className="w-btn-primary">
              <Image src="/brand/logo-white.svg" alt="" width={22} height={22} />
              دخول الطالب
              <span className="w-btn-arrow">←</span>
            </Link>
          </div>
          <div className="w-trust">
            <div className="w-trust-item">
              <span className="w-trust-icon w-trust-blue" />
              واضحة وسهلة
            </div>
            <div className="w-trust-item">
              <span className="w-trust-icon w-trust-green" />
              تتدرّج مع الطالب
            </div>
            <div className="w-trust-item">
              <span className="w-trust-icon w-trust-yellow" />
              تشجيع في كل خطوة
            </div>
          </div>
        </div>

        <div className="w-hero-visual">
          <div className="w-orbit w-orbit-1" />
          <div className="w-orbit w-orbit-2" />
          <Image
            src="/characters/boy/welcome.png"
            alt="شخصية الطالب"
            width={220} height={300}
            className="w-char w-char-boy"
            priority
          />
          <Image
            src="/characters/girl/welcome.png"
            alt="شخصية الطالبة"
            width={200} height={280}
            className="w-char w-char-girl"
            priority
          />
          <div className="w-floor" />
        </div>
      </section>

      <section id="about" className="w-section">
        <div className="w-section-inner">
          <div className="w-section-badge">من نحن</div>
          <h2 className="w-h2">منصة هِمّة التعليمية</h2>
          <p className="w-section-lead">
            هِمّة مشروع بحثي تعليمي يهدف إلى دعم طلاب الصف الثالث الذين يواجهون صعوبات في القراءة.
            تعتمد المنصة على نهج تكيّفي يُعدّل مسار التعلّم بناءً على أداء كل طالب،
            لضمان تقدّم حقيقي وقابل للقياس.
          </p>

          <div className="w-cards-grid">
            <div className="w-about-card w-card-blue animate-on-scroll animate-delay-1">
              <div className="w-about-icon">
                <Image src="/characters/boy/explain.png" alt="" width={80} height={100} />
              </div>
              <h3>للطالب</h3>
              <p>أنشطة قصيرة وممتعة تناسب مستواه، مع تشجيع مستمر وشخصيات محببة ترافقه في رحلته.</p>
            </div>
            <div className="w-about-card w-card-green animate-on-scroll animate-delay-2">
              <div className="w-about-icon">
                <Image src="/characters/girl/explain.png" alt="" width={80} height={100} />
              </div>
              <h3>للباحثة</h3>
              <p>لوحة بيانات احترافية لمتابعة تقدّم الطلاب، مراجعة التسجيلات الصوتية، وإصدار التقارير.</p>
            </div>
            <div className="w-about-card w-card-yellow animate-on-scroll animate-delay-3">
              <div className="w-about-icon" style={{ fontSize: "2.5rem", lineHeight: 1 }}>
                <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="#20364D" strokeWidth="1.5">
                  <path d="M12 2L2 7l10 5 10-5-10-5z"/><path d="M2 17l10 5 10-5"/><path d="M2 12l10 5 10-5"/>
                </svg>
              </div>
              <h3>نظام تكيّفي</h3>
              <p>تُحدّد هِمّة مستوى الطالب تلقائياً وتختار له المحتوى المناسب، فلا إفراط ولا تفريط.</p>
            </div>
          </div>
        </div>
      </section>

      <section id="how" className="w-section w-section-alt">
        <div className="w-section-inner">
          <div className="w-section-badge">كيف تعمل</div>
          <h2 className="w-h2">رحلة الطالب في هِمّة</h2>

          <div className="w-steps">
            <div className="w-step animate-on-scroll animate-delay-1">
              <div className="w-step-num">١</div>
              <div className="w-step-body">
                <h3>الاختبار القبلي</h3>
                <p>يبدأ الطالب باختبار يُحدّد مستواه الحالي في القراءة — 30 سؤالاً متدرجاً.</p>
              </div>
            </div>
            <div className="w-step-line" />
            <div className="w-step animate-on-scroll animate-delay-2">
              <div className="w-step-num">٢</div>
              <div className="w-step-body">
                <h3>الأنشطة التكيّفية</h3>
                <p>تختار هِمّة الأنشطة التي تناسب مستوى الطالب وتُعدّلها تلقائياً مع تقدّمه.</p>
              </div>
            </div>
            <div className="w-step-line" />
            <div className="w-step animate-on-scroll animate-delay-3">
              <div className="w-step-num">٣</div>
              <div className="w-step-body">
                <h3>الاختبار البعدي</h3>
                <p>بعد إتمام المسار التعليمي، يُجري الطالب اختباراً نهائياً لقياس التحسّن الفعلي.</p>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section id="features" className="w-section">
        <div className="w-section-inner">
          <div className="w-section-badge">المزايا</div>
          <h2 className="w-h2">ما يجعل هِمّة مختلفة</h2>

          <div className="w-features">
            <div className="w-feature animate-on-scroll animate-delay-1">
              <div className="w-feature-icon" style={{ background: "#EBF5FF" }}>
                <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#347FD9" strokeWidth="2">
                  <circle cx="12" cy="12" r="10"/><path d="M12 8v4l3 3"/>
                </svg>
              </div>
              <h3>تعلّم في أي وقت</h3>
              <p>المنصة متاحة على الهاتف والكمبيوتر واللوحة، وتحفظ تقدّم الطالب تلقائياً.</p>
            </div>
            <div className="w-feature animate-on-scroll animate-delay-2">
              <div className="w-feature-icon" style={{ background: "#D1FAE5" }}>
                <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#51B985" strokeWidth="2">
                  <path d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/>
                </svg>
              </div>
              <h3>تقييم حقيقي</h3>
              <p>يُسجّل الطالب قراءته ويستقبل تقييماً دقيقاً، بعيداً عن الحفظ والتخمين.</p>
            </div>
            <div className="w-feature animate-on-scroll animate-delay-1">
              <div className="w-feature-icon" style={{ background: "#FEF9C3" }}>
                <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#D97706" strokeWidth="2">
                  <path d="M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z"/>
                </svg>
              </div>
              <h3>تشجيع مستمر</h3>
              <p>شخصيات هِمّة ترافق الطالب في كل خطوة، تُشجّعه عند النجاح وتُحفّزه عند التعثّر.</p>
            </div>
            <div className="w-feature animate-on-scroll animate-delay-2">
              <div className="w-feature-icon" style={{ background: "#F3E8FF" }}>
                <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#7C3AED" strokeWidth="2">
                  <path d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"/>
                </svg>
              </div>
              <h3>تقارير للباحثة</h3>
              <p>بيانات تفصيلية عن أداء كل طالب، مع إمكانية تصدير التقارير لدعم البحث العلمي.</p>
            </div>
          </div>
        </div>
      </section>

      <section className="w-cta">
        <div className="w-cta-inner">
          <Image
            src="/characters/boy/encourage.png"
            alt=""
            width={120} height={160}
            className="w-cta-char"
          />
          <div>
            <h2 className="w-cta-h2">هل أنت مستعد لبدء رحلتك؟</h2>
            <p className="w-cta-p">أدخل رمز الدخول الخاص بك وابدأ التعلّم الآن.</p>
            <Link href="/student/login" className="w-btn-primary w-btn-lg">
              ابدأ الآن
              <span className="w-btn-arrow">←</span>
            </Link>
          </div>
        </div>
      </section>

      <footer className="w-footer">
        <div className="w-footer-inner">
          <Image src="/brand/logo-navy.svg" alt="هِمّة" width={100} height={34} />
          <p className="w-footer-copy">
            منصة هِمّة التعليمية — مشروع بحثي لدعم تعليم القراءة في سلطنة عُمان
          </p>
          <p className="w-footer-tagline">أتعلم، أتطور، أصل إلى القمة</p>
        </div>
      </footer>
    </div>
  );
}
