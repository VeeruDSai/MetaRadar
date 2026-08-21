'use client'

import React, { useState, useEffect, useCallback } from 'react'
import type { MissingSignalWatchItem } from '@/types/api'
import { fetchMissingSignals } from '@/lib/api'
import { formatError, FormattedError } from '@/lib/errors'
import { ErrorState } from '../common/ErrorState'
import { EmptyState } from '../common/EmptyState'

export function MissingSignalsWorkspace() {
  const [items, setItems] = useState<MissingSignalWatchItem[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<FormattedError | null>(null)
  const [statusFilter, setStatusFilter] = useState<string>('')

  const loadMissingSignals = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await fetchMissingSignals(statusFilter || undefined, 50)
      setItems(data)
    } catch (err) {
      setError(formatError(err, 'Failed to fetch missing signal watch items.'))
    } finally {
      setLoading(false)
    }
  }, [statusFilter])

  useEffect(() => {
    loadMissingSignals()
  }, [loadMissingSignals])

  const getStatusBadge = (status: string) => {
    switch (status.toUpperCase()) {
      case 'OVERDUE':
        return 'bg-red-50 text-red-700 border-red-200 dark:bg-red-950/80 dark:text-red-300 dark:border-red-800/80'
      case 'DUE':
        return 'bg-amber-50 text-amber-700 border-amber-200 dark:bg-amber-950/80 dark:text-amber-300 dark:border-amber-800/80'
      case 'WITHIN_WINDOW':
        return 'bg-blue-50 text-blue-700 border-blue-200 dark:bg-blue-950/80 dark:text-blue-300 dark:border-blue-800/80'
      case 'SATISFIED':
        return 'bg-emerald-50 text-emerald-700 border-emerald-200 dark:bg-emerald-950/80 dark:text-emerald-300 dark:border-emerald-800/80'
      case 'SUPPRESSED':
        return 'bg-[var(--surface-muted)] text-[var(--muted-foreground)] border-[var(--border)]'
      default:
        return 'bg-[var(--surface-subtle)] text-[var(--foreground)] border-[var(--border)]'
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <div className="text-[11px] font-semibold tracking-wider uppercase text-[var(--muted-foreground)] mb-0.5">
            Expected Event Horizon & Horizon Scan
          </div>
          <h2 className="text-xl font-bold text-[var(--foreground)]">Missing Signal Watch Engine</h2>
          <p className="text-xs text-[var(--muted-foreground)] mt-1">
            Proactive monitoring for expected regulatory or clinical events that have not yet materialized within their expected time windows.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="px-3 py-1.5 rounded-lg bg-[var(--card)] border border-[var(--border)] text-xs text-[var(--foreground)]"
          >
            <option value="">All Watch States</option>
            <option value="OVERDUE">Overdue</option>
            <option value="DUE">Due Soon</option>
            <option value="WITHIN_WINDOW">Within Window</option>
            <option value="SATISFIED">Satisfied</option>
            <option value="SUPPRESSED">Suppressed</option>
          </select>

          <button
            onClick={loadMissingSignals}
            className="px-3.5 py-1.5 rounded-lg bg-[var(--surface-muted)] hover:bg-[var(--surface-subtle)] text-xs text-[var(--foreground)] transition border border-[var(--border)]"
          >
            Refresh
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
          onRetry={loadMissingSignals}
        />
      )}

      {loading && (
        <div className="space-y-4">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-32 rounded-xl bg-[var(--surface-subtle)] animate-pulse border border-[var(--border)]" />
          ))}
        </div>
      )}

      {!loading && !error && items.length === 0 && (
        <EmptyState
          title="No watch items match the current filter"
          description="Watch items track expected milestone events (e.g. 180-day Phase III readout following trial completion)."
        />
      )}

      {!loading && !error && items.length > 0 && (
        <div className="space-y-4">
          {items.map((item) => (
            <div
              key={item.watch_id}
              className="rounded-xl border border-[var(--border)] bg-[var(--card)] p-5 space-y-3 shadow-xs"
            >
              <div className="flex items-start justify-between gap-4">
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <span className={`px-2 py-0.5 rounded text-[10px] font-semibold uppercase tracking-wider border ${getStatusBadge(item.status)}`}>
                      {item.status}
                    </span>
                    <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-[var(--surface-subtle)] text-[var(--foreground)] border border-[var(--border)]">
                      {item.responsible_function}
                    </span>
                    {item.days_overdue > 0 && (
                      <span className="text-xs font-mono text-red-600 dark:text-red-400 font-semibold">
                        +{item.days_overdue} days overdue
                      </span>
                    )}
                  </div>
                  <h3 className="text-sm font-semibold text-[var(--foreground)]">
                    {item.development_title || 'Portfolio Monitoring Asset'}
                  </h3>
                </div>

                <div className="text-right shrink-0">
                  <div className="text-xs font-mono font-semibold text-[var(--foreground)]">
                    Window: {item.monitoring_window_days} days
                  </div>
                  <div className="text-[10px] text-[var(--muted-foreground)] font-mono">
                    Overdue Heuristic: {item.overdue_heuristic_score !== undefined ? `${Math.round(item.overdue_heuristic_score * 100)}%` : `${Math.round(item.confidence * 100)}%`}
                  </div>
                </div>
              </div>

              {/* Trigger vs Expected Event description */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-2 text-xs">
                <div className="p-3 rounded-lg bg-[var(--surface-subtle)] border border-[var(--border)]">
                  <div className="text-[10px] font-semibold uppercase text-[var(--muted-foreground)] mb-1">Observed Trigger Event</div>
                  <div className="text-[var(--foreground)]">{item.trigger_event}</div>
                </div>
                <div className="p-3 rounded-lg bg-amber-50/50 dark:bg-amber-950/20 border border-amber-200 dark:border-amber-900/40">
                  <div className="text-[10px] font-semibold uppercase text-amber-700 dark:text-amber-400 mb-1">Expected Milestone Event</div>
                  <div className="text-[var(--foreground)] font-medium">{item.expected_event}</div>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
