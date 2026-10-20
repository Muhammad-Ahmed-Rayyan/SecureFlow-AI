"use client";

import useSWR from "swr";
import type {
  Finding,
  Run,
  RunEvent,
  MetricsSummaryResponse,
  BacklogBreakdown,
  FunnelResponse,
  MTTRComparison,
} from "./types";

export const fetcher = async (url: string) => {
  const res = await fetch(url);
  if (!res.ok) {
    const errorText = await res.text();
    let message = `API error ${res.status}`;
    try {
      const parsed = JSON.parse(errorText);
      message = parsed.detail || parsed.message || message;
    } catch {
      message = errorText || message;
    }
    throw new Error(message);
  }
  return res.json();
};

export function useSummary(refreshInterval = 5000) {
  return useSWR<MetricsSummaryResponse>("/api/metrics/summary", fetcher, {
    refreshInterval,
    revalidateOnFocus: true,
  });
}

export function useBacklog(refreshInterval = 5000) {
  return useSWR<BacklogBreakdown>("/api/metrics/backlog", fetcher, {
    refreshInterval,
  });
}

export function useFunnel(refreshInterval = 10000) {
  return useSWR<FunnelResponse>("/api/metrics/funnel", fetcher, {
    refreshInterval,
  });
}

export function useMTTR(refreshInterval = 10000) {
  return useSWR<MTTRComparison>("/api/metrics/mttr", fetcher, {
    refreshInterval,
  });
}

export function useFindings(params?: {
  page?: number;
  page_size?: number;
  severity?: string;
  tier?: string;
  status?: string;
  fix_ready_only?: boolean;
  repository?: string;
  finding_type?: string;
  search?: string;
}) {
  const query = new URLSearchParams();
  if (params?.page) query.set("page", String(params.page));
  if (params?.page_size) query.set("page_size", String(params.page_size));
  if (params?.severity) query.set("severity", params.severity);
  if (params?.tier) query.set("tier", params.tier);
  if (params?.status) query.set("status", params.status);
  if (params?.fix_ready_only !== undefined) query.set("fix_ready_only", String(params.fix_ready_only));
  if (params?.repository) query.set("repository", params.repository);
  if (params?.finding_type) query.set("finding_type", params.finding_type);
  if (params?.search) query.set("search", params.search);

  const url = `/api/findings?${query.toString()}`;
  return useSWR<{
    items: Finding[];
    total: number;
    page: number;
    page_size: number;
    pages: number;
  }>(url, fetcher, { refreshInterval: 5000 });
}

export function useFinding(id: string | null) {
  return useSWR<Finding>(id ? `/api/findings/${id}` : null, fetcher);
}

export function useRuns(limit = 20) {
  return useSWR<Run[]>(`/api/runs?limit=${limit}`, fetcher, {
    refreshInterval: 3000,
  });
}

export function useRun(id: string | null) {
  return useSWR<Run>(id ? `/api/runs/${id}` : null, fetcher, {
    refreshInterval: (run) => {
      if (!run) return 2000;
      if (run.status === "RUNNING" || run.status === "QUEUED") return 1500;
      return 0; // stop polling once finished
    },
  });
}

export function useRunEvents(id: string | null) {
  return useSWR<RunEvent[]>(id ? `/api/runs/${id}/events` : null, fetcher, {
    refreshInterval: 1500,
  });
}

// Action helpers
export async function startRemediation(findingId: string, dryRun = false) {
  const res = await fetch(`/api/findings/${findingId}/remediate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ dry_run: dryRun }),
  });
  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: "Remediation trigger failed" }));
    throw new Error(error.detail || "Remediation trigger failed");
  }
  return res.json();
}

export async function batchRemediate(count = 3, severity = "CRITICAL") {
  const res = await fetch("/api/remediate/batch", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ count, severity, fix_ready_only: true }),
  });
  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: "Batch remediation failed" }));
    throw new Error(error.detail || "Batch remediation failed");
  }
  return res.json();
}

export async function syncPRs() {
  const res = await fetch("/api/prs/sync", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
  });
  if (!res.ok) throw new Error("PR sync failed");
  return res.json();
}

export async function scanRepo(repo?: string) {
  const res = await fetch("/api/scan/repo", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ repository: repo }),
  });
  if (!res.ok) throw new Error("Repo scan failed");
  return res.json();
}

export async function importScan(file: File, format: "csv" | "sarif" | "json") {
  const formData = new FormData();
  formData.append("file", file);
  const endpoint = format === "csv" ? "/api/ingest/csv" : format === "sarif" ? "/api/ingest/sarif" : "/api/ingest/json";
  const res = await fetch(endpoint, {
    method: "POST",
    body: formData,
  });
  if (!res.ok) throw new Error("Scan import failed");
  return res.json();
}
