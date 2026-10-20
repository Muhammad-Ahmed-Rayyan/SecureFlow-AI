"use client";

import React from "react";
import Link from "next/link";
import BracketLabel from "@/components/ui/BracketLabel";
import PillButton from "@/components/ui/PillButton";
import StatusPill from "@/components/ui/StatusPill";
import Skeleton from "@/components/ui/Skeleton";
import EmptyState from "@/components/ui/EmptyState";
import { useRuns } from "@/lib/api";
import { formatDuration, formatRelativeTime } from "@/lib/format";
import { PlayCircle, GitPullRequest, ExternalLink } from "lucide-react";

export default function RunsListPage() {
  const { data: runs, isLoading } = useRuns(50);

  return (
    <div className="max-w-7xl mx-auto px-6 sm:px-8 pt-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-4 mb-8">
        <div>
          <BracketLabel>ACTIVITY</BracketLabel>
          <h1 className="text-3xl sm:text-4xl font-light text-white tracking-tight mt-1">
            Runs
          </h1>
          <p className="text-[13px] text-ink-muted mt-1">
            Historical autonomous remediation executions and agent trace sessions.
          </p>
        </div>

        <div>
          <PillButton variant="primary" size="sm" href="/findings">
            Remediate a finding
          </PillButton>
        </div>
      </div>

      {/* Runs Table */}
      <div className="glass rounded-card overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="border-b border-white/[0.08] bg-white/[0.02] text-[11px] font-mono uppercase tracking-wider text-ink-dim">
                <th className="py-3 px-4">Run ID</th>
                <th className="py-3 px-4">Finding</th>
                <th className="py-3 px-4">Status</th>
                <th className="py-3 px-4">Attempts</th>
                <th className="py-3 px-4">Duration</th>
                <th className="py-3 px-4">Pull Request</th>
                <th className="py-3 px-4">Started</th>
                <th className="py-3 px-4 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/[0.04] text-[13px]">
              {isLoading ? (
                Array.from({ length: 6 }).map((_, i) => (
                  <tr key={i}>
                    <td className="py-3 px-4"><Skeleton height={18} width={100} /></td>
                    <td className="py-3 px-4"><Skeleton height={18} width={90} /></td>
                    <td className="py-3 px-4"><Skeleton height={20} width={75} /></td>
                    <td className="py-3 px-4"><Skeleton height={18} width={40} /></td>
                    <td className="py-3 px-4"><Skeleton height={18} width={60} /></td>
                    <td className="py-3 px-4"><Skeleton height={18} width={80} /></td>
                    <td className="py-3 px-4"><Skeleton height={18} width={70} /></td>
                    <td className="py-3 px-4 text-right"><Skeleton height={28} width={70} className="ml-auto" /></td>
                  </tr>
                ))
              ) : !runs || runs.length === 0 ? (
                <tr>
                  <td colSpan={8} className="py-12">
                    <EmptyState
                      icon={PlayCircle}
                      title="No runs yet"
                      description="Remediate a vulnerability from the backlog to see the 5-agent pipeline in action."
                      action={
                        <PillButton variant="primary" size="sm" href="/findings">
                          View findings
                        </PillButton>
                      }
                    />
                  </td>
                </tr>
              ) : (
                runs.map((r) => (
                  <tr
                    key={r.id}
                    className="hover:bg-white/[0.02] transition-colors group cursor-pointer"
                  >
                    {/* Run ID */}
                    <td className="py-3.5 px-4 font-mono text-[12px] text-ink-muted">
                      <Link href={`/runs/${r.id}`} className="hover:text-accent-bright">
                        {r.id.slice(0, 12)}
                      </Link>
                    </td>

                    {/* Finding ID */}
                    <td className="py-3.5 px-4 font-mono text-[12px] text-white font-medium">
                      <Link href={`/runs/${r.id}`} className="hover:text-accent-bright">
                        {r.finding_id}
                      </Link>
                    </td>

                    {/* Status Pill */}
                    <td className="py-3.5 px-4">
                      <StatusPill status={r.status} size="sm" />
                    </td>

                    {/* Attempts */}
                    <td className="py-3.5 px-4 font-mono text-[12px] text-ink-dim">
                      {r.attempts} / 3
                    </td>

                    {/* Duration */}
                    <td className="py-3.5 px-4 font-mono text-[12px] text-ink-muted">
                      {formatDuration(r.timings?.total_s || 0)}
                    </td>

                    {/* PR Info */}
                    <td className="py-3.5 px-4">
                      {r.pull_request?.url ? (
                        <a
                          href={r.pull_request.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="inline-flex items-center gap-1.5 text-accent-bright hover:underline text-[12px] font-mono"
                          onClick={(e) => e.stopPropagation()}
                        >
                          <GitPullRequest size={13} />
                          <span>#{r.pull_request.number}</span>
                          <ExternalLink size={11} />
                        </a>
                      ) : (
                        <span className="text-[12px] text-ink-dim font-mono">—</span>
                      )}
                    </td>

                    {/* Started */}
                    <td className="py-3.5 px-4 text-ink-dim text-[12px]">
                      {formatRelativeTime(r.created_at)}
                    </td>

                    {/* Action */}
                    <td className="py-3.5 px-4 text-right">
                      <PillButton variant="ghost" size="sm" href={`/runs/${r.id}`}>
                        View trace
                      </PillButton>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
