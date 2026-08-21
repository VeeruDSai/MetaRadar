'use client'

import React, { useState, useEffect, useCallback } from 'react'
import type { ActivityLogItem } from '@/types/api'
import { fetchActivityLogs } from '@/lib/api'
import { formatError, FormattedError } from '@/lib/errors'
import { ErrorState } from '../common/ErrorState'
import { EmptyState } from '../common/EmptyState'

export function ActivityStreamWorkspace() {
  const [logs, setLogs] = useState<ActivityLogItem[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<FormattedError | null>(null)
  const [expandedId, setExpandedId] = useState<string | null>(null)
  const [levelFilter, setLevelFilter] = useState<string>('')

  const loadLogs = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await fetchActivityLogs(100)
      setLogs(data)
    } catch (err) {
      setError(formatError(err, 'Failed to fetch activity stream telemetry.'))
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    loadLogs()
  }, [loadLogs])

  const filteredLogs = levelFilter ? logs.filter((l) => l.level === levelFilter) : logs

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <div className="text-[11px] font-semibold tracking-wider uppercase text-[var(--muted-foreground)] mb-0.5">
            Audit Trail & Diagnostic Stream
          </div>
          <h2 className="text-xl font-bold text-[var(--foreground)]">System Activity & Observability Stream</h2>
          <p className="text-xs text-[var(--muted-foreground)] mt-1">
            End-to-end structured JSON telemetry, correlation tracing (X-Request-ID), and pipeline execution logs.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <select
            value={levelFilter}
            onChange={(e) => setLevelFilter(e.target.value)}
            className="px-3 py-1.5 rounded-lg bg-[var(--card)] border border-[var(--border)] text-xs text-[var(--foreground)]"
          >
            <option value="">All Log Levels</option>
            <option value="INFO">INFO</option>
            <option value="WARNING">WARNING</option>
            <option value="ERROR">ERROR</option>
          </select>

          <button
            onClick={loadLogs}
            className="px-3.5 py-1.5 rounded-lg bg-[var(--surface-muted)] hover:bg-[var(--surface-subtle)] text-xs text-[var(--foreground)] transition border border-[var(--border)]"
          >
            Refresh Stream
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
          onRetry={loadLogs}
        />
      )}

      {loading && (
        <div className="space-y-3">
          {[1, 2, 3, 4, 5].map((i) => (
            <div key={i} className="h-16 rounded-xl bg-[var(--surface-subtle)] animate-pulse border border-[var(--border)]" />
          ))}
        </div>
      )}

      {!loading && !error && filteredLogs.length === 0 && (
        <EmptyState
          title="No activity events found"
          description="System events and connector runs will appear here as the platform processes pipeline workloads."
        />
      )}

      {!loading && !error && filteredLogs.length > 0 && (
        <div className="space-y-2">
          {filteredLogs.map((log) => {
            const isExpanded = expandedId === log.id
            const isError = log.level === 'ERROR'
            const isWarn = log.level === 'WARNING'

            return (
              <div
                key={log.id}
                className={`rounded-xl border p-4 space-y-2 transition ${
                  isError
                    ? 'border-red-200 bg-red-50/50 dark:border-red-800/40 dark:bg-red-950/20'
                    : isWarn
                    ? 'border-amber-200 bg-amber-50/50 dark:border-amber-800/40 dark:bg-amber-950/20'
                    : 'border-[var(--border)] bg-[var(--card)] shadow-xs'
                }`}
              >
                <div
                  className="flex items-start justify-between gap-3 cursor-pointer select-none"
                  onClick={() => setExpandedId(isExpanded ? null : log.id)}
                >
                  <div className="flex items-center gap-2.5 flex-wrap">
                    <span
                      className={`px-2 py-0.5 rounded text-[10px] font-mono font-semibold uppercase tracking-wider ${
                        isError
                          ? 'bg-red-100 text-red-700 border border-red-200 dark:bg-red-950 dark:text-red-300 dark:border-red-800'
                          : isWarn
                          ? 'bg-amber-100 text-amber-700 border border-amber-200 dark:bg-amber-950 dark:text-amber-300 dark:border-amber-800'
                          : 'bg-[var(--surface-subtle)] text-[var(--foreground)] border border-[var(--border)]'
                      }`}
                    >
                      {log.level}
                    </span>
                    <span className="text-xs font-mono font-semibold text-[var(--foreground)]">
                      {log.service} :: {log.component}
                    </span>
                    <span className="text-xs text-[var(--muted-foreground)] font-mono text-[11px]">
                      {new Date(log.timestamp).toLocaleTimeString()}
                    </span>
                  </div>

                  <div className="flex items-center gap-3 shrink-0">
                    {log.duration_ms !== null && log.duration_ms !== undefined && (
                      <span className="text-[11px] font-mono text-[var(--muted-foreground)]">
                        {log.duration_ms} ms
                      </span>
                    )}
                    <span className="text-xs text-[var(--muted-foreground)]">
                      {isExpanded ? '▲' : '▼'}
                    </span>
                  </div>
                </div>

                <p className="text-xs text-[var(--foreground)] leading-relaxed font-sans">
                  {log.message}
                </p>

                {/* Expanded Technical Diagnostics */}
                {isExpanded && (
                  <div className="pt-2 border-t border-[var(--border)] space-y-2 text-xs font-mono">
                    <div className="grid grid-cols-2 gap-2 text-[var(--muted-foreground)] text-[11px]">
                      <div>Event: <span className="text-[var(--foreground)]">{log.event}</span></div>
                      <div>Status: <span className="text-[var(--foreground)]">{log.status}</span></div>
                      {log.request_id && (
                        <div>Request ID: <span className="text-[var(--foreground)]">{log.request_id}</span></div>
                      )}
                      {log.pipeline_run_id && (
                        <div>Pipeline Run: <span className="text-[var(--foreground)]">{log.pipeline_run_id}</span></div>
                      )}
                    </div>

                    {log.details && (
                      <pre className="p-3 rounded-lg bg-[var(--surface-subtle)] border border-[var(--border)] text-[11px] text-[var(--foreground)] overflow-x-auto">
                        {JSON.stringify(log.details, null, 2)}
                      </pre>
                    )}
                  </div>
                )}
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
