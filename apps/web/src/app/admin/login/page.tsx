"use client";

import { useState } from "react";
import Image from "next/image";

export default function AdminLogin() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError("");

    try {
      const res = await fetch("/api/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, password }),
      });

      if (res.ok) {
        window.location.href = "/admin";
      } else {
        const data = await res.json();
        setError(data.detail || "Invalid credentials");
      }
    } catch (err) {
      setError("An error occurred during login");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="admin-login-root" dir="rtl">
      <div className="admin-login-brand">
        <Image src="/brand/logo-white.svg" alt="Himma Logo" width={140} height={48} />
        <h2 className="admin-brand-title">تسجيل دخول الباحثة</h2>
        <p className="admin-brand-sub">لوحة التحكم ومتابعة الطلاب</p>
        <Image src="/characters/girl/welcome.png" alt="Character" width={160} height={200} className="admin-brand-char" priority />
        <p className="admin-brand-tagline">أتعلم، أتطور، أصل إلى القمة</p>
      </div>

      <div className="admin-login-form-wrap">
        <div className="admin-login-form-box">
          <div className="md:hidden flex justify-center mb-8">
            <Image src="/brand/logo-navy.svg" alt="Himma Logo" width={140} height={48} />
          </div>
          <h1>مرحباً بك مجدداً</h1>
          <p>أدخلي بياناتك للوصول إلى لوحة التحكم</p>

          {error && (
            <div data-testid="error-message" className="alert-error text-center mb-4">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-navy font-medium mb-2">اسم المستخدم</label>
              <input
                type="text"
                className="input-field"
                data-testid="input-username"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                required
                dir="ltr"
              />
            </div>
            
            <div>
              <label className="block text-navy font-medium mb-2">كلمة المرور</label>
              <input
                type="password"
                className="input-field"
                data-testid="input-password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                dir="ltr"
              />
            </div>
            
            <button
              type="submit"
              className="btn-primary w-full mt-6"
              data-testid="login-submit"
              disabled={isLoading}
            >
              {isLoading ? <span className="spinner"></span> : "دخول"}
            </button>
          </form>
          <p className="admin-login-hint">الوصول مصرح للباحثين والإداريين فقط</p>
        </div>
      </div>
    </div>
  );
}
