"use client";

import { useState } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import Image from "next/image";
import { LayoutDashboard, Users, UserPlus, Mic, BarChart2, Settings, LogOut, Menu, X } from "lucide-react";

export default function AdminDashboardLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
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
      router.push("/");
    } catch (err) {
      console.error("Logout failed", err);
    }
  };

  const SidebarContent = () => (
    <div className="flex flex-col h-full bg-white font-plex">
      <div className="p-6 flex justify-center items-center border-b border-border">
        <Image src="/brand/logo-navy.svg" alt="Himma Logo" width={120} height={40} />
      </div>
      
      <nav className="flex-1 px-4 py-6 space-y-2 overflow-y-auto">
        {navItems.map((item) => {
          const isActive = pathname === item.href;
          const Icon = item.icon;
          return (
            <Link
              key={item.href}
              href={item.href}
              onClick={() => setMobileMenuOpen(false)}
              className={`flex items-center gap-3 px-4 py-3 rounded-md transition-colors ${
                isActive 
                  ? "bg-bg text-primary font-medium" 
                  : "text-muted hover:bg-bg hover:text-navy"
              }`}
            >
              <Icon size={20} className={isActive ? "text-primary" : "text-muted"} />
              <span>{item.label}</span>
            </Link>
          );
        })}
      </nav>

      <div className="p-4 border-t border-border">
        <button
          onClick={handleLogout}
          className="flex items-center gap-3 px-4 py-3 w-full text-red-600 hover:bg-red-50 rounded-md transition-colors font-medium"
        >
          <LogOut size={20} />
          <span>تسجيل الخروج</span>
        </button>
      </div>
    </div>
  );

  return (
    <div className="sidebar-layout font-plex">
      {/* Desktop Sidebar */}
      <aside className="sidebar">
        <SidebarContent />
      </aside>

      {/* Mobile Sidebar Overlay */}
      {mobileMenuOpen && (
        <div className="md:hidden fixed inset-0 z-50 flex">
          <div className="fixed inset-0 bg-black/50" onClick={() => setMobileMenuOpen(false)} />
          <div className="relative w-64 max-w-sm flex-1 bg-white flex flex-col z-50">
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

      {/* Main Content */}
      <main className="sidebar-content flex flex-col">
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
