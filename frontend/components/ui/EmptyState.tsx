import React from "react";
import { Inbox } from "lucide-react";

interface EmptyStateProps {
  icon?: React.ElementType;
  title: string;
  description?: string;
  action?: React.ReactNode;
  className?: string;
}

export default function EmptyState({
  icon: Icon = Inbox,
  title,
  description,
  action,
  className = "",
}: EmptyStateProps) {
  return (
    <div
      className={`flex flex-col items-center justify-center p-12 text-center rounded-card border border-dashed border-white/10 bg-white/[0.02] ${className}`}
    >
      <div className="w-12 h-12 rounded-full bg-white/[0.04] flex items-center justify-center text-ink-dim mb-4">
        <Icon size={22} />
      </div>
      <h3 className="text-[15px] font-medium text-ink mb-1">{title}</h3>
      {description && (
        <p className="text-[13px] text-ink-muted max-w-sm mb-6 leading-relaxed">
          {description}
        </p>
      )}
      {action && <div>{action}</div>}
    </div>
  );
}
