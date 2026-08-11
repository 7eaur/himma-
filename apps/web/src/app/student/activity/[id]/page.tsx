"use client";

import { useParams, useRouter } from "next/navigation";
import Link from "next/link";

export default function StudentActivity() {
  const params = useParams();
  const router = useRouter();

  return (
    <div style={{ padding: "2rem", maxWidth: "800px", margin: "0 auto", textAlign: "center" }}>
      <h1 style={{ marginBottom: "2rem" }}>نشاط #{params.id}</h1>
      
      <div style={{ background: "white", padding: "3rem", borderRadius: "var(--radius-lg)", boxShadow: "0 4px 20px rgba(0,0,0,0.05)" }}>
        <p style={{ fontSize: "1.2rem", marginBottom: "2rem" }}>
          هذا النشاط قيد التطوير. سيتم عرض محتوى النشاط هنا.
        </p>
        
        <Link href="/student" className="btn btn-primary">
          العودة للوحة الرئيسية
        </Link>
      </div>
    </div>
  );
}
