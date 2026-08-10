"use client";

import { useState, FormEvent } from "react";
import { useRouter } from "next/navigation";

export default function LoginPage() {
  const router = useRouter();
  const [mode, setMode] = useState<"researcher" | "student">("researcher");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [accessCode, setAccessCode] = useState("");
  const [error, setError] = useState("");

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError("");

    const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

    try {
      if (mode === "researcher") {
        const res = await fetch(`${apiUrl}/auth/login`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          credentials: "include",
          body: JSON.stringify({ username, password }),
        });
        if (!res.ok) {
          setError("بيانات الدخول غير صحيحة");
          return;
        }
        router.push("/researcher");
      } else {
        const res = await fetch(`${apiUrl}/auth/student-login`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          credentials: "include",
          body: JSON.stringify({ access_code: accessCode }),
        });
        if (!res.ok) {
          setError("رمز الدخول غير صحيح");
          return;
        }
        router.push("/student");
      }
    } catch {
      setError("حدث خطأ في الاتصال");
    }
  }

  return (
    <div style={{ maxWidth: 400, margin: "4rem auto", padding: "2rem", fontFamily: "sans-serif", direction: "rtl" }}>
      <h1 style={{ textAlign: "center" }}>تسجيل الدخول</h1>

      <div style={{ display: "flex", gap: "1rem", justifyContent: "center", marginBottom: "1.5rem" }}>
        <button
          type="button"
          onClick={() => setMode("researcher")}
          style={{ fontWeight: mode === "researcher" ? "bold" : "normal" }}
          data-testid="tab-researcher"
        >
          باحثة
        </button>
        <button
          type="button"
          onClick={() => setMode("student")}
          style={{ fontWeight: mode === "student" ? "bold" : "normal" }}
          data-testid="tab-student"
        >
          طالب
        </button>
      </div>

      <form onSubmit={handleSubmit}>
        {mode === "researcher" ? (
          <>
            <div style={{ marginBottom: "1rem" }}>
              <label htmlFor="username">اسم المستخدم</label>
              <input
                id="username"
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                required
                style={{ display: "block", width: "100%", padding: "0.5rem" }}
              />
            </div>
            <div style={{ marginBottom: "1rem" }}>
              <label htmlFor="password">كلمة المرور</label>
              <input
                id="password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                style={{ display: "block", width: "100%", padding: "0.5rem" }}
              />
            </div>
          </>
        ) : (
          <div style={{ marginBottom: "1rem" }}>
            <label htmlFor="access-code">رمز الدخول</label>
            <input
              id="access-code"
              type="text"
              value={accessCode}
              onChange={(e) => setAccessCode(e.target.value)}
              required
              style={{ display: "block", width: "100%", padding: "0.5rem" }}
            />
          </div>
        )}

        {error && <p style={{ color: "red" }} data-testid="error-message">{error}</p>}

        <button type="submit" style={{ width: "100%", padding: "0.75rem" }} data-testid="login-submit">
          دخول
        </button>
      </form>
    </div>
  );
}
