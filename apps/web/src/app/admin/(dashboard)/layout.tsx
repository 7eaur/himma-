"use client";

import { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import Image from "next/image";
import { LayoutDashboard, Users, UserPlus, Mic, BarChart2, Settings, LogOut, Menu, X } from "lucide-react";

export default function AdminDashboardLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const navItems = [
    { href: "/admin", label: "لوحة القيادة", icon: LayoutDashboard },
    { href: "/admin/students", label: "الطلاب", icon: Users },
    { href: "/admin/students/new", label: "إضافة طالب", icon: UserPlus },
    { href: "/admin/audio-review", label: "مراجعة التسجيلات", icon: Mic },
    { href: "/admin/reports", label: "التقارير", icon: BarChart2 },
    { href: "/admin/settings", label: "الإعدادات", icon: Settings },
  ];

  const handleLogout = async () => {
    try {
      await fetch("/api/auth/logout", { method: "POST" });
      window.location.href = "/";
    } catch (err) {
      console.error("Logout failed", err);
    }
  };

  const SidebarContent = () => (
    <>
      <div className="sidebar-brand">
        <Image src="/brand/logo-navy.svg" alt="Himma Logo" width={120} height={40} />
      </div>
      
      <nav className="sidebar-nav">
        {navItems.map((item) => {
          const isActive = pathname === item.href;
          const Icon = item.icon;
          return (
            <Link
              key={item.href}
              href={item.href}
              onClick={() => setMobileMenuOpen(false)}
              className={`sidebar-nav-item ${isActive ? "active" : ""}`}
            >
              <Icon size={20} className="sidebar-nav-icon" />
              <span>{item.label}</span>
            </Link>
          );
        })}
      </nav>

      <div className="sidebar-footer">
        <div className="sidebar-user">
          <div className="sidebar-avatar">ب</div>
          <div className="sidebar-user-name">الباحثة</div>
        </div>
        <button onClick={handleLogout} className="sidebar-logout">
          <LogOut size={18} />
          <span>تسجيل الخروج</span>
        </button>
      </div>
    </>
  );

  return (
    <div className="sidebar-layout" dir="rtl">
      <aside className="sidebar hidden md:flex">
        <SidebarContent />
      </aside>

      {mobileMenuOpen && (
        <div className="md:hidden fixed inset-0 z-50 flex">
          <div className="fixed inset-0 bg-black/50" onClick={() => setMobileMenuOpen(false)} />
          <div className="relative w-64 max-w-sm flex-1 bg-white flex flex-col z-50 h-full">
            <button 
              onClick={() => setMobileMenuOpen(false)}
              className="absolute top-4 left-4 p-2 text-muted hover:bg-bg rounded-md"
            >
              <X size={24} />
            </button>
            <SidebarContent />
          </div>
        </div>
      )}

      <main className="sidebar-content">
        <div className="md:hidden flex items-center justify-between bg-white p-4 border-b border-border mb-4 rounded-md shadow-sm">
          <Image src="/brand/logo-navy.svg" alt="Himma Logo" width={100} height={32} />
          <button 
            onClick={() => setMobileMenuOpen(true)}
            className="p-2 text-navy hover:bg-bg rounded-md"
          >
            <Menu size={24} />
          </button>
        </div>
        {children}
      </main>
    </div>
  );
}
