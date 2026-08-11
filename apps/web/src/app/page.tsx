import Link from "next/link";

export default function Home() {
  return (
    <main style={{
      minHeight: "100vh",
      display: "flex",
      flexDirection: "column",
      alignItems: "center",
      justifyContent: "center",
      background: "linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 50%, #f0fdf4 100%)",
      fontFamily: "var(--font-noto-kufi), sans-serif",
      direction: "rtl",
      padding: "2rem",
    }}>
      {/* Himma SVG Logo */}
      <svg width="80" height="80" viewBox="0 0 80 80" fill="none" xmlns="http://www.w3.org/2000/svg" aria-label="شعار هِمّة">
        <circle cx="40" cy="40" r="40" fill="#0ea5e9"/>
        <text x="40" y="52" textAnchor="middle" fill="white" fontSize="32" fontWeight="bold" fontFamily="sans-serif">هـ</text>
      </svg>

      <h1 style={{ fontSize: "2.5rem", color: "#0c4a6e", margin: "1rem 0 0.5rem", fontWeight: 700 }}>
        هِمّة
      </h1>
      <p style={{ color: "#475569", fontSize: "1.1rem", marginBottom: "2.5rem", textAlign: "center", maxWidth: 400 }}>
        منصة تقييم مهارات القراءة العربية للمرحلة الابتدائية
      </p>

      <div style={{ display: "flex", gap: "1rem", flexWrap: "wrap", justifyContent: "center" }}>
        <Link
          href="/login"
          id="btn-login-researcher"
          style={{
            display: "inline-block",
            padding: "0.85rem 2rem",
            background: "#0ea5e9",
            color: "white",
            borderRadius: "8px",
            textDecoration: "none",
            fontWeight: 700,
            fontSize: "1rem",
            boxShadow: "0 4px 12px rgba(14,165,233,0.3)",
            transition: "transform 0.15s",
          }}
        >
          دخول الباحثة / الطالب
        </Link>
      </div>

      <p style={{ marginTop: "3rem", color: "#94a3b8", fontSize: "0.8rem" }}>
        المرحلة 2 · v0.1 · stage/02-content
      </p>
    </main>
  );
}
