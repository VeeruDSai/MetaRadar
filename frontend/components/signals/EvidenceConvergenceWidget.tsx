"use client";

import React from "react";
import { ShieldCheck, Sparkles, Network, ExternalLink } from "lucide-react";
import type { Signal, SignalSource } from "@/types/api";

interface EvidenceConvergenceWidgetProps {
  signal: Signal;
}

interface SourceNode {
  name: string;
  tier: "authoritative" | "regulatory" | "discovery";
  badge: string;
  badgeClass: string;
  link?: string;
}

export const EvidenceConvergenceWidget: React.FC<EvidenceConvergenceWidgetProps> = ({ signal }) => {
  const sourceList: SignalSource[] = Array.isArray(signal.sources) && signal.sources.length > 0
    ? signal.sources
    : [
        {
          id: signal.source_id || "clinical_trials",
          name: signal.source_name || "ClinicalTrials.gov",
          type: "registry",
          url: signal.canonical_url,
        },
      ];

  const classifySource = (src: SignalSource): SourceNode => {
    const name = src.name || src.id || "Source";
    const s = name.toLowerCase() + " " + (src.id || "").toLowerCase();
    
    if (s.includes("clinicaltrials") || s.includes("nct") || s.includes("pubmed") || s.includes("pmid")) {
      return {
        name: s.includes("pubmed") ? "NCBI PubMed" : "ClinicalTrials.gov",
        tier: "authoritative",
        badge: "Tier 1 Authoritative",
        badgeClass: "bg-[var(--success)]/10 text-[var(--success)] border-[var(--success)]/20",
        link: src.url || signal.canonical_url,
      };
    }
    if (s.includes("fda") || s.includes("ema") || s.includes("drugs@fda") || s.includes("epar")) {
      return {
        name: s.includes("fda") ? "U.S. FDA Drug Database" : "European Medicines Agency",
        tier: "regulatory",
        badge: "Tier 1 Regulatory",
        badgeClass: "bg-[var(--primary)]/10 text-[var(--primary)] border-[var(--primary)]/20",
        link: src.url || signal.canonical_url,
      };
    }
    if (s.includes("fierce")) {
      return {
        name: "Fierce Pharma Industry Wire",
        tier: "discovery",
        badge: "Tier 3 Discovery",
        badgeClass: "bg-[var(--warning)]/10 text-[var(--warning)] border-[var(--warning)]/20",
        link: src.url || signal.canonical_url,
      };
    }
    if (s.includes("et") || s.includes("economic times") || s.includes("healthworld")) {
      return {
        name: "ET Healthworld Pharma",
        tier: "discovery",
        badge: "Tier 3 Discovery",
        badgeClass: "bg-[var(--warning)]/10 text-[var(--warning)] border-[var(--warning)]/20",
        link: src.url || signal.canonical_url,
      };
    }
    if (s.includes("biopharma") || s.includes("dive")) {
      return {
        name: "BioPharma Dive Intelligence",
        tier: "discovery",
        badge: "Tier 3 Discovery",
        badgeClass: "bg-[var(--warning)]/10 text-[var(--warning)] border-[var(--warning)]/20",
        link: src.url || signal.canonical_url,
      };
    }
    return {
      name: name,
      tier: "discovery",
      badge: "Tier 3 Discovery",
      badgeClass: "bg-[var(--surface-secondary)] text-[var(--muted-foreground)] border-[var(--border)]",
      link: src.url || signal.canonical_url,
    };
  };

  const nodes: SourceNode[] = sourceList.map(classifySource);
  const authoritativeCount = nodes.filter((n: SourceNode) => n.tier === "authoritative" || n.tier === "regulatory").length;
  const discoveryCount = nodes.filter((n: SourceNode) => n.tier === "discovery").length;
  const isMultiSource = nodes.length > 1;

  return (
    <div className="rounded-xl border border-[var(--border)] bg-[var(--surface)] p-5 transition-all">
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-[var(--border)] pb-3 mb-4">
        <div className="flex items-center gap-2">
          <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-[var(--primary)]/10 text-[var(--primary)]">
            <Network className="h-4 w-4" />
          </div>
          <div>
            <h4 className="text-xs font-bold uppercase tracking-wider text-[var(--foreground)]">
              Evidence Convergence Tree
            </h4>
            <p className="text-[11px] text-[var(--muted-foreground)]">
              Multi-source cross-validation across evidence and discovery channels
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {authoritativeCount > 0 && (
            <span className="inline-flex items-center gap-1 rounded-full border border-[var(--success)]/20 bg-[var(--success)]/10 px-2.5 py-0.5 text-[10px] font-semibold text-[var(--success)]">
              <ShieldCheck className="h-3 w-3" />
              {authoritativeCount} Authoritative
            </span>
          )}
          {discoveryCount > 0 && (
            <span className="inline-flex items-center gap-1 rounded-full border border-[var(--warning)]/20 bg-[var(--warning)]/10 px-2.5 py-0.5 text-[10px] font-semibold text-[var(--warning)]">
              <Sparkles className="h-3 w-3" />
              {discoveryCount} Discovery
            </span>
          )}
        </div>
      </div>

      {isMultiSource ? (
        <div className="space-y-3">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            <div className="space-y-2">
              <div className="text-[10px] font-bold uppercase tracking-wider text-[var(--muted-foreground)]">
                Contributing Independent Sources
              </div>
              {nodes.map((node: SourceNode, i: number) => (
                <div
                  key={i}
                  className="flex items-center justify-between rounded-lg border border-[var(--border)] bg-[var(--surface-secondary)] p-2.5 text-xs transition-colors hover:border-[var(--primary)]/40"
                >
                  <div className="space-y-1">
                    <div className="font-medium text-[var(--foreground)]">{node.name}</div>
                    <span className={`inline-block rounded px-1.5 py-0.2 text-[9px] font-semibold border ${node.badgeClass}`}>
                      {node.badge}
                    </span>
                  </div>
                  {node.link && (
                    <a
                      href={node.link}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-[var(--muted-foreground)] hover:text-[var(--primary)] p-1 transition-colors"
                      title="Open source record"
                    >
                      <ExternalLink className="h-3.5 w-3.5" />
                    </a>
                  )}
                </div>
              ))}
            </div>

            <div className="flex flex-col justify-center rounded-lg border border-[var(--primary)]/20 bg-[var(--primary)]/5 p-4">
              <div className="flex items-center gap-2 text-xs font-bold text-[var(--primary)] mb-2">
                <ShieldCheck className="h-4 w-4" />
                Validated Decision Convergence
              </div>
              <p className="text-[11px] leading-relaxed text-[var(--foreground)] mb-3">
                {authoritativeCount >= 2
                  ? "High confidence: Multi-source corroboration across authoritative clinical registries and publications confirms this development."
                  : authoritativeCount === 1
                  ? "Verified confidence: Authoritative primary evidence corroborates the initial trade discovery feed."
                  : "Discovery signal: Commercial and trade sources reported this development. Awaiting primary registry confirmation."}
              </p>
              <div className="flex items-center gap-2 text-[10px] font-mono text-[var(--muted-foreground)]">
                <span>CONFLUENCE STATUS:</span>
                <span className="font-bold text-[var(--foreground)]">
                  {authoritativeCount >= 1 ? "CORROBORATED" : "INDEPENDENT DISCOVERY"}
                </span>
              </div>
            </div>
          </div>
        </div>
      ) : (
        <div className="rounded-lg border border-[var(--border)] bg-[var(--surface-secondary)] p-4">
          <div className="flex items-center justify-between">
            <div className="space-y-1">
              <div className="text-[10px] font-bold uppercase tracking-wider text-[var(--muted-foreground)]">
                Direct Evidence Anchor
              </div>
              <div className="text-xs font-semibold text-[var(--foreground)]">
                {nodes[0]?.name || "Primary Registry"}
              </div>
              <span className={`inline-block rounded px-1.5 py-0.2 text-[9px] font-semibold border ${nodes[0]?.badgeClass || ""}`}>
                {nodes[0]?.badge || "Authoritative Source"}
              </span>
            </div>
            {nodes[0]?.link && (
              <a
                href={nodes[0].link}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-1 text-xs font-medium text-[var(--primary)] hover:underline"
              >
                View Primary Record
                <ExternalLink className="h-3 w-3" />
              </a>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
