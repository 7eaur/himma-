"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Image from "next/image";

export default function StudentLogin() {
  const [accessCode, setAccessCode] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const router = useRouter();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      const res = await fetch("/api/auth/student-login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ access_code: accessCode.toUpperCase() }),
      });

      if (!res.ok) throw new Error("رمز الدخول غير صحيح");
      
      window.location.href = "/student";
    } catch (err: any) {
      setError(err.message || "حدث خطأ في الاتصال بالخادم");
      setLoading(false);
    }
  };

  return (
    <div className="auth-container">
      <div className="auth-card">
        <div className="logo-container" style={{ marginBottom: "2rem" }}>
          <span className="logo-text" style={{ fontSize: "3rem" }}>هِمّة</span>
        </div>
        
        <h2 style={{ marginBottom: "1.5rem" }}>دخول الطالب</h2>
        
        {error && <div className="alert alert-error" data-testid="error-message">{error}</div>}
        
        <form onSubmit={handleSubmit}>
          <input
            type="text"
            className="input-field"
            placeholder="رمز الدخول (مثال: ABC-1234)"
            value={accessCode}
            onChange={(e) => setAccessCode(e.target.value.toUpperCase())}
            data-testid="input-access-code"
            required
            disabled={loading}
          />
          <p className="link-muted" style={{ marginBottom: "1.5rem", fontSize: "0.9rem" }}>
            اطلب رمز الدخول من المعلمة أو الباحثة
          </p>
          
          <button 
            type="submit" 
            className="btn btn-primary btn-large" 
            style={{ width: "100%" }}
            disabled={loading}
          >
            {loading ? "جاري الدخول..." : "دخول"}
          </button>
        </form>
      </div>
    </div>
  );
}
