"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";
import BracketLabel from "@/components/ui/BracketLabel";
import PillButton from "@/components/ui/PillButton";
import SeverityBadge from "@/components/ui/SeverityBadge";
import TierChip from "@/components/ui/TierChip";
import StatusPill from "@/components/ui/StatusPill";
import Skeleton from "@/components/ui/Skeleton";
import EmptyState from "@/components/ui/EmptyState";
import Toast, { ToastMessage } from "@/components/ui/Toast";
import { useFindings, useSummary, startRemediation, batchRemediate, scanRepo } from "@/lib/api";
import { formatNumber } from "@/lib/format";
import type { Finding } from "@/lib/types";
import { Search, ChevronLeft, ChevronRight, ShieldAlert } from "lucide-react";

export default function FindingsPage() {
  const router = useRouter();
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [selectedSeverity, setSelectedSeverity] = useState<string>("");
  const [fixReadyOnly, setFixReadyOnly] = useState<boolean>(false);
  const [loadingAction, setLoadingAction] = useState<string | null>(null);
  const [toast, setToast] = useState<ToastMessage | null>(null);

  const { mutate: mutateSummary } = useSummary();
  const { data: findingsData, isLoading, mutate: mutateFindings } = useFindings({
    page,
    page_size: 25,
    severity: selectedSeverity || undefined,
    fix_ready_only: fixReadyOnly ? true : undefined,
    search: search.trim() || undefined,
  });

  const findings = findingsData?.items || [];
  const totalItems = findingsData?.total ?? 0;
  const totalPages = findingsData?.pages || Math.max(1, Math.ceil(totalItems / 25));

  const fixReadyCriticalCount = findings.filter(
    (f) => (f.is_fix_ready || f.tier === "AUTO_FIX") && f.severity === "CRITICAL"
  ).length;

  const handleRemediateSingle = async (finding: Finding) => {
    try {
      setLoadingAction(finding.id);
      const res = await startRemediation(finding.id);
      setToast({
        id: String(Date.now()),
        type: "success",
        message: `Remediation started for ${finding.id}`,
      });
      router.push(`/runs/${res.run_id}`);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to trigger remediation";
      setToast({ id: String(Date.now()), type: "error", message: msg });
    } finally {
      setLoadingAction(null);
    }
  };

  const handleBatchRemediate = async () => {
    try {
      setLoadingAction("batch");
      const res = await batchRemediate(3, "CRITICAL");
      setToast({
        id: String(Date.now()),
        type: "success",
        message: `Triggered remediation for ${res.count} critical findings.`,
      });
      mutateFindings();
      mutateSummary();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Batch remediation failed";
      setToast({ id: String(Date.now()), type: "error", message: msg });
    } finally {
      setLoadingAction(null);
    }
  };

  const handleScanRepo = async () => {
    try {
      setLoadingAction("scan");
      setToast({ id: String(Date.now()), type: "info", message: "Scanning target repository with Bandit..." });
      const res = await scanRepo();
      setToast({
        id: String(Date.now()),
        type: "success",
        message: res.message || `Scan completed: ${res.findings_found} findings.`,
      });
      mutateFindings();
      mutateSummary();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Repository scan failed";
      setToast({ id: String(Date.now()), type: "error", message: msg });
    } finally {
      setLoadingAction(null);
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-6 sm:px-8 pt-8">
      {/* Toast notifications */}
      <Toast toast={toast} onClose={() => setToast(null)} />

      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-6 mb-8">
        <div>
          <BracketLabel>BACKLOG</BracketLabel>
          <h1 className="text-3xl sm:text-4xl font-light text-white tracking-tight mt-1">
            Findings
          </h1>
          <p className="text-[13px] text-ink-muted mt-1">
            Triaged security vulnerabilities with autonomous fix eligibility and severity scoring.
          </p>
        </div>

        {/* Action Pills */}
        <div className="flex items-center gap-3 flex-wrap">
          <PillButton
            variant="ghost"
            size="sm"
            onClick={handleScanRepo}
            loading={loadingAction === "scan"}
            title="Run Bandit static scan on target repository in a sandboxed runner"
          >
            Scan repo now
          </PillButton>

          <PillButton
            variant="primary"
            size="sm"
            onClick={handleBatchRemediate}
            loading={loadingAction === "batch"}
            disabled={fixReadyCriticalCount === 0}
            title={
              fixReadyCriticalCount > 0
                ? "Autonomous remediation of top 3 critical fix-ready vulnerabilities"
                : "No fix-ready critical findings available in backlog"
            }
          >
            Remediate top 3 criticals
          </PillButton>
        </div>
      </div>

      {/* Filter Bar (Glass Strip) */}
      <div className="glass p-3.5 rounded-card mb-6 flex flex-col md:flex-row items-stretch md:items-center justify-between gap-4">
        {/* Left: Search input */}
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 text-ink-dim" size={15} />
          <input
            type="text"
            value={search}
            onChange={(e) => {
              setSearch(e.target.value);
              setPage(1);
            }}
            placeholder="Search by ID, CVE, rule or file path..."
            className="w-full h-9 pl-9 pr-4 rounded-full bg-white/[0.04] border border-white/10 text-[13px] text-ink placeholder:text-ink-dim focus:outline-none focus:border-accent-bright transition-colors"
          />
        </div>

        {/* Middle: Severity Chips */}
        <div className="flex items-center gap-1.5 flex-wrap">
          {(["", "CRITICAL", "HIGH", "MEDIUM", "LOW"] as const).map((sev) => (
            <button
              key={sev || "ALL"}
              onClick={() => {
                setSelectedSeverity(sev);
                setPage(1);
              }}
              className={`px-3 py-1 rounded-full text-[12px] font-medium transition-all ${
                selectedSeverity === sev
                  ? "bg-accent text-white"
                  : "bg-white/[0.03] text-ink-muted hover:text-white hover:bg-white/[0.07]"
              }`}
            >
              {sev || "All"}
            </button>
          ))}
        </div>

        {/* Right: Fix-Ready Only Toggle */}
        <div className="flex items-center gap-2 select-none border-l border-white/10 pl-4">
          <label className="text-[13px] text-ink-muted flex items-center gap-2 cursor-pointer">
            <input
              type="checkbox"
              checked={fixReadyOnly}
              onChange={(e) => {
                setFixReadyOnly(e.target.checked);
                setPage(1);
              }}
              className="rounded accent-accent h-4 w-4 cursor-pointer"
            />
            <span className={fixReadyOnly ? "text-accent-bright font-medium" : ""}>
              Fix-ready only
            </span>
          </label>
        </div>
      </div>

      {/* Results count info */}
      <div className="flex items-center justify-between text-[12px] text-ink-dim mb-3 px-1">
        <span>
          Showing {findings.length > 0 ? (page - 1) * 25 + 1 : 0}–
          {Math.min(page * 25, totalItems)} of {formatNumber(totalItems)} findings
        </span>
        {fixReadyOnly && (
          <span className="text-accent-soft font-mono">
            [ Filtered: Fix-Ready (Demo Target Source Match) ]
          </span>
        )}
      </div>

      {/* Table Container */}
      <div className="glass rounded-card overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="border-b border-white/[0.08] bg-white/[0.02] text-[11px] font-mono uppercase tracking-wider text-ink-dim">
                <th className="py-3 px-4">Severity</th>
                <th className="py-3 px-4">ID</th>
                <th className="py-3 px-4">Type</th>
                <th className="py-3 px-4">Repository</th>
                <th className="py-3 px-4">File</th>
                <th className="py-3 px-4">Age</th>
                <th className="py-3 px-4">Tier</th>
                <th className="py-3 px-4">Status</th>
                <th className="py-3 px-4 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/[0.04] text-[13px]">
              {isLoading ? (
                Array.from({ length: 10 }).map((_, i) => (
                  <tr key={i}>
                    <td className="py-3 px-4"><Skeleton height={22} width={75} /></td>
                    <td className="py-3 px-4"><Skeleton height={18} width={85} /></td>
                    <td className="py-3 px-4"><Skeleton height={18} width={130} /></td>
                    <td className="py-3 px-4"><Skeleton height={18} width={110} /></td>
                    <td className="py-3 px-4"><Skeleton height={18} width={150} /></td>
                    <td className="py-3 px-4"><Skeleton height={18} width={45} /></td>
                    <td className="py-3 px-4"><Skeleton height={20} width={80} /></td>
                    <td className="py-3 px-4"><Skeleton height={20} width={65} /></td>
                    <td className="py-3 px-4 text-right"><Skeleton height={32} width={90} className="ml-auto" /></td>
                  </tr>
                ))
              ) : findings.length === 0 ? (
                <tr>
                  <td colSpan={9} className="py-12">
                    <EmptyState
                      icon={ShieldAlert}
                      title="No findings found"
                      description="No vulnerability findings match your current search and filter criteria."
                      action={
                        <PillButton
                          variant="ghost"
                          size="sm"
                          onClick={() => {
                            setSearch("");
                            setSelectedSeverity("");
                            setFixReadyOnly(false);
                            setPage(1);
                          }}
                        >
                          Clear all filters
                        </PillButton>
                      }
                    />
                  </td>
                </tr>
              ) : (
                findings.map((f) => {
                  const isFixReady = f.is_fix_ready || f.tier === "AUTO_FIX";
                  const isAgeOver90 = (f.remediation_time_minutes || 0) > 90 || false; // Or days_open

                  // Shorten file path
                  const pathParts = (f.file_path || "").split("/");
                  const shortFile =
                    pathParts.length > 2
                      ? `.../${pathParts.slice(-2).join("/")}`
                      : f.file_path;

                  return (
                    <tr
                      key={f.id}
                      className="hover:bg-white/[0.02] transition-colors group"
                    >
                      {/* Severity */}
                      <td className="py-3.5 px-4 whitespace-nowrap">
                        <SeverityBadge severity={f.severity} size="sm" />
                      </td>

                      {/* ID */}
                      <td className="py-3.5 px-4 font-mono text-[12px] text-white font-medium whitespace-nowrap">
                        {f.id}
                      </td>

                      {/* Type */}
                      <td className="py-3.5 px-4 text-ink font-medium max-w-[180px] truncate">
                        {f.finding_type || "Vulnerability"}
                      </td>

                      {/* Repository */}
                      <td className="py-3.5 px-4 text-ink-muted max-w-[140px] truncate">
                        {f.repository}
                      </td>

                      {/* File */}
                      <td
                        className="py-3.5 px-4 font-mono text-[11px] text-ink-muted max-w-[200px] truncate"
                        title={`${f.file_path}:${f.line_number}`}
                      >
                        {shortFile}
                        <span className="text-ink-dim">:{f.line_number}</span>
                      </td>

                      {/* Age */}
                      <td className="py-3.5 px-4 font-mono text-[12px] whitespace-nowrap">
                        <span className={isAgeOver90 ? "text-[#ffa86b]" : "text-ink-muted"}>
                          {Math.round((f.remediation_time_minutes || 30) / 10)}d
                        </span>
                      </td>

                      {/* Tier */}
                      <td className="py-3.5 px-4 whitespace-nowrap">
                        <TierChip tier={f.tier} reason={f.tier_reason} />
                      </td>

                      {/* Status */}
                      <td className="py-3.5 px-4 whitespace-nowrap">
                        <StatusPill status={f.status} size="sm" />
                      </td>

                      {/* Action Cell */}
                      <td className="py-3.5 px-4 text-right whitespace-nowrap">
                        {isFixReady ? (
                          <PillButton
                            variant="primary"
                            size="sm"
                            loading={loadingAction === f.id}
                            onClick={() => handleRemediateSingle(f)}
                            title={`Remediate ${f.id} autonomously with 5-agent pipeline`}
                          >
                            Remediate
                          </PillButton>
                        ) : f.tier === "UNSUPPORTED_LANG" ? (
                          <span className="text-[12px] text-ink-dim italic">
                            Adapter not enabled
                          </span>
                        ) : f.tier === "ESCALATE" ? (
                          <span className="text-[12px] text-ink-dim italic">
                            Needs human
                          </span>
                        ) : (
                          <span className="text-[12px] text-ink-dim italic">
                            Source not connected
                          </span>
                        )}
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination Bar */}
        {totalPages > 1 && (
          <div className="p-4 border-t border-white/[0.06] flex items-center justify-between text-[13px] text-ink-muted">
            <div>
              Page {page} of {totalPages}
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={page <= 1}
                className="p-1.5 rounded-lg border border-white/10 hover:bg-white/5 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
                aria-label="Previous page"
              >
                <ChevronLeft size={16} />
              </button>
              <button
                onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                disabled={page >= totalPages}
                className="p-1.5 rounded-lg border border-white/10 hover:bg-white/5 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
                aria-label="Next page"
              >
                <ChevronRight size={16} />
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
