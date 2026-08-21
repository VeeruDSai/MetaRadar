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
          <div className="text-[11px] font-semibold tracking-wider uppercase text-[var(--muted-foreground)] mb-0.5">
            Adversarial Audit & Divergence
          </div>
          <h2 className="text-xl font-bold text-[var(--foreground)]">Red-Team Contradiction Engine</h2>
          <p className="text-xs text-[var(--muted-foreground)] mt-1">
            Pairwise contradiction alerts detecting conflicting claims, divergent clinical trial readouts, or regulatory reversals.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <select
            value={severityFilter}
            onChange={(e) => setSeverityFilter(e.target.value)}
            className="px-3 py-1.5 rounded-lg bg-[var(--card)] border border-[var(--border)] text-xs text-[var(--foreground)]"
          >
            <option value="">All Severities</option>
            <option value="CRITICAL">Critical</option>
            <option value="HIGH">High</option>
            <option value="MEDIUM">Medium</option>
          </select>

          <button
            onClick={loadContradictions}
            className="px-3.5 py-1.5 rounded-lg bg-[var(--surface-muted)] hover:bg-[var(--surface-subtle)] text-xs text-[var(--foreground)] transition border border-[var(--border)]"
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
            <div key={i} className="h-40 rounded-xl bg-[var(--surface-subtle)] animate-pulse border border-[var(--border)]" />
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
              className="rounded-xl border border-red-200 dark:border-red-900/30 bg-[var(--card)] p-5 space-y-4 shadow-xs"
            >
              <div className="flex items-start justify-between gap-4">
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <span className="px-2 py-0.5 rounded text-[10px] font-semibold uppercase tracking-wider bg-red-50 text-red-700 border border-red-200 dark:bg-red-950 dark:text-red-300 dark:border-red-800/60">
                      {c.severity} Severity
                    </span>
                    <span className="text-xs font-mono text-[var(--muted-foreground)]">
                      Rule: {c.rule_name || c.rule_id}
                    </span>
                    <span className="text-xs text-[var(--muted-foreground)] font-mono">
                      NLI Confidence: {Math.round(c.confidence * 100)}%
                    </span>
                  </div>
                  <h3 className="text-sm font-semibold text-[var(--foreground)]">{c.description}</h3>
                </div>
              </div>

              {/* Side-by-Side Verbatim Evidence Excerpts */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3 pt-2">
                <div className="p-3.5 rounded-lg bg-[var(--surface-subtle)] border border-[var(--border)] space-y-1.5">
                  <div className="flex items-center justify-between text-[11px] font-semibold text-[var(--muted-foreground)] uppercase">
                    <span>Claim A (Primary Ingestion)</span>
                    <span className="font-mono text-[var(--muted-foreground)]">ID: {c.claim_a_id}</span>
                  </div>
                  <p className="text-xs text-[var(--foreground)] leading-relaxed select-text font-mono">
                    {c.claim_a_excerpt || 'Evidence excerpt recorded in bronze stream.'}
                  </p>
                </div>

                <div className="p-3.5 rounded-lg bg-red-50/50 dark:bg-red-950/20 border border-red-200 dark:border-red-900/40 space-y-1.5">
                  <div className="flex items-center justify-between text-[11px] font-semibold text-red-700 dark:text-red-400 uppercase">
                    <span>Claim B (Contradicting Stream)</span>
                    <span className="font-mono text-[var(--muted-foreground)]">ID: {c.claim_b_id}</span>
                  </div>
                  <p className="text-xs text-[var(--foreground)] leading-relaxed select-text font-mono">
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
