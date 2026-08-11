"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Image from "next/image";
import styles from "./admin-login.module.css";

export default function AdminLogin() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const router = useRouter();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      const res = await fetch("/api/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, password }),
      });

      if (!res.ok) throw new Error("بيانات الدخول غير صحيحة");
      
      router.push("/admin");
    } catch (err: any) {
      setError(err.message || "حدث خطأ في الاتصال بالخادم");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className={styles.container}>
      <div className={styles.card}>
        <div className={styles.formSide}>
          <div className={styles.logoMobile}>
            <Image src="/brand/logo-navy.svg" alt="هِمّة" width={120} height={60} />
          </div>
          
          <div className={styles.header}>
            <h1 className={styles.title}>مرحباً بعودتك</h1>
            <p className={styles.subtitle}>الرجاء إدخال بيانات الدخول للوصول إلى لوحة الإدارة</p>
          </div>
          
          {error && <div className={styles.errorAlert} data-testid="error-message">{error}</div>}
          
          <form onSubmit={handleSubmit} className={styles.form}>
            <div className={styles.inputGroup}>
              <label htmlFor="username" className={styles.label}>اسم المستخدم</label>
              <input
                id="username"
                type="text"
                className={styles.input}
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                data-testid="input-username"
                required
                disabled={loading}
                autoFocus
              />
            </div>

            <div className={styles.inputGroup}>
              <label htmlFor="password" className={styles.label}>كلمة المرور</label>
              <div className={styles.passwordWrapper}>
                <input
                  id="password"
                  type={showPassword ? "text" : "password"}
                  className={styles.input}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  data-testid="input-password"
                  required
                  disabled={loading}
                />
                <button
                  type="button"
                  className={styles.togglePassword}
                  onClick={() => setShowPassword(!showPassword)}
                  tabIndex={-1}
                >
                  {showPassword ? "إخفاء" : "إظهار"}
                </button>
              </div>
            </div>
            
            <button 
              type="submit" 
              className={styles.submitBtn} 
              disabled={loading}
              data-testid="login-submit"
            >
              {loading ? "جاري التحقق..." : "دخول"}
            </button>
          </form>
        </div>

        <div className={styles.brandSide}>
          <div className={styles.brandContent}>
            <Image src="/brand/logo-white.svg" alt="هِمّة" width={180} height={90} className={styles.brandLogo} />
            <h2 className={styles.brandTagline}>أتعلم، أتطور، أصل إلى القمة</h2>
            <div className={styles.brandVisual}>
              {/* Fallback to simple illustration if no explicit characters image found */}
              <div className={styles.shape1}></div>
              <div className={styles.shape2}></div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
