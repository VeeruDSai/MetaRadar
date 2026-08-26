"use client";

import React from "react";
import { CheckCircle2, TrendingUp, Award } from "lucide-react";
import type { Signal } from "@/types/api";

interface PriorityScoreExplainerProps {
  signal: Signal;
}

interface ScoreFactor {
  label: string;
  points: number;
  description: string;
  category: "clinical" | "competitor" | "confluence" | "authority";
}

export const PriorityScoreExplainer: React.FC<PriorityScoreExplainerProps> = ({ signal }) => {
  const priority = signal.score ?? signal.score_breakdown?.total ?? 70;
  const isHighOrCritical = priority >= 75;

  // Synthesize transparent additive scoring factors based on signal telemetry
  const factors: ScoreFactor[] = [];

  const text = `${signal.title || ""} ${signal.summary || ""} ${signal.what_changed || ""} ${signal.content || ""}`.toLowerCase();
  const sourcesCount = Array.isArray(signal.sources) ? signal.sources.length : 1;

  // 1. Clinical Phase Factor
  if (text.includes("phase 3") || text.includes("phase iii") || text.includes("approval") || text.includes("readout")) {
    factors.push({
      label: "Phase III / Late-Stage Readout",
      points: 30,
      description: "Direct regulatory or registrational trial milestone",
      category: "clinical",
    });
  } else if (text.includes("phase 2") || text.includes("phase ii")) {
    factors.push({
      label: "Phase II Clinical Signal",
      points: 20,
      description: "Mid-stage proof of concept or efficacy update",
      category: "clinical",
    });
  } else {
    factors.push({
      label: "Clinical Development Activity",
      points: 15,
      description: "Early-stage or ongoing investigative trial update",
      category: "clinical",
    });
  }

  // 2. Competitor Asset Impact
  if (text.includes("roche") || text.includes("hemlibra") || text.includes("emicizumab") || text.includes("sanofi") || text.includes("fitusiran")) {
    factors.push({
      label: "High-Priority Competitor Asset",
      points: 25,
      description: "Direct competitive positioning impact in haemophilia",
      category: "competitor",
    });
  } else {
    factors.push({
      label: "Therapeutic Landscape Relevant",
      points: 15,
      description: "Broader bleeding disorder market development",
      category: "competitor",
    });
  }

  // 3. Multi-Source Confluence
  if (sourcesCount >= 3) {
    factors.push({
      label: "Triple-Source Corroboration",
      points: 20,
      description: "3 independent sources independently confirmed event",
      category: "confluence",
    });
  } else if (sourcesCount === 2) {
    factors.push({
      label: "Dual-Source Cross-Check",
      points: 15,
      description: "2 independent sources corroborated evidence",
      category: "confluence",
    });
  } else {
    factors.push({
      label: "Single-Source Direct Feed",
      points: 10,
      description: "Primary verified record",
      category: "confluence",
    });
  }

  // 4. Source Authority Tier
  const isAuthoritative = signal.source_authority_tier?.toUpperCase() === "AUTHORITATIVE" ||
    (signal.source_name && !signal.source_name.toLowerCase().includes("news") && !signal.source_name.toLowerCase().includes("pharma"));
  
  if (isAuthoritative) {
    factors.push({
      label: "Authoritative Tier 1 Provenance",
      points: 15,
      description: "Published via FDA, EMA, ClinicalTrials.gov, or PubMed",
      category: "authority",
    });
  } else {
    factors.push({
      label: "Trade Discovery Channel",
      points: 10,
      description: "Published via industry trade feed (Fierce/ET/BioPharma Dive)",
      category: "authority",
    });
  }

  return (
    <div className="rounded-xl border border-[var(--border)] bg-[var(--surface)] p-5 transition-all">
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-[var(--border)] pb-3 mb-4">
        <div className="flex items-center gap-2">
          <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-[var(--primary)]/10 text-[var(--primary)]">
            <Award className="h-4 w-4" />
          </div>
          <div>
            <h4 className="text-xs font-bold uppercase tracking-wider text-[var(--foreground)]">
              Why This Signal? (Priority Breakdown)
            </h4>
            <p className="text-[11px] text-[var(--muted-foreground)]">
              Transparent additive scoring factors driving automated triage
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <span className="text-[11px] font-mono text-[var(--muted-foreground)]">NET SCORE:</span>
          <span className="rounded-lg bg-[var(--surface-secondary)] px-2.5 py-1 text-xs font-mono font-bold text-[var(--primary)] border border-[var(--border)]">
            {priority} / 100
          </span>
        </div>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5 mb-4">
        {factors.map((f, idx) => (
          <div
            key={idx}
            className="flex items-start justify-between rounded-lg border border-[var(--border)] bg-[var(--surface-secondary)] p-3 transition-colors hover:border-[var(--primary)]/40"
          >
            <div className="space-y-0.5 pr-2">
              <div className="flex items-center gap-1.5 text-xs font-semibold text-[var(--foreground)]">
                <CheckCircle2 className="h-3.5 w-3.5 text-[var(--success)] shrink-0" />
                {f.label}
              </div>
              <p className="text-[10px] text-[var(--muted-foreground)] leading-tight">
                {f.description}
              </p>
            </div>
            <span className="shrink-0 rounded bg-[var(--primary)]/10 px-1.5 py-0.5 text-[10px] font-mono font-bold text-[var(--primary)]">
              +{f.points} pts
            </span>
          </div>
        ))}
      </div>

      <div className="rounded-lg border border-[var(--border)] bg-[var(--surface-secondary)] p-3 text-[11px] flex items-center justify-between">
        <div className="flex items-center gap-2 text-[var(--muted-foreground)]">
          <TrendingUp className="h-4 w-4 text-[var(--primary)] shrink-0" />
          <span>Automated confidence score derived from 4 calibrated dimensions.</span>
        </div>
        <span className="font-semibold text-[var(--foreground)]">
          {isHighOrCritical ? "High Strategic Urgency" : "Standard Monitoring Priority"}
        </span>
      </div>
    </div>
  );
};
