"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { Home, LayoutDashboard, Search, PlayCircle, Plus } from "lucide-react";
import { useSummary } from "@/lib/api";

interface NavItem {
  name: string;
  href: string;
  icon: React.ElementType;
  badge?: boolean;
}

export default function FloatingNav() {
  const pathname = usePathname();
  const { data: summary } = useSummary(15000);

  const hasFixReady = (summary?.fix_ready_count ?? 0) > 0;

  const items: NavItem[] = [
    { name: "Home", href: "/", icon: Home },
    { name: "Dashboard", href: "/dashboard", icon: LayoutDashboard },
    { name: "Findings", href: "/findings", icon: Search, badge: hasFixReady },
    { name: "Runs", href: "/runs", icon: PlayCircle },
  ];

  return (
    <nav
      className="fixed bottom-6 left-1/2 -translate-x-1/2 z-50 nav-pill p-1.5 flex items-center gap-1 shadow-2xl"
      aria-label="Main Navigation"
    >
      {items.map((item) => {
        const isActive =
          item.href === "/"
            ? pathname === "/"
            : pathname.startsWith(item.href);
        const Icon = item.icon;

        return (
          <Link
            key={item.href}
            href={item.href}
            className={`relative flex items-center gap-2 px-3.5 py-2 rounded-[10px] text-[13px] font-medium transition-all duration-200 select-none ${
              isActive
                ? "bg-white/[0.08] text-white shadow-sm"
                : "text-ink-muted hover:text-white hover:bg-white/[0.03]"
            }`}
          >
            {isActive && (
              <span className="w-1.5 h-1.5 rounded-full bg-accent shrink-0 hidden sm:inline-block" />
            )}
            <Icon size={16} className="shrink-0" />
            <span className="hidden sm:inline-block">{item.name}</span>
            {item.badge && (
              <span
                className="inline-flex items-center justify-center w-3.5 h-3.5 rounded-full bg-accent text-[10px] text-white font-bold"
                title={`${summary?.fix_ready_count} fix-ready findings`}
              >
                <Plus size={10} />
              </span>
            )}
          </Link>
        );
      })}
    </nav>
  );
}
