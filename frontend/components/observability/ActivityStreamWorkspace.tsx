'use client'

import React, { useState, useEffect, useCallback } from 'react'
import type { ActivityLogItem } from '@/types/api'
import { fetchActivityLogs } from '@/lib/api'
import { formatError, FormattedError } from '@/lib/errors'
import { SectionTitle, Card, Badge } from '@/components/metaradar'
import { ErrorState } from '../common/ErrorState'
import { Database, RefreshCw } from 'lucide-react'

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

  const getBadgeTone = (level: string): 'critical' | 'high' | 'medium' | 'low' | 'neutral' => {
    switch (level?.toUpperCase()) {
      case 'ERROR':
        return 'critical'
      case 'WARNING':
        return 'high'
      case 'INFO':
        return 'low'
      default:
        return 'neutral'
    }
  }

  return (
    <>
      <SectionTitle
        eyebrow="Audit Trail & Diagnostic Stream"
        title="Observability & Ingestion Logs"
        detail="End-to-end structured JSON telemetry, correlation tracing (X-Request-ID), and pipeline execution logs."
      />

      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 mb-4">
        <div className="filter-bar">
          <button
            className={levelFilter === '' ? 'filter-active' : ''}
            onClick={() => setLevelFilter('')}
          >
            All Log Levels
          </button>
          <button
            className={levelFilter === 'INFO' ? 'filter-active' : ''}
            onClick={() => setLevelFilter('INFO')}
          >
            INFO
          </button>
          <button
            className={levelFilter === 'WARNING' ? 'filter-active' : ''}
            onClick={() => setLevelFilter('WARNING')}
          >
            WARNING
          </button>
          <button
            className={levelFilter === 'ERROR' ? 'filter-active' : ''}
            onClick={() => setLevelFilter('ERROR')}
          >
            ERROR
          </button>
        </div>

        <button
          onClick={loadLogs}
          className="inline-flex items-center gap-1 px-3 py-1.5 rounded text-xs border border-[var(--border)] bg-[var(--surface)] text-[var(--foreground)] hover:border-[var(--signal)]"
        >
          <RefreshCw size={13} className={loading ? 'animate-spin' : ''} />
          <span>Refresh Stream</span>
        </button>
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
        <div className="grid gap-3">
          {[1, 2, 3, 4, 5].map((i) => (
            <Card key={i} className="animate-pulse h-16" />
          ))}
        </div>
      )}

      {!loading && !error && filteredLogs.length === 0 && (
        <Card className="empty-state">
          <Database size={28} />
          <p>No activity events found</p>
          <span>System events and connector runs will appear here as the platform processes pipeline workloads.</span>
        </Card>
      )}

      {!loading && !error && filteredLogs.length > 0 && (
        <div className="grid gap-2">
          {filteredLogs.map((log) => {
            const isExpanded = expandedId === log.id

            return (
              <Card
                key={log.id}
                className="cursor-pointer transition hover:border-[var(--border-selected)]"
              >
                <div
                  className="flex items-start justify-between gap-3 select-none"
                  onClick={() => setExpandedId(isExpanded ? null : log.id)}
                >
                  <div className="flex items-center gap-2.5 flex-wrap">
                    <Badge tone={getBadgeTone(log.level)}>
                      {log.level}
                    </Badge>
                    <span className="text-xs font-mono font-semibold text-[var(--foreground)]">
                      {log.service} :: {log.component}
                    </span>
                    <span className="text-[11px] text-[var(--muted-foreground)] font-mono">
                      {new Date(log.timestamp).toLocaleTimeString()}
                    </span>
                  </div>

                  <div className="flex items-center gap-3 shrink-0">
                    {log.duration_ms !== null && log.duration_ms !== undefined && (
                      <span className="text-[11px] font-mono text-[var(--muted-foreground)]">
                        {log.duration_ms} ms
                      </span>
                    )}
                    <span className="text-xs text-[var(--muted-foreground)] font-mono">
                      {isExpanded ? '▲' : '▼'}
                    </span>
                  </div>
                </div>

                <p className="text-xs text-[var(--foreground)] leading-relaxed m-0 mt-2 font-sans">
                  {log.message}
                </p>

                {isExpanded && (
                  <div className="pt-2 border-t border-[var(--border)] mt-2 text-xs space-y-1.5 font-mono">
                    <div className="flex justify-between text-[11px] text-[var(--muted-foreground)]">
                      <span>Request ID: <code className="text-[var(--foreground)]">{log.request_id || 'N/A'}</code></span>
                      <span>Event: <code className="text-[var(--foreground)]">{log.event}</code></span>
                    </div>
                    {log.details && (
                      <pre
                        className="p-2.5 rounded text-[11px] overflow-x-auto border border-[var(--border)]"
                        style={{ background: 'var(--surface-secondary)' }}
                      >
                        {typeof log.details === 'string' ? log.details : JSON.stringify(log.details, null, 2)}
                      </pre>
                    )}
                  </div>
                )}
              </Card>
            )
          })}
        </div>
      )}
    </>
  )
}
