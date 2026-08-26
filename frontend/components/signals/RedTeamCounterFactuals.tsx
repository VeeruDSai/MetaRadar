"use client";

import React from "react";
import { ShieldAlert, AlertTriangle, Scale, RefreshCw } from "lucide-react";
import type { Signal } from "@/types/api";

interface RedTeamCounterFactualsProps {
  signal: Signal;
  hasContradictions?: boolean;
}

export const RedTeamCounterFactuals: React.FC<RedTeamCounterFactualsProps> = ({ signal, hasContradictions = false }) => {
  return (
    <div className="rounded-xl border border-[var(--border)] bg-[var(--surface)] p-5 transition-all">
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-[var(--border)] pb-3 mb-4">
        <div className="flex items-center gap-2">
          <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-[var(--warning)]/10 text-[var(--warning)]">
            <Scale className="h-4 w-4" />
          </div>
          <div>
            <h4 className="text-xs font-bold uppercase tracking-wider text-[var(--foreground)]">
              What Would Change Our Assessment? (Red-Team Falsification)
            </h4>
            <p className="text-[11px] text-[var(--muted-foreground)]">
              Active self-challenging conditions that would invalidate or downgrade this signal
            </p>
          </div>
        </div>

        <span className={`inline-flex items-center gap-1 rounded-full border px-2.5 py-0.5 text-[10px] font-semibold ${
          hasContradictions
            ? "border-[var(--danger)]/20 bg-[var(--danger)]/10 text-[var(--danger)]"
            : "border-[var(--success)]/20 bg-[var(--success)]/10 text-[var(--success)]"
        }`}>
          {hasContradictions ? "Contradiction Flagged" : "Self-Stress Tested (0 Active Conflicts)"}
        </span>
      </div>

      <div className="space-y-2.5">
        <div className="rounded-lg border border-[var(--border)] bg-[var(--surface-secondary)] p-3 text-xs">
          <div className="flex items-center gap-2 font-semibold text-[var(--foreground)] mb-1">
            <AlertTriangle className="h-3.5 w-3.5 text-[var(--warning)] shrink-0" />
            1. Independent Clinical Replication
          </div>
          <p className="text-[11px] text-[var(--muted-foreground)] leading-relaxed pl-5">
            If peer-reviewed publication data fails to replicate reported primary endpoint statistical significance or shows altered safety sub-cohort analysis.
          </p>
        </div>

        <div className="rounded-lg border border-[var(--border)] bg-[var(--surface-secondary)] p-3 text-xs">
          <div className="flex items-center gap-2 font-semibold text-[var(--foreground)] mb-1">
            <RefreshCw className="h-3.5 w-3.5 text-[var(--primary)] shrink-0" />
            2. Registry Protocol Revision
          </div>
          <p className="text-[11px] text-[var(--muted-foreground)] leading-relaxed pl-5">
            If ClinicalTrials.gov or EU CTR amends target patient inclusion criteria, reducing the addressable haemophilia market population.
          </p>
        </div>

        <div className="rounded-lg border border-[var(--border)] bg-[var(--surface-secondary)] p-3 text-xs">
          <div className="flex items-center gap-2 font-semibold text-[var(--foreground)] mb-1">
            <ShieldAlert className="h-3.5 w-3.5 text-[var(--danger)] shrink-0" />
            3. Regulatory PDUFA Delay or Complete Response Letter
          </div>
          <p className="text-[11px] text-[var(--muted-foreground)] leading-relaxed pl-5">
            If FDA or EMA requests supplementary bridging data or issues an inspection finding extending launch timelines.
          </p>
        </div>
      </div>
    </div>
  );
};
