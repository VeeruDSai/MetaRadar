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
          <h1 className="text-xl font-bold text-slate-100">System Activity & Observability Stream</h1>
          <p className="text-xs text-slate-400 mt-1">
            End-to-end structured JSON telemetry, correlation tracing (X-Request-ID), and pipeline execution logs.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <select
            value={levelFilter}
            onChange={(e) => setLevelFilter(e.target.value)}
            className="px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-800 text-xs text-slate-200"
          >
            <option value="">All Log Levels</option>
            <option value="INFO">INFO</option>
            <option value="WARNING">WARNING</option>
            <option value="ERROR">ERROR</option>
          </select>

          <button
            onClick={loadLogs}
            className="px-3.5 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-xs text-slate-200 transition"
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
            <div key={i} className="h-16 rounded-xl bg-slate-900/40 animate-pulse border border-slate-800" />
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
                className={`rounded-xl border p-4 space-y-2 transition ${isError ? 'border-red-800/40 bg-red-950/20' : isWarn ? 'border-amber-800/40 bg-amber-950/20' : 'border-slate-800 bg-slate-900/60'}`}
              >
                <div
                  className="flex items-start justify-between gap-3 cursor-pointer select-none"
                  onClick={() => setExpandedId(isExpanded ? null : log.id)}
                >
                  <div className="flex items-center gap-2.5 flex-wrap">
                    <span
                      className={`px-2 py-0.5 rounded text-[10px] font-mono font-semibold uppercase tracking-wider ${isError ? 'bg-red-950 text-red-300 border border-red-800' : isWarn ? 'bg-amber-950 text-amber-300 border border-amber-800' : 'bg-slate-800 text-slate-300'}`}
                    >
                      {log.level}
                    </span>
                    <span className="text-xs font-mono font-semibold text-slate-300">
                      {log.service} :: {log.component}
                    </span>
                    <span className="text-xs text-slate-400 font-mono text-[11px]">
                      {new Date(log.timestamp).toLocaleTimeString()}
                    </span>
                  </div>

                  <div className="flex items-center gap-3 shrink-0">
                    {log.duration_ms !== null && log.duration_ms !== undefined && (
                      <span className="text-[11px] font-mono text-slate-500">
                        {log.duration_ms} ms
                      </span>
                    )}
                    <span className="text-xs text-slate-500">
                      {isExpanded ? '▲' : '▼'}
                    </span>
                  </div>
                </div>

                <p className="text-xs text-slate-300 leading-relaxed font-sans">
                  {log.message}
                </p>

                {/* Expanded Technical Diagnostics */}
                {isExpanded && (
                  <div className="pt-2 border-t border-slate-800/60 space-y-2 text-xs font-mono">
                    <div className="grid grid-cols-2 gap-2 text-slate-400 text-[11px]">
                      <div>Event: <span className="text-slate-200">{log.event}</span></div>
                      <div>Status: <span className="text-slate-200">{log.status}</span></div>
                      {log.request_id && (
                        <div>Request ID: <span className="text-slate-200">{log.request_id}</span></div>
                      )}
                      {log.pipeline_run_id && (
                        <div>Pipeline Run: <span className="text-slate-200">{log.pipeline_run_id}</span></div>
                      )}
                    </div>

                    {log.details && (
                      <pre className="p-3 rounded-lg bg-slate-950/80 border border-slate-800 text-[11px] text-slate-300 overflow-x-auto">
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
