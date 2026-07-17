"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const items = [
  { href: "/admin", label: "Users" },
  { href: "/admin/companies", label: "Companies" },
  { href: "/admin/templates", label: "Templates" },
  { href: "/admin/benefits", label: "Benefits" },
  { href: "/admin/storage", label: "Storage" },
  { href: "/admin/checks", label: "System Checks" }
] as const;

export function AdminNav() {
  const pathname = usePathname();
  return (
    <nav className="flex flex-wrap gap-2" aria-label="Admin sections">
      {items.map((item) => {
        const active = pathname === item.href || pathname.startsWith(`${item.href}/`);
        return (
          <Link
            key={item.href}
            href={item.href}
            className={`rounded-md border px-3 py-2 text-sm font-bold ${active ? "border-rl-black bg-rl-black text-rl-inverse" : "border-rl-line text-rl-textStrong hover:bg-rl-soft"}`}
          >
            {item.label}
          </Link>
        );
      })}
    </nav>
  );
}
