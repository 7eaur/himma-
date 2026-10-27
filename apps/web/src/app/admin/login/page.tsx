"use client";

import { useEffect, useState } from "react";
import Image from "next/image";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { ArrowRight, LockKeyhole, ShieldCheck, UserRound } from "lucide-react";

export default function AdminLogin() {
  const router = useRouter();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    const checkSession = async () => {
      try {
        const response = await fetch("/api/auth/me", { cache: "no-store" });
        const data = await response.json().catch(() => null);
        if (response.ok && data?.role === "researcher") {
          router.replace("/admin");
        }
      } catch {
        // Login remains available when there is no valid session.
      }
    };
    void checkSession();
  }, [router]);

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    setIsLoading(true);
    setError("");

    try {
      const response = await fetch("/api/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username: username.trim(), password }),
      });
      const data = await response.json().catch(() => null);

      if (!response.ok) {
        setError(data?.detail || "تعذر تسجيل الدخول. تحقق من البيانات وحاول مرة أخرى.");
        return;
      }

      router.replace("/admin");
      router.refresh();
    } catch {
      setError("تعذر الاتصال بالخادم الآن. حاول مرة أخرى بعد قليل.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="admin-login-root" dir="rtl">
      <div className="admin-login-brand" aria-hidden="true">
        <Image src="/brand/logo-white.svg" alt="" width={140} height={48} priority />
        <div className="admin-login-kicker"><ShieldCheck size={17} /> مساحة المشرف الآمنة</div>
        <h2 className="admin-brand-title">متابعة أوضح، وقرارات أسرع</h2>
        <p className="admin-brand-sub">أدر الطلاب، راجع التسجيلات، وتابع التقدم من مساحة واحدة مرتبة.</p>
        <Image src="/characters/girl/welcome.png" alt="" width={176} height={218} className="admin-brand-char" priority />
        <p className="admin-brand-tagline">منصة هِمّة التعليمية</p>
      </div>

      <div className="admin-login-form-wrap">
        <Link href="/" className="login-back-home" aria-label="العودة إلى الصفحة الرئيسية">
          <ArrowRight size={18} aria-hidden="true" />
          <span>الصفحة الرئيسية</span>
        </Link>

        <div className="admin-login-form-box">
          <div className="admin-login-mobile-logo">
            <Image src="/brand/logo-navy.svg" alt="هِمّة" width={136} height={46} priority />
          </div>
          <span className="admin-login-eyebrow">دخول المشرف</span>
          <h1>مرحبًا بعودتك</h1>
          <p>أدخل بيانات حسابك للوصول إلى مركز المتابعة والإدارة.</p>

          {error && (
            <div data-testid="error-message" className="alert-error text-center mb-4" role="alert">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="admin-login-form">
            <div className="admin-login-field">
              <label htmlFor="supervisor-username">اسم المستخدم</label>
              <div className="relative">
                <input
                  id="supervisor-username"
                  type="text"
                  className="input-field"
                  data-testid="input-username"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  required
                  autoComplete="username"
                  dir="rtl"
                  placeholder="اكتب اسم المستخدم"
                />
                <UserRound size={18} className="admin-login-field-icon" aria-hidden="true" />
              </div>
            </div>

            <div className="admin-login-field">
              <label htmlFor="supervisor-password">كلمة المرور</label>
              <div className="relative">
                <input
                  id="supervisor-password"
                  type="password"
                  className="input-field"
                  data-testid="input-password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  autoComplete="current-password"
                  dir="ltr"
                  placeholder="••••••••"
                />
                <LockKeyhole size={18} className="admin-login-field-icon" aria-hidden="true" />
              </div>
            </div>

            <button
              type="submit"
              className="btn-primary admin-login-submit"
              data-testid="login-submit"
              disabled={isLoading}
            >
              {isLoading ? <><span className="spinner" /> جاري التحقق...</> : "دخول لوحة المشرف"}
            </button>
          </form>
          <p className="admin-login-hint"><ShieldCheck size={15} aria-hidden="true" /> الدخول مخصص للمشرفين المخولين بإدارة المنصة.</p>
        </div>
      </div>
    </div>
  );
}
