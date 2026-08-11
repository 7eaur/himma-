import Link from "next/link";
import styles from "./admin.module.css";

export default function AdminLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className={`admin-layout ${styles.adminContainer}`}>
      <aside className={styles.sidebar}>
        <div className={styles.sidebarLogo}>
          <span className="logo-text" style={{ fontSize: "2rem", color: "var(--primary)" }}>الإدارة</span>
        </div>
        
        <nav className={styles.nav}>
          <Link href="/admin" className={styles.navItem}>
            📊 لوحة القيادة
          </Link>
          <Link href="/admin/students" className={styles.navItem}>
            👥 قائمة الطلاب
          </Link>
          <Link href="/admin/students/new" className={styles.navItem}>
            ➕ إنشاء طالب
          </Link>
          <Link href="/admin/audio-review" className={styles.navItem}>
            🎙️ مراجعة الصوت
          </Link>
          <Link href="/admin/account" className={styles.navItem}>
            ⚙️ الحساب
          </Link>
        </nav>

        <div className={styles.logoutWrapper}>
          <button className="btn" style={{ width: "100%", background: "var(--bg-muted)" }}>
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
