import React from "react";
import { Shield, Search, Wrench, CheckCircle2, GitPullRequest, XCircle } from "lucide-react";

export type NodeState = "idle" | "active" | "done" | "failed";

interface ConstellationProps {
  activeNode?: string;
  nodeStates?: Record<string, NodeState>;
  showRetry?: boolean;
  className?: string;
  interactive?: boolean;
  onNodeClick?: (agentKey: string) => void;
}

const AGENTS = [
  { key: "triage", label: "TRIAGE", icon: Shield, x: 60, y: 55 },
  { key: "analyzer", label: "ANALYZER", icon: Search, x: 195, y: 55 },
  { key: "fixer", label: "FIXER", icon: Wrench, x: 330, y: 55 },
  { key: "validator", label: "VALIDATOR", icon: CheckCircle2, x: 465, y: 55 },
  { key: "pr", label: "PR AGENT", icon: GitPullRequest, x: 600, y: 55 },
];

export default function Constellation({
  activeNode,
  nodeStates = {},
  showRetry = false,
  className = "",
  interactive = false,
  onNodeClick,
}: ConstellationProps) {
  return (
    <div className={`relative w-full overflow-hidden select-none ${className}`}>
      <svg
        viewBox="0 0 660 110"
        className="w-full h-auto drop-shadow-sm"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
      >
        {/* Connecting pipeline lines */}
        <line
          x1="60"
          y1="55"
          x2="600"
          y2="55"
          stroke="rgba(255, 255, 255, 0.22)"
          strokeWidth="1.5"
          strokeDasharray="4 4"
        />

        {/* Retry curved loop from Validator back to Fixer */}
        {showRetry && (
          <path
            d="M 465 40 C 465 10, 330 10, 330 40"
            fill="none"
            stroke="#ff9345"
            strokeWidth="1.5"
            strokeDasharray="3 3"
          />
        )}
      </svg>

      {/* HTML overlay for sharp icons, pulse rings, and labels */}
      <div className="absolute inset-0 flex items-center justify-between px-[5%] pointer-events-none">
        {AGENTS.map((agent) => {
          const state: NodeState =
            nodeStates[agent.key] ||
            (activeNode === agent.key ? "active" : "idle");
          const Icon = agent.icon;

          const isDone = state === "done";
          const isActive = state === "active";
          const isFailed = state === "failed";

          return (
            <div
              key={agent.key}
              onClick={() => interactive && onNodeClick?.(agent.key)}
              className={`flex flex-col items-center gap-2 ${
                interactive ? "pointer-events-auto cursor-pointer" : ""
              }`}
            >
              <div
                className={`relative w-10 h-10 rounded-full flex items-center justify-center transition-all duration-300 ${
                  isActive
                    ? "bg-accent text-white shadow-glow animate-pulseRing border border-accent-bright"
                    : isDone
                    ? "bg-emerald-500/20 text-emerald-400 border border-emerald-500/50"
                    : isFailed
                    ? "bg-[#ff4c6a]/20 text-[#ff6d85] border border-[#ff4c6a]/50"
                    : "bg-[#0b1022] text-ink-muted border border-white/20 hover:border-white/40"
                }`}
              >
                {isFailed ? (
                  <XCircle size={16} />
                ) : isDone ? (
                  <CheckCircle2 size={16} />
                ) : (
                  <Icon size={16} />
                )}
              </div>
              <span
                className={`font-mono text-[10px] tracking-wider uppercase ${
                  isActive
                    ? "text-accent-bright font-semibold"
                    : isDone
                    ? "text-emerald-400 font-medium"
                    : isFailed
                    ? "text-[#ff6d85] font-medium"
                    : "text-ink-dim"
                }`}
              >
                {agent.label}
              </span>
            </div>
          );
        })}
      </div>

      {showRetry && (
        <div className="absolute top-1 left-[54%] -translate-x-1/2 text-[10px] font-mono text-[#ffa86b] uppercase tracking-wider bg-[#0b1022]/80 px-1.5 py-0.5 rounded border border-[#ff9345]/30">
          Retry 1
        </div>
      )}
    </div>
  );
}
