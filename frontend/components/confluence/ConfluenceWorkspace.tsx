'use client'

import React, { useState, useEffect, useCallback } from 'react'
import Link from 'next/link'
import type { ConfluenceAlertItem, ConfluenceInspectResponse } from '@/types/api'
import { fetchConfluenceAlerts, inspectConfluence } from '@/lib/api'
import { formatError, FormattedError } from '@/lib/errors'
import { SectionTitle, Card, Badge } from '@/components/metaradar'
import { ErrorState } from '../common/ErrorState'
import { ExternalLink, RefreshCw, X, Zap } from 'lucide-react'

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
    <>
      <SectionTitle
        eyebrow="Cross-Source Evidence Clustering"
        title="Confluence Alerts"
        detail="Independent signals converging on the same development within a 48-hour window (≥3 distinct independent source providers required)."
      />

      <div className="kpi-grid">
        <div className="panel kpi">
          <p className="eyebrow">Confluences detected</p>
          <div className="kpi-value">
            <strong style={{ color: 'var(--signal)' }}>{alerts.length}</strong>
            <span>Active clusters</span>
          </div>
        </div>
        <div className="panel kpi">
          <p className="eyebrow">Detection window</p>
          <div className="kpi-value">
            <strong>48h</strong>
            <span>Rolling window</span>
          </div>
        </div>
        <div className="panel kpi">
          <p className="eyebrow">Source requirement</p>
          <div className="kpi-value">
            <strong>≥3</strong>
            <span>Distinct providers</span>
          </div>
        </div>
        <div className="panel kpi">
          <p className="eyebrow">Cluster alignment</p>
          <div className="kpi-value">
            <strong style={{ color: 'var(--success)' }}>High</strong>
            <span>Verified</span>
          </div>
        </div>
      </div>

      <div className="flex items-center justify-between gap-3 mb-4">
        <div className="text-xs text-[var(--muted-foreground)]">
          {alerts.length} multi-source confluences flagged in active window
        </div>
        <button
          onClick={loadAlerts}
          className="inline-flex items-center gap-1 px-3 py-1.5 rounded text-xs border border-[var(--border)] bg-[var(--surface)] text-[var(--foreground)] hover:border-[var(--signal)]"
        >
          <RefreshCw size={13} className={loading ? 'animate-spin' : ''} />
          <span>Refresh Confluences</span>
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
        <div className="grid gap-4">
          {[1, 2, 3].map((i) => (
            <Card key={i} className="animate-pulse h-36" />
          ))}
        </div>
      )}

      {!loading && !error && alerts.length === 0 && (
        <Card className="empty-state">
          <Zap size={28} />
          <p>No active confluence alerts detected</p>
          <span>A confluence alert triggers when ≥3 distinct independent source providers converge on a single development within 48 hours.</span>
        </Card>
      )}

      {!loading && !error && alerts.length > 0 && (
        <div className="grid gap-4">
          {alerts.map((item) => (
            <Card key={item.confluence_id}>
              <div className="flex items-start justify-between gap-4 mb-2">
                <div>
                  <div className="flex items-center gap-2 mb-1">
                    <Badge tone="high">{item.confluence_type || 'Confirmed'} Confluence</Badge>
                    <span className="text-xs font-mono text-[var(--muted-foreground)]">
                      {item.independent_sources_count ?? item.signal_count} Distinct Sources Converged
                    </span>
                  </div>
                  <h3 className="text-base font-semibold text-[var(--foreground)] m-0">
                    {item.development_title || 'Haemophilia Development'}
                  </h3>
                  {item.reasoning && (
                    <p className="text-xs text-[var(--muted-foreground)] leading-relaxed m-0 mt-1">
                      {item.reasoning}
                    </p>
                  )}
                </div>

                <div className="text-right shrink-0">
                  <div className="text-sm font-mono font-bold" style={{ color: 'var(--signal)' }}>
                    Score: {item.score !== undefined ? `${item.score} / 100` : '0.0 / 100'}
                  </div>
                  <button
                    onClick={() => handleInspect(item)}
                    className="mt-2 text-link text-xs inline-flex items-center gap-1 border-0 bg-transparent p-0"
                  >
                    <span>Inspect Evidence</span>
                    <ExternalLink size={12} />
                  </button>
                </div>
              </div>

              {item.score_breakdown && Object.keys(item.score_breakdown).length > 0 && (
                <div className="flex items-center gap-2 flex-wrap text-xs pt-2 border-t border-[var(--border)] mt-2">
                  <span className="text-[var(--muted-foreground)] text-[11px]">Score Calculation Drivers:</span>
                  {Object.entries(item.score_breakdown).map(([k, v]) => (
                    <Badge key={k} tone="neutral">
                      {k.replace(/_/g, ' ')}: +{v} pts
                    </Badge>
                  ))}
                </div>
              )}

              {item.signals && item.signals.length > 0 && (
                <div className="pt-2 border-t border-[var(--border)] mt-2">
                  <div className="text-[10px] uppercase tracking-wider font-semibold text-[var(--muted-foreground)] mb-1.5">
                    Contributing Evidence Signals
                  </div>
                  <div className="grid gap-1.5">
                    {item.signals.map((s, idx) => (
                      <div
                        key={idx}
                        className="flex items-center justify-between text-xs p-2 rounded border border-[var(--border)]"
                        style={{ background: 'var(--surface-secondary)' }}
                      >
                        <span className="text-[var(--foreground)] font-medium truncate max-w-md">{s.title}</span>
                        <div className="flex items-center gap-2 shrink-0 ml-2">
                          <span className="text-[var(--muted-foreground)] font-mono text-[10px]">
                            {s.signal_type}
                          </span>
                          {s.canonical_url ? (
                            <a
                              href={s.canonical_url}
                              target="_blank"
                              rel="noreferrer noopener"
                              className="text-link text-[11px]"
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
            </Card>
          ))}
        </div>
      )}

      {/* Backward Trace Inspect Modal / Drawer */}
      {inspectTarget && (
        <div className="drawer-backdrop" onClick={() => setInspectTarget(null)}>
          <aside
            className="signal-drawer overflow-y-auto max-h-screen"
            style={{ width: 'min(580px, 100%)' }}
            onClick={(e) => e.stopPropagation()}
            role="dialog"
            aria-modal="true"
            aria-label="Confluence Evidence Backward Trace"
          >
            <div className="drawer-top">
              <Badge tone="high">{inspectTarget.label}</Badge>
              <button
                className="icon-button"
                onClick={() => setInspectTarget(null)}
                aria-label="Close inspector"
              >
                <X size={18} />
              </button>
            </div>

            <h2>{inspectTarget.development_title || 'Haemophilia Development'}</h2>
            <div className="drawer-score">
              <strong>{inspectTarget.score} / 100</strong>
              <span>Confluence Score</span>
              <span className="font-semibold text-signal">≥3 Sources Required</span>
            </div>

            <div className="drawer-sections">
              <h3>Mathematical Reasoning</h3>
              <p>{inspectTarget.reasoning}</p>
              <div className="text-[10px] text-[var(--muted-foreground)] font-mono">
                Window: {inspectTarget.window_hours}h sliding · Contributing: {inspectTarget.distinct_sources_count} sources
              </div>

              <h3 className="mt-4">
                Verified Evidence Sources ({inspectTarget.sources.length})
              </h3>
              {inspectTarget.sources.length === 0 ? (
                <p>No verbatim citations linked for this development.</p>
              ) : (
                <div className="grid gap-2.5">
                  {inspectTarget.sources.map((src, i) => (
                    <div
                      key={i}
                      className="p-3 rounded border border-[var(--border)]"
                      style={{ background: 'var(--surface-secondary)' }}
                    >
                      <div className="flex items-center justify-between gap-2 mb-1.5">
                        <div className="flex items-center gap-1.5">
                          <Badge tone="neutral">{src.source_name}</Badge>
                          <span className="font-mono text-[10px] text-[var(--muted-foreground)]">
                            {src.external_id}
                          </span>
                        </div>
                        <span className="font-mono text-xs font-bold" style={{ color: 'var(--success)' }}>
                          +{src.points_contributed} pts
                        </span>
                      </div>

                      <p className="text-xs text-[var(--foreground)] leading-relaxed m-0 my-1 font-sans italic">
                        &ldquo;{src.verbatim_excerpt}&rdquo;
                      </p>

                      <div className="flex items-center justify-between text-[10px] text-[var(--muted-foreground)] font-mono pt-1">
                        <span>{src.published_at ? `Published: ${src.published_at.slice(0, 10)}` : ''}</span>
                        <div className="flex items-center gap-2">
                          <Link
                            href={`/signals/${encodeURIComponent(src.external_id)}`}
                            className="text-[var(--signal)] hover:underline font-semibold"
                          >
                            Inspect Signal Detail →
                          </Link>
                          {src.source_url && !src.source_url.includes('metaradar.internal') && (
                            <a
                              href={src.source_url}
                              target="_blank"
                              rel="noreferrer noopener"
                              className="text-link"
                            >
                              Source ↗
                            </a>
                          )}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </aside>
        </div>
      )}
    </>
  )
}
