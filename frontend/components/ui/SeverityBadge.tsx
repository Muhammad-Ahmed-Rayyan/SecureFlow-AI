import React from "react";
import type { Severity } from "@/lib/types";

interface SeverityBadgeProps {
  severity: Severity | string;
  size?: "md" | "sm";
  className?: string;
}

const SEVERITY_CONFIG: Record<
  string,
  { bg: string; border: string; dot: string; text: string; label: string }
> = {
  CRITICAL: {
    bg: "bg-[rgba(255,76,106,0.12)]",
    border: "border-[rgba(255,76,106,0.3)]",
    dot: "bg-[#ff4c6a]",
    text: "text-[#ff6d85]",
    label: "Critical",
  },
  HIGH: {
    bg: "bg-[rgba(255,147,69,0.12)]",
    border: "border-[rgba(255,147,69,0.3)]",
    dot: "bg-[#ff9345]",
    text: "text-[#ffa86b]",
    label: "High",
  },
  MEDIUM: {
    bg: "bg-[rgba(255,199,59,0.12)]",
    border: "border-[rgba(255,199,59,0.3)]",
    dot: "bg-[#ffc73b]",
    text: "text-[#ffd469]",
    label: "Medium",
  },
  LOW: {
    bg: "bg-[rgba(76,195,255,0.12)]",
    border: "border-[rgba(76,195,255,0.3)]",
    dot: "bg-[#4cc3ff]",
    text: "text-[#7cd5ff]",
    label: "Low",
  },
};

export default function SeverityBadge({
  severity,
  size = "md",
  className = "",
}: SeverityBadgeProps) {
  const upper = (severity || "LOW").toUpperCase();
  const cfg = SEVERITY_CONFIG[upper] || SEVERITY_CONFIG.LOW;

  const pad = size === "sm" ? "px-2 py-0.5 text-[11px]" : "px-2.5 py-1 text-[12px]";
  const dotSize = size === "sm" ? "w-1.5 h-1.5" : "w-2 h-2";

  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full border font-medium uppercase tracking-wide select-none ${cfg.bg} ${cfg.border} ${cfg.text} ${pad} ${className}`}
    >
      <span className={`rounded-full shrink-0 ${dotSize} ${cfg.dot}`} />
      <span>{cfg.label}</span>
    </span>
  );
}
