'use client'

import React, { useState, useEffect, useCallback } from 'react'
import type { ContradictionItem } from '@/types/api'
import { fetchRedTeamContradictions } from '@/lib/api'
import { formatError, FormattedError } from '@/lib/errors'
import { ErrorState } from '../common/ErrorState'
import { EmptyState } from '../common/EmptyState'

export function ContradictionWorkspace() {
  const [contradictions, setContradictions] = useState<ContradictionItem[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<FormattedError | null>(null)
  const [severityFilter, setSeverityFilter] = useState<string>('')

  const loadContradictions = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await fetchRedTeamContradictions(severityFilter || undefined, 50)
      setContradictions(data)
    } catch (err) {
      setError(formatError(err, 'Failed to fetch Red-Team contradiction alerts.'))
    } finally {
      setLoading(false)
    }
  }, [severityFilter])

  useEffect(() => {
    loadContradictions()
  }, [loadContradictions])

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-slate-100">Red-Team Contradiction Engine</h1>
          <p className="text-xs text-slate-400 mt-1">
            Pairwise contradiction alerts detecting conflicting claims, divergent clinical trial readouts, or regulatory reversals.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <select
            value={severityFilter}
            onChange={(e) => setSeverityFilter(e.target.value)}
            className="px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-800 text-xs text-slate-200"
          >
            <option value="">All Severities</option>
            <option value="CRITICAL">Critical</option>
            <option value="HIGH">High</option>
            <option value="MEDIUM">Medium</option>
          </select>

          <button
            onClick={loadContradictions}
            className="px-3.5 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-xs text-slate-200 transition"
          >
            Refresh Alerts
          </button>
        </div>
      </div>

      {error && (
        <ErrorState
          title={error.title}
          message={error.message}
          requestId={error.requestId}
          endpoint={error.endpoint}
          statusCode={error.statusCode}
          onRetry={loadContradictions}
        />
      )}

      {loading && (
        <div className="space-y-4">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-40 rounded-xl bg-slate-900/40 animate-pulse border border-slate-800" />
          ))}
        </div>
      )}

      {!loading && !error && contradictions.length === 0 && (
        <EmptyState
          title="No active contradictions detected"
          description="The Red-Team engine continuously compares incoming evidence against prior claims to flag semantic divergences."
        />
      )}

      {!loading && !error && contradictions.length > 0 && (
        <div className="space-y-4">
          {contradictions.map((c) => (
            <div
              key={c.contradiction_id}
              className="rounded-xl border border-red-900/30 bg-slate-900/60 p-5 space-y-4 shadow-sm"
            >
              <div className="flex items-start justify-between gap-4">
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <span className="px-2 py-0.5 rounded text-[10px] font-semibold uppercase tracking-wider bg-red-950 text-red-300 border border-red-800/60">
                      {c.severity} Severity
                    </span>
                    <span className="text-xs font-mono text-slate-400">
                      Rule: {c.rule_name || c.rule_id}
                    </span>
                    <span className="text-xs text-slate-500">
                      NLI Confidence: {Math.round(c.confidence * 100)}%
                    </span>
                  </div>
                  <h3 className="text-sm font-semibold text-slate-200">{c.description}</h3>
                </div>
              </div>

              {/* Side-by-Side Verbatim Evidence Excerpts */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3 pt-2">
                <div className="p-3.5 rounded-lg bg-slate-950/70 border border-slate-800 space-y-1.5">
                  <div className="flex items-center justify-between text-[11px] font-semibold text-slate-400 uppercase">
                    <span>Claim A (Primary Ingestion)</span>
                    <span className="font-mono text-slate-500">ID: {c.claim_a_id}</span>
                  </div>
                  <p className="text-xs text-slate-300 leading-relaxed select-text font-mono">
                    {c.claim_a_excerpt || 'Evidence excerpt recorded in bronze stream.'}
                  </p>
                </div>

                <div className="p-3.5 rounded-lg bg-slate-950/70 border border-red-900/40 space-y-1.5">
                  <div className="flex items-center justify-between text-[11px] font-semibold text-red-400 uppercase">
                    <span>Claim B (Contradicting Stream)</span>
                    <span className="font-mono text-slate-500">ID: {c.claim_b_id}</span>
                  </div>
                  <p className="text-xs text-slate-300 leading-relaxed select-text font-mono">
                    {c.claim_b_excerpt || 'Contradicting evidence excerpt recorded in bronze stream.'}
                  </p>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
