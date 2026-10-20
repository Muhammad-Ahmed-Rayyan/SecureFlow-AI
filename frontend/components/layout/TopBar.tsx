"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { Shield } from "lucide-react";
import PillButton from "../ui/PillButton";

export default function TopBar() {
  const [online, setOnline] = useState<boolean | null>(null);

  useEffect(() => {
    const checkHealth = async () => {
      try {
        const res = await fetch("/api/health");
        if (res.ok) setOnline(true);
        else setOnline(false);
      } catch {
        setOnline(false);
      }
    };
    checkHealth();
    const interval = setInterval(checkHealth, 30000);
    return () => clearInterval(interval);
  }, []);

  return (
    <header className="sticky top-0 z-40 w-full h-[72px] px-8 flex items-center justify-between border-b border-white/[0.04] bg-[#04060d]/80 backdrop-blur-md">
      {/* Brand */}
      <Link href="/" className="flex items-center gap-2.5 group">
        <div className="w-8 h-8 rounded-lg bg-accent/20 border border-accent/40 flex items-center justify-center text-accent-bright group-hover:scale-105 transition-transform">
          <Shield size={18} />
        </div>
        <div className="font-sans text-[15px] font-bold tracking-[0.08em] uppercase select-none">
          <span className="text-white">SECURE</span>
          <span className="text-ink-muted">FLOW</span>
          <span className="text-accent ml-0.5">.AI</span>
        </div>
      </Link>

      {/* Right controls */}
      <div className="flex items-center gap-4">
        {/* Health pill */}
        <div
          className="flex items-center gap-2 px-3 py-1 rounded-full bg-white/[0.03] border border-white/10 text-[12px] text-ink-muted select-none"
          title={online === true ? "Backend connected" : online === false ? "Backend unreachable" : "Checking status..."}
        >
          <span
            className={`w-2 h-2 rounded-full ${
              online === true
                ? "bg-emerald-400 shadow-[0_0_8px_rgba(52,211,153,0.5)]"
                : online === false
                ? "bg-[#ff4c6a]"
                : "bg-ink-dim animate-pulse"
            }`}
          />
          <span className="font-medium">
            {online === true ? "API online" : online === false ? "API offline" : "Connecting..."}
          </span>
        </div>

        {/* GitHub link */}
        <PillButton
          variant="ghost"
          size="sm"
          href="https://github.com/Muhammad-Ahmed-Rayyan/SecureFlow-AI"
          title="View source on GitHub"
        >
          View on GitHub
        </PillButton>
      </div>
    </header>
  );
}
