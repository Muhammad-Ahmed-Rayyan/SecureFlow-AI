import React from "react";

interface BracketLabelProps {
  children: React.ReactNode;
  className?: string;
}

export default function BracketLabel({ children, className = "" }: BracketLabelProps) {
  return (
    <span
      className={`font-mono text-[11px] font-semibold uppercase tracking-[0.14em] text-accent-soft select-none inline-flex items-center gap-1 ${className}`}
    >
      <span className="text-ink-dim">[</span>
      <span>{children}</span>
      <span className="text-ink-dim">.. ]</span>
    </span>
  );
}
