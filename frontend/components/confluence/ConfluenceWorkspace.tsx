'use client'

import React, { useState, useEffect, useCallback } from 'react'
import type { ConfluenceAlertItem } from '@/types/api'
import { fetchConfluenceAlerts } from '@/lib/api'
import { formatError, FormattedError } from '@/lib/errors'
import { ErrorState } from '../common/ErrorState'
import { EmptyState } from '../common/EmptyState'

export function ConfluenceWorkspace() {
  const [alerts, setAlerts] = useState<ConfluenceAlertItem[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<FormattedError | null>(null)

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

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-slate-100">Multi-Source Confluence Alerts</h1>
          <p className="text-xs text-slate-400 mt-1">
            Independent signals converging on the same development within a 48-hour window (≥3 source types).
          </p>
        </div>
        <button
          onClick={loadAlerts}
          className="px-3.5 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-xs text-slate-200 transition"
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
            <div key={i} className="h-32 rounded-xl bg-slate-900/40 animate-pulse border border-slate-800" />
          ))}
        </div>
      )}

      {!loading && !error && alerts.length === 0 && (
        <EmptyState
          title="No active confluence alerts detected"
          description="A confluence alert triggers when ≥3 independent signal types converge on a single development within 48 hours."
        />
      )}

      {!loading && !error && alerts.length > 0 && (
        <div className="space-y-4">
          {alerts.map((item) => (
            <div
              key={item.confluence_id}
              className="rounded-xl border border-slate-800 bg-slate-900/60 p-5 space-y-4 shadow-sm"
            >
              <div className="flex items-start justify-between gap-4">
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <span className="px-2 py-0.5 rounded text-[10px] font-semibold uppercase tracking-wider bg-purple-950/80 text-purple-300 border border-purple-800/60">
                      {item.confluence_type || 'Emerging'} Confluence
                    </span>
                    <span className="text-xs font-mono text-slate-400">
                      {item.independent_sources_count || item.signal_count} Sources Converged
                    </span>
                  </div>
                  <h3 className="text-base font-semibold text-slate-200">
                    {item.development_title || 'Haemophilia Development'}
                  </h3>
                </div>

                <div className="text-right shrink-0">
                  <div className="text-sm font-mono font-bold text-purple-400">
                    Score: {item.score !== undefined ? `${item.score} / 100` : '75.0'}
                  </div>
                  <div className="text-[10px] text-slate-500 font-mono">
                    Engine: {item.calculation_version || 'confluence_v2.0'}
                  </div>
                </div>
              </div>

              {/* Score breakdown chips */}
              {item.score_breakdown && Object.keys(item.score_breakdown).length > 0 && (
                <div className="flex items-center gap-2 flex-wrap text-xs">
                  <span className="text-slate-500 text-[11px]">Drivers:</span>
                  {Object.entries(item.score_breakdown).map(([k, v]) => (
                    <span
                      key={k}
                      className="px-2 py-0.5 rounded bg-slate-800 text-slate-300 font-mono text-[11px]"
                    >
                      {k.replace(/_/g, ' ')}: +{v} pts
                    </span>
                  ))}
                </div>
              )}

              {/* Signals list preview */}
              {item.signals && item.signals.length > 0 && (
                <div className="space-y-2 pt-2 border-t border-slate-800/60">
                  <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
                    Contributing Evidence Signals
                  </div>
                  <div className="space-y-1.5">
                    {item.signals.map((s, idx) => (
                      <div
                        key={idx}
                        className="flex items-center justify-between text-xs p-2 rounded-lg bg-slate-950/40 border border-slate-800/40"
                      >
                        <span className="text-slate-300 font-medium truncate max-w-md">{s.title}</span>
                        <span className="text-slate-500 font-mono text-[11px] shrink-0 ml-2">
                          {s.signal_type}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
