import React from "react";
import { ArrowUpRight, Loader2 } from "lucide-react";

interface ArrowOrbProps {
  size?: "md" | "sm";
  loading?: boolean;
  disabled?: boolean;
  glow?: boolean;
  className?: string;
}

export default function ArrowOrb({
  size = "md",
  loading = false,
  disabled = false,
  glow = false,
  className = "",
}: ArrowOrbProps) {
  const dimClass = size === "sm" ? "w-7 h-7" : "w-9 h-9";
  const iconSize = size === "sm" ? 14 : 16;

  return (
    <div
      className={`inline-flex items-center justify-center rounded-full transition-transform duration-200 ${
        disabled
          ? "bg-ink-dim/30 text-ink-dim cursor-not-allowed"
          : "bg-accent text-white group-hover:scale-105"
      } ${dimClass} ${glow && !disabled ? "shadow-glow" : ""} ${className}`}
    >
      {loading ? (
        <Loader2 className="animate-spin text-white" size={iconSize} />
      ) : (
        <ArrowUpRight
          className="transition-transform duration-200 group-hover:translate-x-0.5 group-hover:-translate-y-0.5"
          size={iconSize}
        />
      )}
    </div>
  );
}
