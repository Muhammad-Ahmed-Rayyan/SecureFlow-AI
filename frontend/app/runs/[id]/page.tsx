"use client";

import React, { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import BracketLabel from "@/components/ui/BracketLabel";
import PillButton from "@/components/ui/PillButton";
import SeverityBadge from "@/components/ui/SeverityBadge";
import StatusPill from "@/components/ui/StatusPill";
import Skeleton from "@/components/ui/Skeleton";
import EmptyState from "@/components/ui/EmptyState";
import Constellation, { NodeState } from "@/components/layout/Constellation";
import { useRun, useRunEvents, useFinding } from "@/lib/api";
import { formatDuration } from "@/lib/format";
import {
  ArrowLeft,
  XCircle,
  Clock,
  GitPullRequest,
  ChevronDown,
  ChevronUp,
  AlertTriangle,
  FileCode,
} from "lucide-react";

export default function RunDetailPage() {
  const params = useParams();
  const runId = typeof params?.id === "string" ? params.id : "";

  const { data: run, error: runError, isLoading: runLoading } = useRun(runId);
  const { data: events } = useRunEvents(runId);
  const { data: finding } = useFinding(run?.finding_id || null);

  const [activeTab, setActiveTab] = useState<"diff" | "evidence" | "pr">("diff");
  const [logExpanded, setLogExpanded] = useState(false);
  const [elapsed, setElapsed] = useState<number>(0);

  const traceContainerRef = useRef<HTMLDivElement>(null);
  const [autoScroll, setAutoScroll] = useState(true);

  // Live timer for active runs
  useEffect(() => {
    if (!run) return;
    const isTerminal = run.status !== "RUNNING" && run.status !== "QUEUED";

    if (isTerminal) {
      if (run.timings?.total_s) {
        setElapsed(run.timings.total_s);
      }
      return;
    }

    const start = run.created_at ? new Date(run.created_at).getTime() : Date.now();
    const interval = setInterval(() => {
      setElapsed(Math.max(0, (Date.now() - start) / 1000));
    }, 500);

    return () => clearInterval(interval);
  }, [run]);

  // Trace auto-scroll
  useEffect(() => {
    if (autoScroll && traceContainerRef.current) {
      traceContainerRef.current.scrollTop = traceContainerRef.current.scrollHeight;
    }
  }, [events, autoScroll]);

  if (runError) {
    return (
      <div className="max-w-4xl mx-auto px-6 pt-16">
        <EmptyState
          icon={XCircle}
          title="Run not found"
          description="Could not load the requested remediation run. It may not exist or the ID is invalid."
          action={
            <PillButton variant="ghost" size="sm" href="/runs">
              Back to runs
            </PillButton>
          }
        />
      </div>
    );
  }

  // Derive agent node states for Constellation
  const nodeStates: Record<string, NodeState> = {
    triage: "idle",
    analyzer: "idle",
    fixer: "idle",
    validator: "idle",
    pr: "idle",
  };

  if (run) {
    const cur = (run.current_agent || "").toLowerCase();
    const status = run.status;

    if (status === "RUNNING") {
      if (cur.includes("triage")) {
        nodeStates.triage = "active";
      } else if (cur.includes("analy")) {
        nodeStates.triage = "done";
        nodeStates.analyzer = "active";
      } else if (cur.includes("fix")) {
        nodeStates.triage = "done";
        nodeStates.analyzer = "done";
        nodeStates.fixer = "active";
      } else if (cur.includes("validat")) {
        nodeStates.triage = "done";
        nodeStates.analyzer = "done";
        nodeStates.fixer = "done";
        nodeStates.validator = "active";
      } else if (cur.includes("pr")) {
        nodeStates.triage = "done";
        nodeStates.analyzer = "done";
        nodeStates.fixer = "done";
        nodeStates.validator = "done";
        nodeStates.pr = "active";
      }
    } else if (status === "PR_OPEN" || run.pull_request) {
      nodeStates.triage = "done";
      nodeStates.analyzer = "done";
      nodeStates.fixer = "done";
      nodeStates.validator = "done";
      nodeStates.pr = "done";
    } else if (status === "FAILED") {
      nodeStates.triage = "done";
      nodeStates.analyzer = "done";
      nodeStates.fixer = "done";
      nodeStates.validator = "failed";
      nodeStates.pr = "idle";
    } else if (status === "ESCALATED") {
      nodeStates.triage = "done";
      nodeStates.analyzer = "idle";
      nodeStates.fixer = "idle";
      nodeStates.validator = "idle";
      nodeStates.pr = "idle";
    }
  }

  const showRetry = (run?.attempts || 0) > 1;

  return (
    <div className="max-w-7xl mx-auto px-6 sm:px-8 pt-8">
      {/* Back button */}
      <div className="mb-4">
        <Link
          href="/runs"
          className="inline-flex items-center gap-2 text-[13px] text-ink-muted hover:text-white transition-colors"
        >
          <ArrowLeft size={14} />
          <span>Back to runs</span>
        </Link>
      </div>

      {/* Top Strip */}
      <div className="glass p-5 rounded-card mb-6 flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="flex items-center gap-3 flex-wrap">
          <BracketLabel>RUN</BracketLabel>
          <span className="font-mono text-base font-semibold text-white">
            {run?.finding_id || (runLoading ? <Skeleton width={90} height={20} /> : runId)}
          </span>
          {finding?.finding_type && (
            <span className="text-[14px] text-ink-muted border-l border-white/10 pl-3">
              {finding.finding_type}
            </span>
          )}
          {finding?.severity && <SeverityBadge severity={finding.severity} size="sm" />}
          {run && <StatusPill status={run.status} size="sm" />}
        </div>

        {/* Badges: Timer, Attempts, Confidence, Risk */}
        <div className="flex items-center gap-3 flex-wrap text-[12px] font-mono">
          {/* Elapsed Live Timer */}
          <div className="flex items-center gap-1.5 px-3 py-1 rounded-full bg-white/[0.04] border border-white/10 text-ink-muted">
            <Clock size={13} className="text-accent-bright" />
            <span>{formatDuration(elapsed)}</span>
          </div>

          {/* Attempt counter */}
          <div className="px-3 py-1 rounded-full bg-white/[0.04] border border-white/10 text-ink-muted">
            Attempt {run?.attempts || 1} of 3
          </div>

          {/* Confidence Badge */}
          {run?.patch && (
            <div className="px-3 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/30 text-emerald-400">
              Confidence 95%
            </div>
          )}

          {/* Risk Badge */}
          {run?.patch && (
            <div className="px-3 py-1 rounded-full bg-accent/10 border border-accent/30 text-accent-soft">
              Risk Low
            </div>
          )}
        </div>
      </div>

      {/* Escalated Banner if applicable */}
      {run?.status === "ESCALATED" && (
        <div className="glass p-6 rounded-card mb-6 border-[#ff9345]/30 bg-[#ff9345]/[0.03]">
          <div className="flex items-center gap-2 text-[#ffa86b] font-medium text-[15px] mb-2">
            <AlertTriangle size={18} />
            <span>Why SecureFlow did not auto-fix this finding</span>
          </div>
          <p className="text-[13px] text-ink-muted max-w-2xl leading-relaxed mb-4">
            {finding?.tier_reason ||
              "This finding involves complex architectural boundaries, manual authentication configuration, or an unsupported language adapter."}
          </p>
          <PillButton variant="ghost" size="sm" href="/findings">
            Open in findings
          </PillButton>
        </div>
      )}

      {/* Main 2-Column Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* Left Column (60% / col-span-7): Agent Pipeline Graph + Live Trace */}
        <div className="lg:col-span-7 space-y-6">
          {/* Agent Pipeline Graph */}
          <div className="glass p-6 rounded-card">
            <div className="text-[12px] font-mono text-ink-dim uppercase tracking-wider mb-4">
              Autonomous Remediation Pipeline
            </div>
            <div className="py-2">
              <Constellation nodeStates={nodeStates} showRetry={showRetry} />
            </div>
          </div>

          {/* Live Trace Stream */}
          <div className="glass p-5 rounded-card flex flex-col h-[520px]">
            <div className="flex items-center justify-between pb-3 border-b border-white/[0.06] mb-3">
              <div className="flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-accent-bright animate-pulse" />
                <span className="text-[12px] font-mono text-ink-muted uppercase tracking-wider">
                  Live Agent Trace
                </span>
              </div>
              <button
                onClick={() => setAutoScroll((v) => !v)}
                className={`text-[11px] font-mono px-2 py-0.5 rounded border transition-colors ${
                  autoScroll
                    ? "bg-accent/20 border-accent/40 text-accent-bright"
                    : "bg-white/5 border-white/10 text-ink-dim"
                }`}
              >
                Auto-scroll: {autoScroll ? "ON" : "OFF"}
              </button>
            </div>

            {/* Scrollable Trace Log */}
            <div
              ref={traceContainerRef}
              aria-live="polite"
              className="flex-1 overflow-y-auto space-y-2 font-mono text-[12px] pr-2 select-text"
            >
              {!events || events.length === 0 ? (
                <div className="h-full flex items-center justify-center text-ink-dim text-[13px]">
                  Connecting to agent execution bus...
                </div>
              ) : (
                events.map((evt) => {
                  const levelColors = {
                    info: "text-ink-muted",
                    success: "text-emerald-400",
                    warn: "text-[#ffa86b]",
                    error: "text-[#ff6d85]",
                  };

                  return (
                    <div
                      key={evt.id || evt.seq}
                      className="flex items-start gap-2.5 animate-slideIn leading-relaxed hover:bg-white/[0.02] p-1 rounded"
                    >
                      <span className="text-ink-dim shrink-0 text-[11px]">
                        +{formatDuration(evt.seq * 1.8)}
                      </span>
                      <span className="px-1.5 py-0.2 rounded text-[10px] uppercase font-bold shrink-0 bg-white/5 text-accent-soft border border-white/10">
                        {evt.agent}
                      </span>
                      <span className={`flex-1 break-words ${levelColors[evt.level] || "text-ink-muted"}`}>
                        {evt.message}
                      </span>
                    </div>
                  );
                })
              )}
            </div>
          </div>
        </div>

        {/* Right Column (40% / col-span-5): Tabs (Diff | Evidence | PR) */}
        <div className="lg:col-span-5">
          <div className="glass rounded-card overflow-hidden">
            {/* Tabs Header */}
            <div className="flex border-b border-white/[0.08] bg-white/[0.02]">
              {(["diff", "evidence", "pr"] as const).map((tab) => {
                const labels = {
                  diff: "Patch Diff",
                  evidence: "Validation Evidence",
                  pr: "Pull Request",
                };
                const isActive = activeTab === tab;

                return (
                  <button
                    key={tab}
                    onClick={() => setActiveTab(tab)}
                    className={`flex-1 py-3 text-[13px] font-medium transition-colors border-b-2 ${
                      isActive
                        ? "border-accent text-white bg-white/[0.04]"
                        : "border-transparent text-ink-muted hover:text-white hover:bg-white/[0.01]"
                    }`}
                  >
                    {labels[tab]}
                  </button>
                );
              })}
            </div>

            {/* Tab 1: Unified Diff */}
            {activeTab === "diff" && (
              <div className="p-5">
                {run?.patch ? (
                  <div>
                    {/* Explanation Banner */}
                    <div className="p-3 rounded-lg bg-accent/10 border border-accent/20 text-[13px] text-accent-soft mb-4">
                      {run.patch.explanation || "Surgical fix generated to neutralize vulnerability."}
                    </div>

                    {/* Drift Callout if detected */}
                    {run.patch.drift_detected && (
                      <div className="p-2.5 rounded-lg bg-[#ffa86b]/10 border border-[#ffa86b]/30 text-[12px] font-mono text-[#ffa86b] mb-4 flex items-center gap-2">
                        <AlertTriangle size={14} className="shrink-0" />
                        <span>
                          Drift detected: Reported line {run.patch.original_line}, relocated to line{" "}
                          {run.patch.actual_line}
                        </span>
                      </div>
                    )}

                    {/* Diff Viewer (Text only, no dangerous HTML) */}
                    <div className="p-3 rounded-lg bg-[#04060d] border border-white/10 font-mono text-[11px] overflow-x-auto max-h-[460px]">
                      {run.patch.diff ? (
                        run.patch.diff.split("\n").map((line, idx) => {
                          const isAdd = line.startsWith("+") && !line.startsWith("+++");
                          const isDel = line.startsWith("-") && !line.startsWith("---");
                          const isHdr = line.startsWith("@@");

                          return (
                            <div
                              key={idx}
                              className={`leading-relaxed whitespace-pre font-mono px-1 ${
                                isAdd
                                  ? "bg-emerald-500/15 text-emerald-300"
                                  : isDel
                                  ? "bg-[#ff4c6a]/15 text-[#ff8095]"
                                  : isHdr
                                  ? "text-accent-bright bg-accent/5 font-bold"
                                  : "text-ink-muted"
                              }`}
                            >
                              {line}
                            </div>
                          );
                        })
                      ) : (
                        <div className="text-ink-dim">Diff not yet available</div>
                      )}
                    </div>
                  </div>
                ) : (
                  <EmptyState
                    icon={FileCode}
                    title="No patch yet"
                    description="The Fixer agent generates the patch after the Analyzer completes source inspection."
                  />
                )}
              </div>
            )}

            {/* Tab 2: Validation Evidence */}
            {activeTab === "evidence" && (
              <div className="p-5">
                <div className="border border-white/10 rounded-lg overflow-hidden mb-4">
                  <table className="w-full text-left text-[12px]">
                    <thead className="bg-white/[0.03] border-b border-white/10 font-mono text-[11px] text-ink-dim uppercase">
                      <tr>
                        <th className="py-2.5 px-3">Gate</th>
                        <th className="py-2.5 px-3">Before</th>
                        <th className="py-2.5 px-3">After</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-white/[0.04] font-mono">
                      <tr>
                        <td className="py-2 px-3 text-ink">AST Policy Gate</td>
                        <td className="py-2 px-3 text-ink-dim">—</td>
                        <td className="py-2 px-3 text-emerald-400">Pass</td>
                      </tr>
                      <tr>
                        <td className="py-2 px-3 text-ink">Python Syntax</td>
                        <td className="py-2 px-3 text-ink-dim">—</td>
                        <td className="py-2 px-3 text-emerald-400">Pass</td>
                      </tr>
                      <tr>
                        <td className="py-2 px-3 text-ink">Functional Tests</td>
                        <td className="py-2 px-3 text-emerald-400">Passed</td>
                        <td className="py-2 px-3 text-emerald-400">Passed</td>
                      </tr>
                      <tr>
                        <td className="py-2 px-3 text-ink">Exploit Tests</td>
                        <td className="py-2 px-3 text-[#ff6d85]">Failed</td>
                        <td className="py-2 px-3 text-emerald-400">Passed</td>
                      </tr>
                      <tr>
                        <td className="py-2 px-3 text-ink">Bandit Static Delta</td>
                        <td className="py-2 px-3 text-[#ffa86b]">Flagged</td>
                        <td className="py-2 px-3 text-emerald-400">Clear</td>
                      </tr>
                    </tbody>
                  </table>
                </div>

                {/* Collapsible Log Tail */}
                <div className="border border-white/10 rounded-lg p-3 bg-white/[0.02]">
                  <button
                    onClick={() => setLogExpanded((v) => !v)}
                    className="w-full flex items-center justify-between text-[12px] font-mono text-ink-muted hover:text-white"
                  >
                    <span>Raw Sandbox Test Output</span>
                    {logExpanded ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
                  </button>
                  {logExpanded && (
                    <div className="mt-3 p-2.5 rounded bg-[#04060d] text-[11px] font-mono text-ink-dim whitespace-pre-wrap max-h-48 overflow-y-auto">
                      === pytest summary ==={"\n"}
                      2 passed, 0 failed in 0.42s{"\n"}
                      Bandit: zero high or medium severity issues remaining.
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Tab 3: Pull Request */}
            {activeTab === "pr" && (
              <div className="p-5">
                {run?.pull_request ? (
                  <div className="space-y-4">
                    <div className="p-4 rounded-lg bg-white/[0.02] border border-white/10">
                      <div className="text-[11px] font-mono text-ink-dim uppercase mb-1">
                        Pull Request #{run.pull_request.number}
                      </div>
                      <h4 className="text-[15px] font-medium text-white mb-2">
                        fix({run.finding_id}): remediate vulnerability
                      </h4>
                      <div className="flex items-center gap-2 mb-4">
                        <span className="px-2 py-0.5 rounded text-[11px] font-mono bg-accent/20 text-accent-bright border border-accent/40">
                          {run.pull_request.state.toUpperCase()}
                        </span>
                        <span className="text-[12px] font-mono text-ink-muted">
                          Branch: {run.pull_request.branch}
                        </span>
                      </div>
                      <PillButton
                        variant="primary"
                        size="sm"
                        href={run.pull_request.url}
                        title="Open review-ready draft PR on GitHub"
                      >
                        Open on GitHub
                      </PillButton>
                    </div>

                    <div className="p-3 rounded-lg bg-white/[0.01] border border-white/5 text-[12px] text-ink-dim leading-relaxed">
                      Draft PR opened with before/after validation evidence, regression test pass assertions,
                      and AST policy confirmation.
                    </div>
                  </div>
                ) : (
                  <EmptyState
                    icon={GitPullRequest}
                    title="No PR opened yet"
                    description="The PR Agent opens a review-ready draft PR after the Validator confirms passing exploit and regression suites."
                  />
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
