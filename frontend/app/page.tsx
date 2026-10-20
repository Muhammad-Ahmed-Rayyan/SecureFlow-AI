"use client";

import React from "react";
import BracketLabel from "@/components/ui/BracketLabel";
import PillButton from "@/components/ui/PillButton";
import ScrollHint from "@/components/layout/ScrollHint";
import Constellation from "@/components/layout/Constellation";
import Skeleton from "@/components/ui/Skeleton";
import EmptyState from "@/components/ui/EmptyState";
import { useSummary } from "@/lib/api";
import { formatHours, formatNumber, formatPercent } from "@/lib/format";
import { Shield, Search, Wrench, CheckCircle2, GitPullRequest, AlertCircle } from "lucide-react";

export default function HomePage() {
  const { data: summary, error, isLoading } = useSummary();

  const agentCards = [
    {
      title: "Triage Agent",
      role: "Deterministic Policy",
      icon: Shield,
      desc: "Scores priority, classifies remediation tier, and detects data quality drift.",
    },
    {
      title: "Analyzer Agent",
      role: "Deep Source Context",
      icon: Search,
      desc: "Maps AST caller hierarchy and relocates drifted line numbers in the live repo.",
    },
    {
      title: "Fixer Agent",
      role: "Surgical Code Generation",
      icon: Wrench,
      desc: "Generates full-file replacements avoiding regex truncation and patch corruption.",
    },
    {
      title: "Validator Agent",
      role: "Multi-Gate Sandbox",
      icon: CheckCircle2,
      desc: "Runs AST policy, syntax compiler, exploit tests, and Bandit differential analysis.",
    },
    {
      title: "PR Agent",
      role: "Evidence-Backed Delivery",
      icon: GitPullRequest,
      desc: "Opens draft pull requests with complete before/after verification logs.",
    },
  ];

  return (
    <div className="relative w-full max-w-7xl mx-auto px-6 sm:px-8 pt-8 sm:pt-16">
      {/* HERO SECTION */}
      <section className="relative min-h-[calc(100vh-140px)] flex flex-col justify-between">
        <div className="w-full">
          {/* Eyebrow */}
          <div className="mb-6 animate-rise">
            <BracketLabel>DEVSECOPS</BracketLabel>
          </div>

          {/* Split Headline & Hero Grid */}
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
            {/* Left Headline Block */}
            <div className="lg:col-span-7 flex flex-col justify-between">
              <h1 className="text-4xl sm:text-6xl md:text-7xl font-light tracking-display leading-[1.05] text-ink animate-rise">
                <span className="block font-medium">Remediating</span>
                <span className="block text-ink-muted">the Backlog</span>
                <span className="block mt-2">
                  in{" "}
                  <span className="font-normal text-white">
                    Minutes<span className="text-accent font-bold">.</span>
                  </span>
                </span>
              </h1>

              {/* Action */}
              <div className="mt-8 sm:mt-12 flex items-center gap-4 animate-rise">
                <PillButton variant="primary" size="md" href="/dashboard">
                  Open dashboard
                </PillButton>
              </div>
            </div>

            {/* Right Blurb & Constellation Orb Block */}
            <div className="lg:col-span-5 flex flex-col items-start lg:items-end justify-between">
              {/* Blurb */}
              <p className="text-[13px] text-ink-muted max-w-[280px] leading-relaxed mb-8 animate-rise">
                SecureFlow AI turns scanner findings into validated, review-ready draft pull requests.
              </p>

              {/* Ambient Orb & Constellation */}
              <div className="relative w-full max-w-[420px] aspect-square rounded-full flex items-center justify-center p-6 mt-4">
                {/* Radial Glow */}
                <div
                  className="absolute inset-0 rounded-full pointer-events-none"
                  style={{
                    background:
                      "radial-gradient(circle, rgba(43,89,255,0.24) 0%, rgba(43,89,255,0.06) 55%, transparent 70%)",
                  }}
                />
                <div className="relative z-10 w-full">
                  <Constellation />
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Scroll Hint */}
        <div className="pb-8 pt-12">
          <ScrollHint />
        </div>
      </section>

      {/* HOW IT WORKS SECTION */}
      <section className="py-20 border-t border-white/[0.06]">
        <div className="mb-12">
          <BracketLabel>HOW IT WORKS</BracketLabel>
          <h2 className="text-2xl sm:text-3xl font-medium text-ink mt-2">
            The 5-Agent Autonomous Remediation Pipeline
          </h2>
          <p className="text-[14px] text-ink-muted mt-1 max-w-xl">
            Deterministic rule gates ensure zero hallucination, verifiable exploit prevention, and reproducible diffs.
          </p>
        </div>

        {/* 5 Agent Cards */}
        <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
          {agentCards.map((agent, i) => {
            const Icon = agent.icon;
            return (
              <div
                key={agent.title}
                className="glass p-5 rounded-card flex flex-col justify-between hover:border-accent/40 transition-all duration-300 group"
              >
                <div>
                  <div className="w-8 h-8 rounded-lg bg-accent/15 border border-accent/30 text-accent-bright flex items-center justify-center mb-4 group-hover:scale-105 transition-transform">
                    <Icon size={16} />
                  </div>
                  <div className="text-[11px] font-mono text-accent-soft uppercase tracking-wider mb-1">
                    0{i + 1} {"//"} {agent.role}
                  </div>
                  <h3 className="text-[15px] font-medium text-white mb-2">{agent.title}</h3>
                  <p className="text-[12px] text-ink-muted leading-relaxed">{agent.desc}</p>
                </div>
              </div>
            );
          })}
        </div>
      </section>

      {/* BY THE NUMBERS SECTION */}
      <section className="py-20 border-t border-white/[0.06]">
        <div className="mb-12">
          <BracketLabel>BY THE NUMBERS</BracketLabel>
          <h2 className="text-2xl sm:text-3xl font-medium text-ink mt-2">
            Real Backlog Analytics
          </h2>
          <p className="text-[14px] text-ink-muted mt-1">
            Measured directly from your security scan findings and execution pipeline.
          </p>
        </div>

        {error ? (
          <EmptyState
            icon={AlertCircle}
            title="Metrics Unreachable"
            description="Could not connect to the SecureFlow AI backend. Check if the server is running."
            action={
              <PillButton variant="ghost" size="sm" onClick={() => window.location.reload()}>
                Retry connection
              </PillButton>
            }
          />
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {/* Metric 1 */}
            <div className="glass p-6 rounded-card">
              <div className="text-[12px] font-mono text-ink-muted uppercase tracking-wider mb-2">
                Open Security Findings
              </div>
              {isLoading || !summary ? (
                <Skeleton height={48} width={120} className="mb-2" />
              ) : (
                <div className="text-4xl sm:text-5xl font-light text-white tracking-tight">
                  {formatNumber(summary.open_findings)}
                </div>
              )}
              <div className="text-[13px] text-ink-muted mt-2">
                Total scanner findings triaged and tracked
              </div>
            </div>

            {/* Metric 2 */}
            <div className="glass p-6 rounded-card">
              <div className="text-[12px] font-mono text-ink-muted uppercase tracking-wider mb-2">
                Estimated Engineer-Hours
              </div>
              {isLoading || !summary ? (
                <Skeleton height={48} width={140} className="mb-2" />
              ) : (
                <div className="text-4xl sm:text-5xl font-light text-accent-bright tracking-tight">
                  {formatHours(summary.total_engineer_hours_baseline)}
                </div>
              )}
              <div className="text-[13px] text-ink-muted mt-2">
                Manual remediation effort required across backlog
              </div>
            </div>

            {/* Metric 3 */}
            <div className="glass p-6 rounded-card">
              <div className="text-[12px] font-mono text-ink-muted uppercase tracking-wider mb-2">
                Without Scanner Fix
              </div>
              {isLoading || !summary ? (
                <Skeleton height={48} width={100} className="mb-2" />
              ) : (
                <div className="text-4xl sm:text-5xl font-light text-white tracking-tight">
                  {formatPercent(summary.baseline_without_fix_share_pct)}
                </div>
              )}
              <div className="text-[13px] text-ink-muted mt-2">
                Share of findings needing developer intervention
              </div>
            </div>
          </div>
        )}

        {/* Repeat CTA */}
        <div className="mt-16 flex flex-col items-center justify-center text-center">
          <h3 className="text-xl sm:text-2xl font-light text-white mb-6">
            Ready to resolve your security debt?
          </h3>
          <PillButton variant="primary" size="md" href="/dashboard">
            Open dashboard
          </PillButton>
        </div>
      </section>
    </div>
  );
}
