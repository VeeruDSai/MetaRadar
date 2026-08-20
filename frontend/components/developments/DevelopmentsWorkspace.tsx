'use client'

import React, { useState, useEffect, useCallback } from 'react'
import type { DevelopmentSummary } from '@/types/api'
import { fetchDevelopments } from '@/lib/api'
import { formatError, FormattedError } from '@/lib/errors'
import { ErrorState } from '../common/ErrorState'
import { EmptyState } from '../common/EmptyState'

export function DevelopmentsWorkspace() {
  const [developments, setDevelopments] = useState<DevelopmentSummary[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<FormattedError | null>(null)

  const loadDevelopments = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await fetchDevelopments(50)
      setDevelopments(data)
    } catch (err) {
      setError(formatError(err, 'Failed to fetch clinical developments registry.'))
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    loadDevelopments()
  }, [loadDevelopments])

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-slate-100">Competitive Developments Registry</h1>
          <p className="text-xs text-slate-400 mt-1">
            Canonical disease-area development tracks linking clinical trials, regulatory filings, and competitor milestones.
          </p>
        </div>
        <button
          onClick={loadDevelopments}
          className="px-3.5 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-xs text-slate-200 transition"
        >
          Refresh Registry
        </button>
      </div>

      {error && (
        <ErrorState
          title={error.title}
          message={error.message}
          requestId={error.requestId}
          endpoint={error.endpoint}
          statusCode={error.statusCode}
          onRetry={loadDevelopments}
        />
      )}

      {loading && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="h-32 rounded-xl bg-slate-900/40 animate-pulse border border-slate-800" />
          ))}
        </div>
      )}

      {!loading && !error && developments.length === 0 && (
        <EmptyState
          title="No registered developments found"
          description="Competitive developments are synthesized automatically when new clinical trials or regulatory filings are ingested."
        />
      )}

      {!loading && !error && developments.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {developments.map((d) => (
            <div
              key={d.development_id}
              className="rounded-xl border border-slate-800 bg-slate-900/60 p-5 space-y-3 shadow-sm hover:border-slate-700 transition"
            >
              <div className="flex items-start justify-between gap-3">
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <span className="px-2 py-0.5 rounded text-[10px] font-semibold uppercase tracking-wider bg-blue-950/80 text-blue-300 border border-blue-800/60">
                      Stage: {d.current_stage || 'Announced'}
                    </span>
                    <span className="text-xs font-mono text-slate-400">
                      {d.disease || 'Haemophilia'}
                    </span>
                  </div>
                  <h3 className="text-base font-semibold text-slate-200">{d.title}</h3>
                </div>

                <div className="text-right shrink-0">
                  <span className="px-2 py-0.5 rounded-full text-xs font-mono bg-slate-800 text-slate-300">
                    {d.signal_count} signals
                  </span>
                </div>
              </div>

              <div className="flex items-center justify-between pt-2 border-t border-slate-800/60 text-xs text-slate-400">
                <div>Asset: <span className="text-slate-200 font-medium">{d.asset_name || 'N/A'}</span></div>
                <div>Sponsor: <span className="text-slate-200 font-medium">{d.company_name || 'Competitor'}</span></div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
