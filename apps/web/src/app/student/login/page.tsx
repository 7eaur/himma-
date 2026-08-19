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
    // Basic formatting for ABC-1234
    let val = e.target.value.toUpperCase().replace(/[^A-Z0-9]/g, "");
    if (val.length > 3) {
      val = val.slice(0, 3) + "-" + val.slice(3, 7);
    }
    setAccessCode(val);
  };

  return (
    <div className="min-h-screen bg-bg flex flex-col items-center justify-center p-4 font-tajawal relative overflow-hidden">
      {/* Decorative background elements */}
      <div className="absolute top-[-10%] right-[-5%] w-64 h-64 bg-yellow/20 rounded-full blur-3xl -z-10"></div>
      <div className="absolute bottom-[-10%] left-[-5%] w-80 h-80 bg-primary/20 rounded-full blur-3xl -z-10"></div>

      <div className="w-full max-w-md bg-white rounded-3xl shadow-xl p-8 border-4 border-white">
        <div className="flex justify-center mb-8">
          <Image src="/brand/logo-gradient.svg" alt="Himma Logo" width={180} height={60} />
        </div>
        
        <div className="flex justify-center mb-8">
          <Image 
            src="/characters/girl-welcome.png" 
            alt="Welcome" 
            width={160} 
            height={200}
            className="drop-shadow-md hover:scale-105 transition-transform duration-300" 
          />
        </div>
        
        <h1 className="text-3xl font-bold text-navy mb-8 text-center">أهلاً بك يا بطل!</h1>
        
        {error && (
          <div data-testid="error-message" className="alert-error text-center mb-6 font-bold">
            {error}
          </div>
        )}
        
        <form onSubmit={handleSubmit} className="space-y-6">
          <div>
            <label className="block text-navy font-bold text-lg mb-3 text-center">
              أدخل رمز الدخول السري الخاص بك
            </label>
            <input
              type="text"
              className="w-full border-4 border-border rounded-2xl p-4 text-center text-3xl font-mono font-bold text-primary tracking-widest uppercase transition-colors focus:border-primary focus:outline-none placeholder-muted/50"
              value={accessCode}
              onChange={handleAccessCodeChange}
              placeholder="ABC-1234"
              maxLength={8}
              required
              dir="ltr"
            />
          </div>
          
          <button
            type="submit"
            className="w-full bg-primary hover:bg-[#276bb8] text-white font-bold text-xl py-5 rounded-2xl shadow-lg transition-transform hover:-translate-y-1 active:translate-y-0"
            disabled={isLoading || accessCode.length < 3}
          >
            {isLoading ? <span className="spinner mx-auto border-4"></span> : "يلا نبدأ!"}
          </button>
        </form>
      </div>
    </div>
  );
}
