'use client'

import React, { useState, useEffect, useCallback } from 'react'
import type { SourceRegistryItem } from '@/types/api'
import { fetchSourcesHealth } from '@/lib/api'
import { formatError, FormattedError } from '@/lib/errors'
import { ErrorState } from '../common/ErrorState'
import { EmptyState } from '../common/EmptyState'

export function SourcesOperationsWorkspace() {
  const [sources, setSources] = useState<SourceRegistryItem[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<FormattedError | null>(null)

  const loadSources = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await fetchSourcesHealth()
      setSources(data)
    } catch (err) {
      setError(formatError(err, 'Failed to fetch source connectors health.'))
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    loadSources()
  }, [loadSources])

  const getStatusBadge = (status: string) => {
    switch (status.toUpperCase()) {
      case 'HEALTHY':
        return 'bg-emerald-950/80 text-emerald-300 border-emerald-800/80'
      case 'DEGRADED':
        return 'bg-amber-950/80 text-amber-300 border-amber-800/80'
      case 'RATE_LIMITED':
        return 'bg-orange-950/80 text-orange-300 border-orange-800/80'
      case 'AUTH_FAILED':
      case 'ERROR':
        return 'bg-red-950/80 text-red-300 border-red-800/80'
      case 'STALE':
        return 'bg-yellow-950/80 text-yellow-300 border-yellow-800/80'
      case 'DISABLED':
        return 'bg-slate-800 text-slate-400 border-slate-700'
      case 'NEVER_CONNECTED':
      default:
        return 'bg-slate-900 text-slate-400 border-slate-800'
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-slate-100">Source Connectors & Health Operations</h1>
          <p className="text-xs text-slate-400 mt-1">
            Real-time connector status, latency metrics, HTTP return codes, and ingestion telemetry across configured providers.
          </p>
        </div>
        <button
          onClick={loadSources}
          className="px-3.5 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-xs text-slate-200 transition"
        >
          Refresh Sources
        </button>
      </div>

      {error && (
        <ErrorState
          title={error.title}
          message={error.message}
          requestId={error.requestId}
          endpoint={error.endpoint}
          statusCode={error.statusCode}
          onRetry={loadSources}
        />
      )}

      {loading && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {[1, 2, 3, 4, 5, 6].map((i) => (
            <div key={i} className="h-44 rounded-xl bg-slate-900/40 animate-pulse border border-slate-800" />
          ))}
        </div>
      )}

      {!loading && !error && sources.length === 0 && (
        <EmptyState
          title="No sources configured"
          description="Source connectors (PubMed, ClinicalTrials, OpenFDA, EMA, NewsAPI) populate automatically from the backend configuration."
        />
      )}

      {!loading && !error && sources.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {sources.map((s) => (
            <div
              key={s.source_id}
              className="rounded-xl border border-slate-800 bg-slate-900/60 p-5 space-y-4 shadow-sm hover:border-slate-700 transition flex flex-col justify-between"
            >
              <div className="space-y-2">
                <div className="flex items-start justify-between gap-2">
                  <h3 className="text-sm font-semibold text-slate-100 truncate">{s.name}</h3>
                  <span className={`px-2 py-0.5 rounded text-[10px] font-semibold uppercase tracking-wider border shrink-0 ${getStatusBadge(s.connector_status)}`}>
                    {s.connector_status}
                  </span>
                </div>

                <div className="text-xs text-slate-400 font-mono">
                  Source ID: {s.source_id} • {s.freshness_class}
                </div>
              </div>

              <div className="grid grid-cols-2 gap-2 text-xs pt-2 border-t border-slate-800/60">
                <div className="p-2 rounded bg-slate-950/60 border border-slate-800">
                  <div className="text-[10px] text-slate-500 uppercase">Latency</div>
                  <div className="font-mono text-slate-200 mt-0.5">{s.latency_ms !== null && s.latency_ms !== undefined ? `${s.latency_ms} ms` : 'N/A'}</div>
                </div>
                <div className="p-2 rounded bg-slate-950/60 border border-slate-800">
                  <div className="text-[10px] text-slate-500 uppercase">Records Accepted</div>
                  <div className="font-mono text-emerald-400 mt-0.5">{s.records_accepted || 0}</div>
                </div>
                <div className="p-2 rounded bg-slate-950/60 border border-slate-800">
                  <div className="text-[10px] text-slate-500 uppercase">HTTP Status</div>
                  <div className="font-mono text-slate-200 mt-0.5">{s.http_status || '200 OK'}</div>
                </div>
                <div className="p-2 rounded bg-slate-950/60 border border-slate-800">
                  <div className="text-[10px] text-slate-500 uppercase">Last Sync</div>
                  <div className="font-mono text-slate-300 mt-0.5 text-[11px] truncate">
                    {s.last_success ? new Date(s.last_success).toLocaleTimeString() : 'Never'}
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
