import React from "react";

export default function SourcesPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-100">Data Sources & Connectors</h1>
        <p className="text-sm text-slate-400">Public connector health status, rate limits & quota metrics</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {[
          { name: "NCBI PubMed", type: "Literature & Trials", freshness: "Near Real-Time", status: "Active" },
          { name: "ClinicalTrials.gov", type: "Trial Registry", freshness: "Near Real-Time", status: "Active" },
          { name: "NewsAPI", type: "Industry Press", freshness: "Delayed (24h)", status: "Quota: 100/day" },
          { name: "FDA OpenFDA", type: "Regulatory Decisions", freshness: "Batch / Adapter", status: "Ready" },
          { name: "EMA RSS", type: "EU Regulatory", freshness: "Batch / Adapter", status: "Ready" },
          { name: "Synthetic Demo Set", type: "Pre-curated Haemophilia", freshness: "Synthetic", status: "500 Signals Loaded" },
        ].map((s) => (
          <div key={s.name} className="bento-card flex justify-between items-center">
            <div>
              <h3 className="font-semibold text-slate-100 text-sm">{s.name}</h3>
              <p className="text-xs text-slate-400">{s.type} · {s.freshness}</p>
            </div>
            <span className="text-xs font-semibold px-2 py-1 bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 rounded">
              {s.status}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
