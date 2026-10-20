"use client";

import React, { useEffect } from "react";
import { CheckCircle2, AlertCircle, Info, X } from "lucide-react";

export interface ToastMessage {
  id: string;
  type: "success" | "error" | "info";
  message: string;
}

interface ToastProps {
  toast: ToastMessage | null;
  onClose: () => void;
}

export default function Toast({ toast, onClose }: ToastProps) {
  useEffect(() => {
    if (!toast) return;
    const timer = setTimeout(() => {
      onClose();
    }, 4000);
    return () => clearTimeout(timer);
  }, [toast, onClose]);

  if (!toast) return null;

  const icons = {
    success: <CheckCircle2 className="text-emerald-400 shrink-0" size={16} />,
    error: <AlertCircle className="text-[#ff6d85] shrink-0" size={16} />,
    info: <Info className="text-accent-bright shrink-0" size={16} />,
  };

  const borders = {
    success: "border-emerald-500/30",
    error: "border-[#ff4c6a]/30",
    info: "border-accent/40",
  };

  return (
    <div
      role="status"
      aria-live="polite"
      className={`fixed bottom-24 right-8 z-50 flex items-center gap-3 px-4 py-3 rounded-card bg-[#0b1022]/90 backdrop-blur-md border ${
        borders[toast.type]
      } shadow-card text-[13px] text-ink animate-rise max-w-sm`}
    >
      {icons[toast.type]}
      <span className="flex-1 leading-snug">{toast.message}</span>
      <button
        onClick={onClose}
        className="text-ink-dim hover:text-ink p-0.5 rounded transition-colors"
        aria-label="Close notification"
      >
        <X size={14} />
      </button>
    </div>
  );
}
