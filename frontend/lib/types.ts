export type Severity = "CRITICAL" | "HIGH" | "MEDIUM" | "LOW";
export type FindingStatus = "NEW" | "QUEUED" | "RUNNING" | "PR_OPEN" | "MERGED" | "REJECTED" | "ESCALATED" | "FAILED";
export type RemediationTier = "AUTO_FIX" | "DEPENDENCY" | "ESCALATE" | "UNSUPPORTED_LANG";
export type AgentRemediationStatus = "NOT_STARTED" | "TRIAGED" | "ANALYZED" | "PATCH_GENERATED" | "VALIDATED" | "PR_OPENED" | "FAILED" | "ESCALATED";

export interface Finding {
  id: string;
  repository: string;
  tool: string;
  finding_type: string;
  cve_id?: string | null;
  severity: Severity;
  file_path: string;
  line_number: number;
  description: string;
  confidence: number;
  fix_ready_status: boolean;
  remediation_time_minutes: number;
  created_at: string;
  status: FindingStatus;
  pull_request_url?: string | null;
  pull_request_number?: number | null;
  metadata?: Record<string, unknown>;
  quality_flags: string[];
  baseline_fix_time_minutes: number;
  baseline_source: string;
  tier: RemediationTier;
  tier_reason: string;
  fix_order: number;
  is_fix_ready: boolean;
  agent_remediation_status: AgentRemediationStatus;
  last_run_id?: string | null;
  updated_at: string;
}

export interface PatchInfo {
  file_path: string;
  original_line: number;
  drift_detected: boolean;
  actual_line?: number | null;
  explanation: string;
  diff: string;
}

export interface ValidationCheck {
  name: string;
  passed: boolean;
  details?: string;
  stdout?: string;
  stderr?: string;
}

export interface ValidationResults {
  policy_passed: boolean;
  syntax_passed: boolean;
  tests_passed: boolean;
  exploit_passed: boolean;
  bandit_passed: boolean;
  checks: ValidationCheck[];
}

export interface PullRequestInfo {
  number: number;
  url: string;
  branch: string;
  state: "open" | "closed" | "merged";
  merged: boolean;
  time_to_draft_seconds?: number | null;
}

export interface Run {
  id: string;
  finding_id: string;
  status: FindingStatus;
  target_repo: string;
  base_branch: string;
  branch_name: string;
  agent_remediation_status: AgentRemediationStatus;
  current_agent?: string | null;
  attempts: number;
  patch?: PatchInfo | null;
  timings?: Record<string, number> | null;
  usage?: { prompt_tokens: number; completion_tokens: number; total_tokens: number } | null;
  validation_results?: ValidationResults | null;
  pull_request?: PullRequestInfo | null;
  error?: string | null;
  created_at: string;
  updated_at: string;
}

export interface RunEvent {
  id: string;
  run_id: string;
  seq: number;
  timestamp: string;
  agent: string;
  level: "info" | "warn" | "error" | "success";
  message: string;
  details?: Record<string, unknown> | null;
}

export interface MetricsSummaryResponse {
  total_findings: number;
  open_findings: number;
  fix_ready_count: number;
  active_runs_count: number;
  completed_runs_count: number;
  total_engineer_hours_baseline: number;
  hours_saved: number;
  avg_remediation_seconds: number;
  acceptance_rate_pct: number;
  baseline_without_fix_share_pct: number;
  severities: Record<string, number>;
}

export interface BacklogTimelinePoint {
  timestamp: string;
  open: number;
  in_review: number;
  merged: number;
}

export interface BacklogBreakdown {
  timeline: BacklogTimelinePoint[];
  by_age_and_severity: Array<{
    age_bucket: "0-30" | "31-90" | "90+";
    CRITICAL: number;
    HIGH: number;
    MEDIUM: number;
    LOW: number;
  }>;
}

export interface FunnelStage {
  stage: string;
  count: number;
  pct_of_backlog: number;
  caption: string;
}

export interface FunnelResponse {
  stages: FunnelStage[];
  total_backlog: number;
}

export interface MTTRComparison {
  manual_hours: number;
  secureflow_seconds: number;
  reduction_pct: number;
  time_to_draft_avg_seconds: number;
  time_to_merge_avg_seconds: number;
}
