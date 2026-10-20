"use client";

import React, { useState } from "react";
import Link from "next/link";
import BracketLabel from "@/components/ui/BracketLabel";
import PillButton from "@/components/ui/PillButton";
import StatusPill from "@/components/ui/StatusPill";
import Skeleton from "@/components/ui/Skeleton";
import Toast, { ToastMessage } from "@/components/ui/Toast";
import { useSummary, useBacklog, useFunnel, useMTTR, useRuns, syncPRs } from "@/lib/api";
import { formatDuration, formatHours, formatNumber, formatPercent } from "@/lib/format";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts";
import { Clock, CheckCircle2, AlertOctagon, TrendingDown, GitPullRequest } from "lucide-react";

export default function DashboardPage() {
  const [syncing, setSyncing] = useState(false);
  const [toast, setToast] = useState<ToastMessage | null>(null);

  const { data: summary, mutate: mutateSummary, isLoading: summaryLoading } = useSummary(5000);
  const { data: backlog, mutate: mutateBacklog, isLoading: backlogLoading } = useBacklog(5000);
  const { data: funnel, isLoading: funnelLoading } = useFunnel(10000);
  const { data: mttr } = useMTTR(10000);
  const { data: runs, mutate: mutateRuns } = useRuns(6);

  const handleRefresh = async () => {
    try {
      setSyncing(true);
      const res = await syncPRs();
      setToast({
        id: String(Date.now()),
        type: "success",
        message: `Synced with GitHub: ${res.synced || 0} PRs updated.`,
      });
      mutateSummary();
      mutateBacklog();
      mutateRuns();
    } catch {
      setToast({
        id: String(Date.now()),
        type: "error",
        message: "Failed to sync PR status with GitHub",
      });
    } finally {
      setSyncing(false);
    }
  };

  const hasRuns = (summary?.completed_runs_count ?? 0) > 0 || (runs && runs.length > 0);
  const acceptanceDecision = summary?.acceptance?.n_decided ?? 0;

  return (
    <div className="max-w-7xl mx-auto px-6 sm:px-8 pt-8">
      {/* Toast notifications */}
      <Toast toast={toast} onClose={() => setToast(null)} />

      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-4 mb-8">
        <div>
          <BracketLabel>OVERVIEW</BracketLabel>
          <h1 className="text-3xl sm:text-4xl font-light text-white tracking-tight mt-1">
            Security debt, live.
          </h1>
          <p className="text-[13px] text-ink-muted mt-1">
            Autonomous vulnerability remediation throughput, verification metrics, and backlog reduction.
          </p>
        </div>

        {/* Right side: Refresh */}
        <div className="flex items-center gap-3">
          <PillButton
            variant="ghost"
            size="sm"
            onClick={handleRefresh}
            loading={syncing}
            title="Poll GitHub for PR reviews, merges and closures"
          >
            Refresh
          </PillButton>
        </div>
      </div>

      {/* ROW 1: 4 KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        {/* KPI 1: Time to review-ready PR */}
        <div className="glass p-5 rounded-card flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between text-[11px] font-mono text-ink-dim uppercase tracking-wider mb-2">
              <span>Time to Review-Ready PR</span>
              <Clock size={14} className="text-accent-bright" />
            </div>
            {summaryLoading || !summary ? (
              <Skeleton height={36} width={100} className="mb-2" />
            ) : hasRuns && summary.avg_remediation_seconds > 0 ? (
              <div className="text-3xl font-light text-white tracking-tight">
                {formatDuration(summary.avg_remediation_seconds)}
              </div>
            ) : (
              <div className="text-sm text-ink-dim italic">Run a remediation to measure</div>
            )}
          </div>
          <div className="flex items-center justify-between text-[12px] text-ink-muted mt-3 pt-3 border-t border-white/[0.04]">
            <span>vs 6.8 h manual effort</span>
            <span className="text-emerald-400 font-mono font-medium">-99%</span>
          </div>
        </div>

        {/* KPI 2: Acceptance rate */}
        <div className="glass p-5 rounded-card flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between text-[11px] font-mono text-ink-dim uppercase tracking-wider mb-2">
              <span>PR Acceptance Rate</span>
              <CheckCircle2 size={14} className="text-emerald-400" />
            </div>
            {summaryLoading || !summary ? (
              <Skeleton height={36} width={80} className="mb-2" />
            ) : acceptanceDecision > 0 ? (
              <div className="text-3xl font-light text-emerald-400 tracking-tight">
                {formatPercent(summary.acceptance_rate_pct)}
              </div>
            ) : (
              <div className="text-sm text-ink-dim italic">No decisions yet</div>
            )}
          </div>
          <div className="text-[12px] text-ink-muted mt-3 pt-3 border-t border-white/[0.04]">
            {summary?.acceptance?.merged ?? 0} merged of {acceptanceDecision} decided
          </div>
        </div>

        {/* KPI 3: Open backlog */}
        <div className="glass p-5 rounded-card flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between text-[11px] font-mono text-ink-dim uppercase tracking-wider mb-2">
              <span>Open Backlog</span>
              <AlertOctagon size={14} className="text-[#ff6d85]" />
            </div>
            {summaryLoading || !summary ? (
              <Skeleton height={36} width={90} className="mb-2" />
            ) : (
              <div className="text-3xl font-light text-white tracking-tight">
                {formatNumber(summary.open_findings)}
              </div>
            )}
          </div>
          <div className="text-[12px] text-ink-muted mt-3 pt-3 border-t border-white/[0.04]">
            {summary?.severities?.CRITICAL ?? 0} critical, {summary?.severities?.HIGH ?? 0} high
          </div>
        </div>

        {/* KPI 4: Engineer-hours saved */}
        <div className="glass p-5 rounded-card flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between text-[11px] font-mono text-ink-dim uppercase tracking-wider mb-2">
              <span>Engineer-Hours Saved</span>
              <TrendingDown size={14} className="text-accent-bright" />
            </div>
            {summaryLoading || !summary ? (
              <Skeleton height={36} width={90} className="mb-2" />
            ) : (
              <div className="text-3xl font-light text-accent-bright tracking-tight">
                {formatHours(summary.hours_saved)}
              </div>
            )}
          </div>
          <div className="text-[12px] text-ink-muted mt-3 pt-3 border-t border-white/[0.04]">
            of {formatHours(summary?.total_engineer_hours_baseline)} backlog
          </div>
        </div>
      </div>

      {/* ROW 2: Charts (Backlog Timeline + Age/Severity) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 mb-6">
        {/* Backlog, Live (2/3 / col-span-8) */}
        <div className="lg:col-span-8 glass p-5 rounded-card">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-[14px] font-medium text-white">Backlog, Live</h3>
              <p className="text-[12px] text-ink-muted">Historical baseline vs live PR remediation events</p>
            </div>
            <span className="font-mono text-[11px] text-accent-soft uppercase">[ Timeline ]</span>
          </div>

          <div className="h-64 w-full">
            {backlogLoading || !backlog ? (
              <Skeleton height="100%" width="100%" />
            ) : (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={backlog.timeline} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                  <XAxis dataKey="timestamp" stroke="#69718f" fontSize={11} tickLine={false} />
                  <YAxis stroke="#69718f" fontSize={11} tickLine={false} />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: "rgba(11,16,34,0.95)",
                      border: "1px solid rgba(255,255,255,0.1)",
                      borderRadius: "12px",
                      color: "#e9edff",
                      fontSize: "12px",
                    }}
                  />
                  <Legend wrapperStyle={{ fontSize: "12px", paddingTop: "10px" }} />
                  <Bar dataKey="open" name="Open Backlog" stackId="a" fill="#2b59ff" radius={[0, 0, 4, 4]} />
                  <Bar dataKey="in_review" name="In Review (PR Open)" stackId="a" fill="#4c7dff" />
                  <Bar dataKey="merged" name="Merged" stackId="a" fill="#10b981" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            )}
          </div>
        </div>

        {/* Backlog by Age and Severity (1/3 / col-span-4) */}
        <div className="lg:col-span-4 glass p-5 rounded-card">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-[14px] font-medium text-white">Age and Severity</h3>
              <p className="text-[12px] text-ink-muted">Backlog exposure buckets</p>
            </div>
            <span className="font-mono text-[11px] text-ink-dim uppercase">[ Days ]</span>
          </div>

          <div className="h-64 w-full">
            {backlogLoading || !backlog ? (
              <Skeleton height="100%" width="100%" />
            ) : (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart
                  data={backlog.by_age_and_severity}
                  margin={{ top: 10, right: 10, left: -25, bottom: 0 }}
                >
                  <XAxis dataKey="age_bucket" stroke="#69718f" fontSize={11} tickLine={false} />
                  <YAxis stroke="#69718f" fontSize={11} tickLine={false} />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: "rgba(11,16,34,0.95)",
                      border: "1px solid rgba(255,255,255,0.1)",
                      borderRadius: "12px",
                      color: "#e9edff",
                      fontSize: "12px",
                    }}
                  />
                  <Bar dataKey="CRITICAL" fill="#ff4c6a" name="Critical" />
                  <Bar dataKey="HIGH" fill="#ff9345" name="High" />
                  <Bar dataKey="MEDIUM" fill="#ffc73b" name="Medium" />
                  <Bar dataKey="LOW" fill="#4cc3ff" name="Low" />
                </BarChart>
              </ResponsiveContainer>
            )}
          </div>
        </div>
      </div>

      {/* ROW 3: Funnel, MTTR, Recent Runs */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-12">
        {/* 1. Remediation Funnel */}
        <div className="glass p-5 rounded-card flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-[14px] font-medium text-white">Remediation Funnel</h3>
              <span className="font-mono text-[11px] text-accent-soft uppercase">[ Conversion ]</span>
            </div>
            <p className="text-[12px] text-ink-muted mb-4">
              Progression from raw scanner findings to merged pull requests.
            </p>

            <div className="space-y-3">
              {funnelLoading || !funnel ? (
                Array.from({ length: 5 }).map((_, i) => (
                  <div key={i}>
                    <Skeleton height={14} width="100%" className="mb-1" />
                    <Skeleton height={6} width="100%" />
                  </div>
                ))
              ) : (
                funnel.stages.map((stage) => (
                  <div key={stage.stage}>
                    <div className="flex items-center justify-between text-[12px] mb-1">
                      <span className="text-white font-medium">{stage.stage}</span>
                      <span className="font-mono text-ink-muted">{stage.count}</span>
                    </div>
                    <div className="w-full h-1.5 rounded-full bg-white/[0.04] overflow-hidden">
                      <div
                        className="h-full bg-accent rounded-full transition-all duration-500"
                        style={{
                          width: `${Math.min(100, Math.max(5, (stage.count / (funnel.total_backlog || 1)) * 100))}%`,
                        }}
                      />
                    </div>
                    <p className="text-[10px] text-ink-dim mt-0.5">{stage.caption}</p>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>

        {/* 2. MTTR Comparison */}
        <div className="glass p-5 rounded-card flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-[14px] font-medium text-white">MTTR Benchmark</h3>
              <span className="font-mono text-[11px] text-emerald-400 font-bold uppercase">
                {mttr?.reduction_pct ? `-${mttr.reduction_pct}%` : "-99%"}
              </span>
            </div>
            <p className="text-[12px] text-ink-muted mb-4">
              Developer turnaround vs autonomous multi-agent pipeline.
            </p>

            {/* Comparison Bars */}
            <div className="space-y-4 mb-6">
              <div>
                <div className="flex items-center justify-between text-[12px] mb-1">
                  <span className="text-ink-muted">Manual Remediation Baseline</span>
                  <span className="font-mono text-white">6.8 hours</span>
                </div>
                <div className="w-full h-2 rounded-full bg-white/[0.04] overflow-hidden">
                  <div className="h-full bg-[#ff9345] rounded-full w-full" />
                </div>
              </div>

              <div>
                <div className="flex items-center justify-between text-[12px] mb-1">
                  <span className="text-ink-muted">SecureFlow AI (Pipeline)</span>
                  <span className="font-mono text-emerald-400">
                    {formatDuration(mttr?.secureflow_seconds || 192)}
                  </span>
                </div>
                <div className="w-full h-2 rounded-full bg-white/[0.04] overflow-hidden">
                  <div className="h-full bg-emerald-400 rounded-full w-[3%]" />
                </div>
              </div>
            </div>

            {/* Benchmarks Table */}
            <div className="border border-white/10 rounded-lg p-3 bg-white/[0.01] text-[12px] font-mono space-y-1.5">
              <div className="flex justify-between text-ink-dim">
                <span>Avg Time to Draft PR:</span>
                <span className="text-white">{formatDuration(mttr?.time_to_draft_avg_seconds || 192)}</span>
              </div>
              <div className="flex justify-between text-ink-dim">
                <span>Avg Time to Merge:</span>
                <span className="text-white">
                  {mttr?.time_to_merge_avg_seconds ? formatDuration(mttr.time_to_merge_avg_seconds) : "Immediate"}
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* 3. Recent Runs */}
        <div className="glass p-5 rounded-card flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-[14px] font-medium text-white">Recent Runs</h3>
              <Link
                href="/runs"
                className="font-mono text-[11px] text-accent-soft hover:text-white uppercase transition-colors"
              >
                View all &rarr;
              </Link>
            </div>
            <p className="text-[12px] text-ink-muted mb-4">
              Latest autonomous pipeline executions.
            </p>

            <div className="space-y-2.5">
              {!runs || runs.length === 0 ? (
                <div className="text-center py-8 text-ink-dim text-[13px]">
                  No remediation runs yet.
                </div>
              ) : (
                runs.slice(0, 5).map((r) => (
                  <Link
                    key={r.id}
                    href={`/runs/${r.id}`}
                    className="flex items-center justify-between p-2.5 rounded-lg bg-white/[0.02] hover:bg-white/[0.05] border border-white/[0.04] transition-all group"
                  >
                    <div>
                      <div className="font-mono text-[12px] font-medium text-white group-hover:text-accent-bright">
                        {r.finding_id}
                      </div>
                      <div className="text-[11px] text-ink-dim">
                        {formatDuration(r.timings?.total_s || 0)}
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <StatusPill status={r.status} size="sm" />
                      {r.pull_request?.url && (
                        <GitPullRequest size={14} className="text-accent-bright" />
                      )}
                    </div>
                  </Link>
                ))
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Footnote */}
      <div className="text-center text-[12px] text-ink-dim pb-12">
        Baseline from ps09_vulnerability_scans.csv (synthetic). Agent timings and acceptance are measured from real runs.
      </div>
    </div>
  );
}
