import React from "react";
import type { RemediationTier } from "@/lib/types";

interface TierChipProps {
  tier: RemediationTier | string;
  reason?: string;
  className?: string;
}

const TIER_CONFIG: Record<
  string,
  { label: string; style: string }
> = {
  AUTO_FIX: {
    label: "Auto-fix",
    style: "bg-accent/15 border-accent/40 text-accent-bright",
  },
  DEPENDENCY: {
    label: "Dependency",
    style: "bg-white/[0.05] border-white/15 text-ink-muted",
  },
  ESCALATE: {
    label: "Escalated",
    style: "bg-[#ff9345]/15 border-[#ff9345]/40 text-[#ffa86b]",
  },
  UNSUPPORTED_LANG: {
    label: "Adapter not enabled",
    style: "bg-transparent border-dashed border-white/20 text-ink-dim",
  },
};

export default function TierChip({ tier, reason, className = "" }: TierChipProps) {
  const cfg = TIER_CONFIG[tier] || {
    label: tier,
    style: "bg-white/5 border-white/10 text-ink-dim",
  };

  return (
    <span
      title={reason || cfg.label}
      className={`inline-flex items-center px-2 py-0.5 rounded-chip border text-[11px] font-medium tracking-tight select-none cursor-default transition-colors ${cfg.style} ${className}`}
    >
      {cfg.label}
    </span>
  );
}
