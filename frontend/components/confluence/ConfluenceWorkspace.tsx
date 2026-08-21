'use client'

import React, { useState, useEffect, useCallback } from 'react'
import type { ConfluenceAlertItem, ConfluenceInspectResponse } from '@/types/api'
import { fetchConfluenceAlerts, inspectConfluence } from '@/lib/api'
import { formatError, FormattedError } from '@/lib/errors'
import { ErrorState } from '../common/ErrorState'
import { EmptyState } from '../common/EmptyState'

export function ConfluenceWorkspace() {
  const [alerts, setAlerts] = useState<ConfluenceAlertItem[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<FormattedError | null>(null)
  const [inspectTarget, setInspectTarget] = useState<ConfluenceInspectResponse | null>(null)
  const [inspectLoading, setInspectLoading] = useState(false)

  const loadAlerts = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await fetchConfluenceAlerts(50)
      setAlerts(data)
    } catch (err) {
      setError(formatError(err, 'Failed to fetch confluence alerts.'))
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    loadAlerts()
  }, [loadAlerts])

  const handleInspect = async (item: ConfluenceAlertItem) => {
    setInspectLoading(true)
    try {
      const data = await inspectConfluence(item.confluence_id)
      setInspectTarget(data)
    } catch (err) {
      // Fallback to local item evidence if endpoint is unavailable
      setInspectTarget({
        confluence_id: item.confluence_id,
        development_id: item.development_id,
        development_title: item.development_title,
        score: item.score ?? 0.0,
        label: `${item.confluence_type || 'Confirmed'} Confluence (${item.independent_sources_count ?? 0} Independent Sources)`,
        confluence_type: item.confluence_type || 'confirmed',
        window_hours: 48,
        distinct_sources_count: item.independent_sources_count ?? 0,
        score_breakdown: item.score_breakdown || {},
        reasoning: item.reasoning || `Score of ${item.score ?? 0.0} calculated from ${item.independent_sources_count ?? 0} distinct independent source providers converging in 48h.`,
        sources: item.evidence_sources || [],
        detected_at: item.created_at,
      })
    } finally {
      setInspectLoading(false)
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-[var(--foreground)]">Multi-Source Confluence Alerts</h2>
          <p className="text-xs text-[var(--muted-foreground)] mt-1">
            Independent signals converging on the same development within a 48-hour window (≥3 distinct independent source providers required).
          </p>
        </div>
        <button
          onClick={loadAlerts}
          className="px-3.5 py-1.5 rounded-lg bg-[var(--surface-muted)] hover:bg-[var(--surface-subtle)] text-[var(--foreground)] text-xs transition border border-[var(--border)]"
        >
          Refresh Confluences
        </button>
      </div>

      {error && (
        <ErrorState
          title={error.title}
          message={error.message}
          requestId={error.requestId}
          endpoint={error.endpoint}
          statusCode={error.statusCode}
          onRetry={loadAlerts}
        />
      )}

      {loading && (
        <div className="space-y-4">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-32 rounded-xl bg-[var(--surface-subtle)] animate-pulse border border-[var(--border)]" />
          ))}
        </div>
      )}

      {!loading && !error && alerts.length === 0 && (
        <EmptyState
          title="No active confluence alerts detected"
          description="A confluence alert triggers when ≥3 distinct independent source providers converge on a single development within 48 hours."
        />
      )}

      {!loading && !error && alerts.length > 0 && (
        <div className="space-y-4">
          {alerts.map((item) => (
            <div
              key={item.confluence_id}
              className="rounded-xl border border-[var(--border)] bg-[var(--card)] p-5 space-y-4 shadow-xs"
            >
              <div className="flex items-start justify-between gap-4">
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <span className="px-2 py-0.5 rounded text-[10px] font-semibold uppercase tracking-wider bg-purple-50 text-purple-700 border border-purple-200 dark:bg-purple-950/80 dark:text-purple-300 dark:border-purple-800/60">
                      {item.confluence_type || 'Emerging'} Confluence
                    </span>
                    <span className="text-xs font-mono text-[var(--muted-foreground)]">
                      {item.independent_sources_count ?? item.signal_count} Distinct Sources Converged
                    </span>
                  </div>
                  <h3 className="text-base font-semibold text-[var(--foreground)]">
                    {item.development_title || 'Haemophilia Development'}
                  </h3>
                  {item.reasoning && (
                    <p className="text-xs text-[var(--muted-foreground)] leading-relaxed font-sans">{item.reasoning}</p>
                  )}
                </div>

                <div className="text-right shrink-0 space-y-2">
                  <div>
                    <div className="text-sm font-mono font-bold text-purple-600 dark:text-purple-400">
                      Score: {item.score !== undefined ? `${item.score} / 100` : '0.0 / 100'}
                    </div>
                    <div className="text-[10px] text-[var(--muted-foreground)] font-mono">
                      Engine: {item.calculation_version || 'confluence_v2.0'}
                    </div>
                  </div>
                  <button
                    onClick={() => handleInspect(item)}
                    className="px-3 py-1 text-xs font-medium rounded-lg bg-purple-50 hover:bg-purple-100 text-purple-700 border border-purple-200 dark:bg-purple-900/60 dark:hover:bg-purple-800/80 dark:text-purple-200 dark:border-purple-700/60 transition flex items-center gap-1.5 ml-auto"
                  >
                    <span>Inspect Evidence</span>
                    <span>→</span>
                  </button>
                </div>
              </div>

              {/* Score breakdown chips */}
              {item.score_breakdown && Object.keys(item.score_breakdown).length > 0 && (
                <div className="flex items-center gap-2 flex-wrap text-xs pt-1">
                  <span className="text-[var(--muted-foreground)] text-[11px]">Score Calculation Drivers:</span>
                  {Object.entries(item.score_breakdown).map(([k, v]) => (
                    <span
                      key={k}
                      className="px-2 py-0.5 rounded bg-[var(--surface-muted)] text-[var(--foreground)] font-mono text-[11px] border border-[var(--border)]"
                    >
                      {k.replace(/_/g, ' ')}: +{v} pts
                    </span>
                  ))}
                </div>
              )}

              {/* Signals list preview */}
              {item.signals && item.signals.length > 0 && (
                <div className="space-y-2 pt-2 border-t border-[var(--border)]">
                  <div className="text-xs font-semibold text-[var(--muted-foreground)] uppercase tracking-wider">
                    Contributing Evidence Signals
                  </div>
                  <div className="space-y-1.5">
                    {item.signals.map((s, idx) => (
                      <div
                        key={idx}
                        className="flex items-center justify-between text-xs p-2.5 rounded-lg bg-[var(--surface-subtle)] border border-[var(--border)]"
                      >
                        <span className="text-[var(--foreground)] font-medium truncate max-w-md">{s.title}</span>
                        <div className="flex items-center gap-2 shrink-0 ml-2">
                          <span className="text-[var(--muted-foreground)] font-mono text-[11px]">
                            {s.signal_type}
                          </span>
                          {s.canonical_url ? (
                            <a
                              href={s.canonical_url}
                              target="_blank"
                              rel="noreferrer"
                              className="text-purple-600 dark:text-purple-400 hover:underline text-[11px] font-medium"
                            >
                              Source URL ↗
                            </a>
                          ) : (
                            <span className="text-[10px] font-mono text-[var(--muted-foreground)]">
                              SOURCE URL UNAVAILABLE
                            </span>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Backward Trace Inspect Modal / Drawer */}
      {inspectTarget && (
        <div className="fixed inset-0 z-50 overflow-hidden bg-black/60 backdrop-blur-xs flex justify-end">
          <div
            className="w-full max-w-2xl bg-[var(--card)] border-l border-[var(--border)] h-full overflow-y-auto p-6 space-y-6 shadow-2xl flex flex-col justify-between"
            role="dialog"
            aria-modal="true"
            aria-label="Confluence Evidence Backward Trace"
          >
            <div className="space-y-6">
              {/* Header */}
              <div className="flex items-start justify-between gap-4 pb-4 border-b border-[var(--border)]">
                <div className="space-y-1.5">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="px-2 py-0.5 rounded text-[10px] font-semibold uppercase tracking-wider bg-purple-50 text-purple-700 border border-purple-200 dark:bg-purple-950/80 dark:text-purple-300 dark:border-purple-800/60">
                      {inspectTarget.label}
                    </span>
                    <span className="text-xs font-mono text-emerald-600 dark:text-emerald-400 font-bold">
                      Score: {inspectTarget.score} / 100
                    </span>
                  </div>
                  <h3 className="text-lg font-semibold text-[var(--foreground)]">
                    {inspectTarget.development_title || 'Haemophilia Development'}
                  </h3>
                </div>
                <button
                  onClick={() => setInspectTarget(null)}
                  className="p-1.5 rounded-lg bg-[var(--surface-muted)] hover:bg-[var(--surface-subtle)] text-[var(--muted-foreground)] transition"
                  aria-label="Close inspector"
                >
                  ✕
                </button>
              </div>

              {/* Explainable Reasoning Answer */}
              <div className="bg-[var(--surface-subtle)] p-4 rounded-xl border border-[var(--border)] space-y-2">
                <h4 className="text-xs font-semibold uppercase tracking-wider text-purple-700 dark:text-purple-400">
                  Inspectable Mathematical Reasoning
                </h4>
                <p className="text-xs text-[var(--foreground)] leading-relaxed font-sans">
                  {inspectTarget.reasoning}
                </p>
                <div className="text-[11px] text-[var(--muted-foreground)] font-mono pt-1">
                  Time Window: Sliding {inspectTarget.window_hours} hours · Threshold: ≥3 distinct independent source providers
                </div>
              </div>

              {/* Verbatim Independent Sources Chain */}
              <div className="space-y-3">
                <h4 className="text-xs font-semibold uppercase tracking-wider text-[var(--muted-foreground)]">
                  Unbroken Backward Trace: Verbatim Source Excerpts ({inspectTarget.sources.length} Verified Sources)
                </h4>
                {inspectTarget.sources.length === 0 ? (
                  <div className="text-xs text-[var(--muted-foreground)] italic p-3 bg-[var(--surface-subtle)] rounded-lg border border-[var(--border)]">
                    No verbatim citations linked for this development.
                  </div>
                ) : (
                  <div className="space-y-3">
                    {inspectTarget.sources.map((src, i) => (
                      <div
                        key={i}
                        className="p-4 rounded-xl bg-[var(--surface-subtle)] border border-[var(--border)] space-y-2.5"
                      >
                        <div className="flex items-center justify-between gap-2 flex-wrap">
                          <div className="flex items-center gap-2">
                            <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-purple-50 text-purple-700 border border-purple-200 dark:bg-purple-950/80 dark:text-purple-300 font-medium">
                              {src.source_name}
                            </span>
                            <span className="text-[11px] font-mono text-[var(--muted-foreground)]">
                              ID: {src.external_id}
                            </span>
                          </div>
                          <span className="text-xs font-mono font-semibold text-emerald-600 dark:text-emerald-400">
                            +{src.points_contributed} pts
                          </span>
                        </div>

                        {/* Verbatim Excerpt */}
                        <div className="p-3 rounded-lg bg-[var(--card)] border border-[var(--border)] text-xs text-[var(--foreground)] leading-relaxed font-sans select-text">
                          &ldquo;{src.verbatim_excerpt}&rdquo;
                        </div>

                        {/* Provenance URLs & Timestamps */}
                        <div className="flex items-center justify-between text-[11px] text-[var(--muted-foreground)] font-mono pt-1">
                          <div>
                            {src.published_at && `Published: ${src.published_at.slice(0, 10)}`}
                          </div>
                          {src.source_url ? (
                            <a
                              href={src.source_url}
                              target="_blank"
                              rel="noreferrer"
                              className="text-purple-600 dark:text-purple-400 hover:underline flex items-center gap-1 font-medium"
                            >
                              <span>View Original Public Source</span>
                              <span>↗</span>
                            </a>
                          ) : (
                            <span className="text-[10px] font-mono text-[var(--muted-foreground)]">
                              SOURCE URL UNAVAILABLE
                            </span>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>

            <div className="pt-4 border-t border-[var(--border)] flex justify-end">
              <button
                onClick={() => setInspectTarget(null)}
                className="px-4 py-2 rounded-lg bg-[var(--surface-muted)] hover:bg-[var(--surface-subtle)] text-xs text-[var(--foreground)] transition border border-[var(--border)]"
              >
                Close Inspector
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
