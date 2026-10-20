"use client";

import React from "react";
import Link from "next/link";
import ArrowOrb from "./ArrowOrb";

interface PillButtonProps {
  children: React.ReactNode;
  variant?: "primary" | "ghost";
  size?: "md" | "sm";
  href?: string;
  onClick?: (e: React.MouseEvent) => void;
  loading?: boolean;
  disabled?: boolean;
  icon?: "arrow" | "none";
  title?: string;
  className?: string;
  type?: "button" | "submit" | "reset";
}

export default function PillButton({
  children,
  variant = "primary",
  size = "md",
  href,
  onClick,
  loading = false,
  disabled = false,
  icon = "arrow",
  title,
  className = "",
  type = "button",
}: PillButtonProps) {
  const isSm = size === "sm";
  const heightClass = isSm ? "h-9 pl-4 pr-1.5 text-[13px]" : "h-11 pl-5 pr-2 text-[14px]";

  const baseStyle =
    "group inline-flex items-center justify-between font-medium rounded-pill transition-all duration-200 select-none outline-none focus-visible:ring-2 focus-visible:ring-accent-bright";

  const variantStyle =
    variant === "primary"
      ? "bg-white text-[#06080F] hover:bg-white/95 hover:shadow-glow active:scale-[0.98]"
      : "bg-white/[0.04] text-ink hover:bg-white/[0.08] border border-white/10 hover:border-white/20 active:scale-[0.98]";

  const disabledStyle = disabled || loading ? "opacity-40 cursor-not-allowed pointer-events-none" : "cursor-pointer";

  const content = (
    <>
      <span className="mr-3 whitespace-nowrap">{children}</span>
      {icon === "arrow" && (
        <ArrowOrb size={size} loading={loading} disabled={disabled} glow={variant === "primary"} />
      )}
    </>
  );

  if (href && !disabled) {
    return (
      <Link
        href={href}
        className={`${baseStyle} ${variantStyle} ${heightClass} ${disabledStyle} ${className}`}
        title={title}
      >
        {content}
      </Link>
    );
  }

  return (
    <button
      type={type}
      onClick={onClick}
      disabled={disabled || loading}
      className={`${baseStyle} ${variantStyle} ${heightClass} ${disabledStyle} ${className}`}
      title={title}
    >
      {content}
    </button>
  );
}
