"use client";

import { useState } from "react";
import Image from "next/image";

export default function StudentLogin() {
  const [accessCode, setAccessCode] = useState("");
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError("");

    try {
      const res = await fetch("/api/auth/student-login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ access_code: accessCode }),
      });

      if (res.ok) {
        window.location.href = "/student";
      } else {
        const data = await res.json();
        setError(data.detail || "رمز الدخول غير صحيح");
      }
    } catch (err) {
      setError("حدث خطأ أثناء تسجيل الدخول");
    } finally {
      setIsLoading(false);
    }
  };

  const handleAccessCodeChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    let val = e.target.value.toUpperCase().replace(/[^A-Z0-9]/g, "");
    if (val.length > 3) {
      val = val.slice(0, 3) + "-" + val.slice(3, 7);
    }
    setAccessCode(val);
  };

  return (
    <div className="student-login-root" dir="rtl">
      <div className="student-login-amb-1" />
      <div className="student-login-amb-2" />

      <div className="student-login-card">
        <div className="flex justify-center student-login-logo">
          <Image src="/brand/logo-gradient.svg" alt="Himma Logo" width={180} height={60} />
        </div>
        
        <div className="flex justify-center mb-6">
          <Image 
            src="/characters/boy/welcome.png" 
            alt="Welcome" 
            width={140} 
            height={180}
            className="drop-shadow-md hover:scale-105 transition-transform duration-300" 
          />
        </div>
        
        <h1 className="student-login-title">أهلاً بك يا بطل!</h1>
        <p className="student-login-sub">أدخل رمز الدخول السري لنبدأ التعلم معاً</p>
        
        {error && (
          <div data-testid="error-message" className="alert-error text-center mb-6 font-bold">
            {error}
          </div>
        )}
        
        <form onSubmit={handleSubmit}>
          <input
            type="text"
            className="student-login-code-input mb-4"
            data-testid="input-access-code"
            value={accessCode}
            onChange={handleAccessCodeChange}
            placeholder="ABC-1234"
            maxLength={8}
            required
            dir="ltr"
          />
          
          <button
            type="submit"
            className="student-login-btn"
            data-testid="student-login-submit"
            disabled={isLoading || accessCode.length < 8}
          >
            {isLoading ? <span className="spinner mx-auto border-4"></span> : "يلا نبدأ!"}
          </button>
        </form>
      </div>
    </div>
  );
}
