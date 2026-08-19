"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import styles from "./admin.module.css";

export default function AdminLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter();

  async function handleLogout() {
    await fetch("/api/auth/logout", { method: "POST", credentials: "include" });
    router.push("/admin/login");
  }

  return (
    <div className={`admin-layout ${styles.adminContainer}`}>
      <aside className={styles.sidebar}>
        <div className={styles.sidebarLogo}>
          <span className="logo-text" style={{ fontSize: "2rem", color: "var(--primary)" }}>الإدارة</span>
        </div>
        
        <nav className={styles.nav}>
          <Link href="/admin" className={styles.navItem}>لوحة القيادة</Link>
          <Link href="/admin/students" className={styles.navItem}>قائمة الطلاب</Link>
          <Link href="/admin/students/new" className={styles.navItem}>إنشاء طالب</Link>
          <Link href="/admin/audio-review" className={styles.navItem}>مراجعة الصوت</Link>
          <Link href="/admin/account" className={styles.navItem}>الحساب</Link>
        </nav>

        <div className={styles.logoutWrapper}>
          <button
            data-testid="btn-logout"
            className="btn"
            style={{ width: "100%", background: "var(--bg-muted)" }}
            onClick={handleLogout}
          >
            تسجيل الخروج
          </button>
        </div>
      </aside>

      <main className={styles.mainContent}>
        {children}
      </main>
    </div>
  );
}
