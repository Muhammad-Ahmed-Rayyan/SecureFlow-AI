import React from "react";
import { AlertTriangle, Clock, Copy, FileQuestion, HelpCircle } from "lucide-react";

interface FlagIconProps {
  flag: string;
  className?: string;
}

const FLAG_CONFIG: Record<string, { icon: React.ElementType; label: string; color: string }> = {
  LANG_MISMATCH: {
    icon: FileQuestion,
    label: "Language mismatch: repository language differs from file extension",
    color: "text-[#ffa86b]",
  },
  DESC_MISMATCH: {
    icon: AlertTriangle,
    label: "Description mismatch: description keywords conflict with reported vulnerability type",
    color: "text-[#ff6d85]",
  },
  DUP_CVE: {
    icon: Copy,
    label: "Duplicate CVE: same CVE detected across multiple findings",
    color: "text-[#ffd469]",
  },
  DUP_FILE: {
    icon: Copy,
    label: "Duplicate file: multiple findings on the same line or file",
    color: "text-[#ffd469]",
  },
  MISSING_FIX_TIME: {
    icon: Clock,
    label: "Imputed baseline: remediation time was missing or zero, imputed from severity group median",
    color: "text-accent-bright",
  },
};

export default function FlagIcon({ flag, className = "" }: FlagIconProps) {
  const cfg = FLAG_CONFIG[flag] || {
    icon: HelpCircle,
    label: `Quality flag: ${flag}`,
    color: "text-ink-dim",
  };

  const Icon = cfg.icon;

  return (
    <span
      title={cfg.label}
      className={`inline-flex items-center justify-center p-1 rounded-md bg-white/[0.04] hover:bg-white/[0.08] cursor-help transition-colors ${cfg.color} ${className}`}
    >
      <Icon size={13} />
    </span>
  );
}
