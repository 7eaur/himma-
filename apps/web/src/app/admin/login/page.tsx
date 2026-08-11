"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

export default function AdminLogin() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
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
      setLoading(false);
    }
  };

  return (
    <div className="auth-container admin-layout">
      <div className="auth-card">
        <h2 style={{ marginBottom: "1.5rem" }}>دخول الإدارة</h2>
        
        {error && <div className="alert alert-error" data-testid="error-message">{error}</div>}
        
        <form onSubmit={handleSubmit}>
          <input
            type="text"
            className="input-field"
            placeholder="اسم المستخدم"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            data-testid="input-username"
            required
            disabled={loading}
          />
          <input
            type="password"
            className="input-field"
            placeholder="كلمة المرور"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            data-testid="input-password"
            required
            disabled={loading}
          />
          
          <button 
            type="submit" 
            className="btn btn-primary btn-large" 
            style={{ width: "100%", marginTop: "1rem" }}
            disabled={loading}
            data-testid="login-submit"
          >
            {loading ? "جاري الدخول..." : "دخول"}
          </button>
        </form>
      </div>
    </div>
  );
}
