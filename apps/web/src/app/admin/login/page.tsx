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
    <div className="min-h-screen bg-bg flex items-center justify-center p-4 font-plex">
      <div className="card w-full max-w-md">
        <div className="flex justify-center mb-8">
          <Image src="/brand/logo-navy.svg" alt="Himma Logo" width={140} height={48} />
        </div>
        
        <h1 className="text-2xl font-bold text-navy mb-6 text-center">تسجيل دخول الباحثة</h1>
        
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
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              dir="ltr"
            />
          </div>
          
          <button
            type="submit"
            className="btn-primary w-full mt-6"
            disabled={isLoading}
          >
            {isLoading ? <span className="spinner"></span> : "دخول"}
          </button>
        </form>
      </div>
    </div>
  );
}
