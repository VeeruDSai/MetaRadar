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
        return 'bg-red-950/80 text-red-300 border-red-800/80'
      case 'DUE':
        return 'bg-amber-950/80 text-amber-300 border-amber-800/80'
      case 'WITHIN_WINDOW':
        return 'bg-blue-950/80 text-blue-300 border-blue-800/80'
      case 'SATISFIED':
        return 'bg-emerald-950/80 text-emerald-300 border-emerald-800/80'
      case 'SUPPRESSED':
        return 'bg-slate-800 text-slate-400 border-slate-700'
      default:
        return 'bg-slate-900 text-slate-300 border-slate-800'
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-slate-100">Missing Signal Watch Engine</h1>
          <p className="text-xs text-slate-400 mt-1">
            Proactive monitoring for expected regulatory or clinical events that have not yet materialized within their expected time windows.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-800 text-xs text-slate-200"
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
            className="px-3.5 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-xs text-slate-200 transition"
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
            <div key={i} className="h-32 rounded-xl bg-slate-900/40 animate-pulse border border-slate-800" />
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
              className="rounded-xl border border-slate-800 bg-slate-900/60 p-5 space-y-3 shadow-sm"
            >
              <div className="flex items-start justify-between gap-4">
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <span className={`px-2 py-0.5 rounded text-[10px] font-semibold uppercase tracking-wider border ${getStatusBadge(item.status)}`}>
                      {item.status}
                    </span>
                    <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-slate-800 text-slate-300">
                      {item.responsible_function}
                    </span>
                    {item.days_overdue > 0 && (
                      <span className="text-xs font-mono text-red-400 font-medium">
                        +{item.days_overdue} days overdue
                      </span>
                    )}
                  </div>
                  <h3 className="text-sm font-semibold text-slate-200">
                    {item.development_title || 'Portfolio Monitoring Asset'}
                  </h3>
                </div>

                <div className="text-right shrink-0">
                  <div className="text-xs font-mono font-semibold text-slate-300">
                    Window: {item.monitoring_window_days} days
                  </div>
                  <div className="text-[10px] text-slate-500">
                    Overdue Heuristic: {item.overdue_heuristic_score !== undefined ? `${Math.round(item.overdue_heuristic_score * 100)}%` : `${Math.round(item.confidence * 100)}%`}
                  </div>
                </div>
              </div>

              {/* Trigger vs Expected Event description */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-2 text-xs">
                <div className="p-3 rounded-lg bg-slate-950/60 border border-slate-800">
                  <div className="text-[10px] font-semibold uppercase text-slate-500 mb-1">Observed Trigger Event</div>
                  <div className="text-slate-300">{item.trigger_event}</div>
                </div>
                <div className="p-3 rounded-lg bg-slate-950/60 border border-slate-800">
                  <div className="text-[10px] font-semibold uppercase text-amber-400 mb-1">Expected Milestone Event</div>
                  <div className="text-slate-300 font-medium">{item.expected_event}</div>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
