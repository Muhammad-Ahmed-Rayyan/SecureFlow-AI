import React from "react";
import type { FindingStatus } from "@/lib/types";

interface StatusPillProps {
  status: FindingStatus | string;
  size?: "md" | "sm";
  className?: string;
}

const STATUS_CONFIG: Record<
  string,
  { label: string; bg: string; text: string; dot?: string; pulsing?: boolean }
> = {
  NEW: {
    label: "New",
    bg: "bg-white/[0.04] border-white/10",
    text: "text-ink-muted",
    dot: "bg-ink-dim",
  },
  QUEUED: {
    label: "Queued",
    bg: "bg-accent/10 border-accent/20",
    text: "text-accent-soft",
    dot: "bg-accent-soft",
  },
  RUNNING: {
    label: "Running",
    bg: "bg-accent/20 border-accent/50",
    text: "text-white",
    dot: "bg-accent-bright",
    pulsing: true,
  },
  PR_OPEN: {
    label: "PR open",
    bg: "bg-accent/15 border-accent/40",
    text: "text-accent-bright",
    dot: "bg-accent-bright",
  },
  MERGED: {
    label: "Merged",
    bg: "bg-emerald-500/15 border-emerald-500/30",
    text: "text-emerald-400",
    dot: "bg-emerald-400",
  },
  REJECTED: {
    label: "Rejected",
    bg: "bg-[#ff4c6a]/15 border-[#ff4c6a]/30",
    text: "text-[#ff6d85]",
    dot: "bg-[#ff4c6a]",
  },
  ESCALATED: {
    label: "Escalated",
    bg: "bg-[#ff9345]/15 border-[#ff9345]/30",
    text: "text-[#ffa86b]",
    dot: "bg-[#ff9345]",
  },
  FAILED: {
    label: "Failed",
    bg: "bg-[#ff4c6a]/15 border-[#ff4c6a]/30",
    text: "text-[#ff6d85]",
    dot: "bg-[#ff4c6a]",
  },
};

export default function StatusPill({
  status,
  size = "md",
  className = "",
}: StatusPillProps) {
  const upper = (status || "NEW").toUpperCase();
  const cfg = STATUS_CONFIG[upper] || STATUS_CONFIG.NEW;

  const pad = size === "sm" ? "px-2 py-0.5 text-[11px]" : "px-2.5 py-1 text-[12px]";

  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full border font-medium select-none ${cfg.bg} ${cfg.text} ${pad} ${className}`}
    >
      {cfg.dot && (
        <span
          className={`w-1.5 h-1.5 rounded-full shrink-0 ${cfg.dot} ${
            cfg.pulsing ? "animate-pulseRing" : ""
          }`}
        />
      )}
      <span>{cfg.label}</span>
    </span>
  );
}
