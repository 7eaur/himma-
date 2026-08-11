"use client";

import Link from "next/link";
import Image from "next/image";
import { useEffect, useState } from "react";

export default function LandingPage() {
  const [mounted, setMounted] = useState(false);
  useEffect(() => setMounted(true), []);

  return (
    <div className="landing-container">
      <div className="landing-content">
        {/* Logo and Tagline */}
        <div className="hero-section">
          <div className="logo-container">
            <span className="logo-text">هِمّة</span>
          </div>
          <h1 className="hero-title">أتعلم، أتطور، أصل إلى القمة</h1>
          <p className="hero-subtitle">
            رحلة ممتعة تبدأ باختبار بسيط لتحديد مستواك، ثم تنطلق في أنشطة مصممة خصيصاً لك لتعزيز مهاراتك خطوة بخطوة.
          </p>
        </div>

        {/* Level Cards */}
        <div className="levels-section">
          <div className="level-card level-1">
            <span className="level-number">1</span>
            <h3>مبتدئ</h3>
            <p>بداية الرحلة</p>
          </div>
          <div className="level-card level-2">
            <span className="level-number">2</span>
            <h3>متوسط</h3>
            <p>تطور مستمر</p>
          </div>
          <div className="level-card level-3">
            <span className="level-number">3</span>
            <h3>متقدم</h3>
            <p>وصول للقمة</p>
          </div>
        </div>

        {/* Primary Action */}
        <div className="action-section">
          <Link href="/student/login" className="btn btn-primary btn-large">
            الدخول برمز الطالب
          </Link>
        </div>

        {/* Admin Link */}
        <div className="admin-link-section">
          <Link href="/admin/login" className="link-muted">
            دخول الإدارة
          </Link>
        </div>
      </div>
    </div>
  );
}
