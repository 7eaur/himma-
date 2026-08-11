"use client";

import { useState, FormEvent, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Image from "next/image";
import styles from "./login.module.css";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

function LoginForm() {
  const router = useRouter();
  const params = useSearchParams();
  const initialRole = params.get("role") === "student" ? "student" : "researcher";

  const [mode, setMode] = useState<"researcher" | "student">(initialRole);
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [accessCode, setAccessCode] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      if (mode === "researcher") {
        const res = await fetch(`${API_URL}/auth/login`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          credentials: "include",
          body: JSON.stringify({ username, password }),
        });
        if (!res.ok) { setError("بيانات الدخول غير صحيحة"); return; }
        router.push("/researcher");
      } else {
        const res = await fetch(`${API_URL}/auth/student-login`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          credentials: "include",
          body: JSON.stringify({ access_code: accessCode }),
        });
        if (!res.ok) { setError("رمز الدخول غير صحيح"); return; }
        router.push("/student");
      }
    } catch {
      setError("حدث خطأ في الاتصال بالخادم");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className={styles.page}>
      <div className={styles.card}>
        {/* Logo */}
        <div className={styles.logoWrap}>
          <Image
            src="/brand/logo-gradient.svg"
            alt="منصة هِمّة"
            width={120}
            height={60}
            priority
          />
        </div>

        <h1 className={styles.title}>تسجيل الدخول</h1>

        {/* Role Tabs */}
        <div className={styles.tabs} role="tablist">
          <button
            type="button"
            role="tab"
            aria-selected={mode === "researcher"}
            className={`${styles.tab} ${mode === "researcher" ? styles.tabActive : ""}`}
            onClick={() => { setMode("researcher"); setError(""); }}
            data-testid="tab-researcher"
          >
            👩‍🔬 الباحثة
          </button>
          <button
            type="button"
            role="tab"
            aria-selected={mode === "student"}
            className={`${styles.tab} ${mode === "student" ? styles.tabActive : ""}`}
            onClick={() => { setMode("student"); setError(""); }}
            data-testid="tab-student"
          >
            🎒 الطالب
          </button>
        </div>

        <form onSubmit={handleSubmit} className={styles.form}>
          {mode === "researcher" ? (
            <>
              <div className="form-group">
                <label htmlFor="username" className="form-label">اسم المستخدم</label>
                <input
                  id="username"
                  type="text"
                  autoComplete="username"
                  className="form-input"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  required
                  placeholder="أدخل اسم المستخدم"
                  data-testid="input-username"
                />
              </div>
              <div className="form-group">
                <label htmlFor="password" className="form-label">كلمة المرور</label>
                <input
                  id="password"
                  type="password"
                  autoComplete="current-password"
                  className="form-input"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  placeholder="أدخل كلمة المرور"
                  data-testid="input-password"
                />
              </div>
            </>
          ) : (
            <div className="form-group">
              <label htmlFor="access-code" className="form-label">رمز دخول الطالب</label>
              <input
                id="access-code"
                type="text"
                autoComplete="off"
                className={`form-input ${styles.codeInput}`}
                value={accessCode}
                onChange={(e) => setAccessCode(e.target.value.toUpperCase())}
                required
                placeholder="مثال: ABC-1234"
                maxLength={10}
                data-testid="input-access-code"
              />
              <p className={styles.hint}>
                اطلب رمز الدخول من المعلمة أو الباحثة
              </p>
            </div>
          )}

          {error && (
            <div className="alert alert-error" data-testid="error-message">
              {error}
            </div>
          )}

          <button
            type="submit"
            className="btn btn-primary"
            style={{ width: "100%", marginTop: "var(--space-2)" }}
            disabled={loading}
            data-testid="login-submit"
          >
            {loading ? "جاري الدخول..." : "دخول"}
          </button>
        </form>
      </div>
    </main>
  );
}

export default function LoginPage() {
  return (
    <Suspense>
      <LoginForm />
    </Suspense>
  );
}
