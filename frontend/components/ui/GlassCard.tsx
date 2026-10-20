import React from "react";

interface GlassCardProps {
  children: React.ReactNode;
  title?: React.ReactNode;
  action?: React.ReactNode;
  dense?: boolean;
  className?: string;
  onClick?: () => void;
}

export default function GlassCard({
  children,
  title,
  action,
  dense = false,
  className = "",
  onClick,
}: GlassCardProps) {
  const pad = dense ? "p-5" : "p-6";

  return (
    <div
      onClick={onClick}
      className={`glass ${pad} transition-all duration-200 ${
        onClick ? "cursor-pointer hover:border-white/20" : ""
      } ${className}`}
    >
      {(title || action) && (
        <div className="flex items-center justify-between gap-4 mb-4">
          {title && (
            <div className="text-[14px] font-medium text-ink flex items-center gap-2">
              {title}
            </div>
          )}
          {action && <div className="flex items-center gap-2">{action}</div>}
        </div>
      )}
      {children}
    </div>
  );
}
