"use client";

import Link from "next/link";
import type { Route } from "next";
import { useCallback, useEffect, useState } from "react";
import { usePathname, useRouter } from "next/navigation";
import { FileClock, Inbox, LogOut, Settings, Upload, Rows3, Trash2, PanelLeftClose, PanelLeftOpen } from "lucide-react";
import { api } from "@/lib/api";

const nav: Array<{ href: Route; label: string; icon: typeof Upload; badge?: boolean }> = [
  { href: "/upload", label: "Upload Quotation PDFs", icon: Upload },
  { href: "/history", label: "History", icon: FileClock },
  { href: "/admin", label: "Admin", icon: Settings },
  { href: "/inbox", label: "Inbox", icon: Inbox, badge: true },
  { href: "/trash", label: "Trash", icon: Trash2 },
];

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const [collapsed, setCollapsed] = useState(true);
  const [signingOut, setSigningOut] = useState(false);
  const [signOutError, setSignOutError] = useState("");
  const [unreadCount, setUnreadCount] = useState(0);

  useEffect(() => {
    setCollapsed(localStorage.getItem("rl-sidebar-collapsed") !== "false");
  }, []);

  const loadUnread = useCallback(async () => {
    try {
      const result = await api<{ unread_count: number }>("/notifications/unread-count");
      setUnreadCount(result.unread_count);
    } catch {
      setUnreadCount(0);
    }
  }, []);

  useEffect(() => {
    loadUnread();
  }, [loadUnread, pathname]);

  function toggleSidebar() {
    setCollapsed((current) => {
      const next = !current;
      localStorage.setItem("rl-sidebar-collapsed", String(next));
      return next;
    });
  }

  async function signOut() {
    setSigningOut(true);
    setSignOutError("");
    try {
      await api<void>("/auth/logout", { method: "POST" });
      router.replace("/login");
    } catch (error) {
      setSignOutError(error instanceof Error ? error.message : "Could not sign out. Please try again.");
    } finally {
      setSigningOut(false);
    }
  }

  return (
    <div className="min-h-screen bg-white">
      <header className="border-b border-rl-line bg-white">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-5 py-4">
          <Link href="/upload" className="flex items-center gap-3 font-bold text-rl-textStrong">
            <Rows3 aria-hidden="true" size={22} />
            <span>Risklocker Quotation Converter</span>
          </Link>
          <button
            className="rl-button rl-button-secondary"
            onClick={signOut}
            disabled={signingOut}
            type="button"
          >
            <LogOut aria-hidden="true" size={18} />
            {signingOut ? "Signing out" : "Sign out"}
          </button>
        </div>
      </header>
      <div className={`mx-auto grid max-w-[1560px] grid-cols-1 gap-5 px-5 py-5 ${collapsed ? "lg:grid-cols-[72px_1fr]" : "lg:grid-cols-[230px_1fr]"}`}>
        <nav className="lg:border-r lg:border-rl-line lg:pr-3">
          <button
            className="rl-button rl-button-secondary mb-3 hidden w-full lg:inline-flex"
            type="button"
            onClick={toggleSidebar}
            aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}
          >
            {collapsed ? <PanelLeftOpen aria-hidden="true" size={18} /> : <PanelLeftClose aria-hidden="true" size={18} />}
            <span className={collapsed ? "sr-only" : ""}>{collapsed ? "Expand" : "Collapse"}</span>
          </button>
          <div className="grid gap-2">
            {nav.map((item) => {
              const Icon = item.icon;
              const active = pathname === item.href || pathname.startsWith(`${item.href}/`);
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  title={collapsed ? item.label : undefined}
                  className={`relative flex min-h-11 items-center gap-3 rounded-md px-3 py-2 font-bold ${
                    active ? "bg-rl-black text-rl-inverse" : "text-rl-textStrong hover:bg-rl-soft"
                  }`}
                >
                  <Icon aria-hidden="true" size={18} />
                  <span className={collapsed ? "lg:sr-only" : ""}>{item.label}</span>
                  {item.badge && unreadCount > 0 ? (
                    <span
                      className={`absolute right-2 top-1/2 flex h-5 min-w-[20px] -translate-y-1/2 items-center justify-center rounded-full bg-rl-red px-1 text-[11px] font-bold leading-tight text-white ${collapsed ? "lg:right-0.5 lg:top-0.5 lg:-translate-y-0" : ""}`}
                      aria-label={`${unreadCount} unread notification${unreadCount === 1 ? "" : "s"}`}
                    >
                      {unreadCount}
                    </span>
                  ) : null}
                </Link>
              );
            })}
          </div>
        </nav>
        <main>
          {signOutError ? <p role="alert" className="mb-4 rounded-md border border-rl-red bg-red-50 p-3 font-bold text-rl-red">{signOutError}</p> : null}
          {children}
        </main>
      </div>
    </div>
  );
}
