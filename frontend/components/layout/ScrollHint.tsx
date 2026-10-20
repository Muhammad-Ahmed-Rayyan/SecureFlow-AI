import React from "react";
import { ArrowDown } from "lucide-react";

export default function ScrollHint() {
  return (
    <div className="inline-flex items-center gap-2 text-ink-muted select-none">
      <div className="w-5 h-5 rounded-full bg-accent/20 border border-accent/40 flex items-center justify-center text-accent-bright animate-bounce">
        <ArrowDown size={12} />
      </div>
      <span className="font-mono text-[11px] tracking-wide uppercase text-ink-muted">
        Scroll to explore
      </span>
    </div>
  );
}
