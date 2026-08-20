'use client'

import React, { useState, useEffect, useCallback } from 'react'
import type { SourceRegistryItem } from '@/types/api'
import { fetchSourcesHealth, triggerIngestAndPipelineSync } from '@/lib/api'
import { formatError, FormattedError } from '@/lib/errors'
import { ErrorState } from '../common/ErrorState'
import { EmptyState } from '../common/EmptyState'

export function SourcesOperationsWorkspace() {
  const [sources, setSources] = useState<SourceRegistryItem[]>([])
  const [loading, setLoading] = useState(true)
  const [syncing, setSyncing] = useState(false)
  const [syncResult, setSyncResult] = useState<any | null>(null)
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

  const handleLiveSync = async () => {
    setSyncing(true)
    setError(null)
    setSyncResult(null)
    try {
      const res = await triggerIngestAndPipelineSync(undefined, 50)
      setSyncResult(res)
      await loadSources()
    } catch (err) {
      setError(formatError(err, 'Live web ingestion failed.'))
    } finally {
      setSyncing(false)
    }
  }

  const getStatusBadge = (status: string) => {
    switch (status.toUpperCase()) {
      case 'HEALTHY':
        return 'bg-emerald-500/10 text-emerald-700 border-emerald-500/30 dark:bg-emerald-950/80 dark:text-emerald-300 dark:border-emerald-800/80'
      case 'DEGRADED':
        return 'bg-amber-500/10 text-amber-700 border-amber-500/30 dark:bg-amber-950/80 dark:text-amber-300 dark:border-amber-800/80'
      case 'RATE_LIMITED':
        return 'bg-orange-500/10 text-orange-700 border-orange-500/30 dark:bg-orange-950/80 dark:text-orange-300 dark:border-orange-800/80'
      case 'AUTH_FAILED':
      case 'ERROR':
        return 'bg-red-500/10 text-red-700 border-red-500/30 dark:bg-red-950/80 dark:text-red-300 dark:border-red-800/80'
      case 'STALE':
        return 'bg-yellow-500/10 text-yellow-700 border-yellow-500/30 dark:bg-yellow-950/80 dark:text-yellow-300 dark:border-yellow-800/80'
      case 'DISABLED':
        return 'bg-slate-100 text-slate-600 border-slate-200 dark:bg-slate-800 dark:text-slate-400 dark:border-slate-700'
      case 'NEVER_CONNECTED':
      default:
        return 'bg-slate-100 text-slate-600 border-slate-200 dark:bg-slate-900 dark:text-slate-400 dark:border-slate-800'
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between gap-4 flex-wrap">
        <div>
          <h1 className="text-xl font-bold text-slate-900 dark:text-slate-100">Source Connectors & Health Operations</h1>
          <p className="text-xs text-slate-600 dark:text-slate-400 mt-1">
            Real-time connector status, latency metrics, HTTP return codes, and live public ingestion telemetry across configured providers.
          </p>
        </div>
        <div className="flex items-center gap-2.5">
          <button
            onClick={loadSources}
            className="px-3.5 py-1.5 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-700 dark:bg-slate-800 dark:hover:bg-slate-700 text-xs dark:text-slate-200 transition border border-slate-200 dark:border-slate-700"
          >
            Refresh Health
          </button>
          <button
            onClick={handleLiveSync}
            disabled={syncing}
            className="px-4 py-1.5 rounded-lg bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-xs font-semibold text-white shadow-md transition flex items-center gap-1.5"
          >
            {syncing ? (
              <>
                <span className="inline-block w-3 h-3 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                <span>Ingesting Live Data...</span>
              </>
            ) : (
              <>
                <span>⚡</span>
                <span>Trigger Live Web Ingestion</span>
              </>
            )}
          </button>
        </div>
      </div>

      {syncResult && (
        <div className="p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/30 dark:bg-emerald-950/40 dark:border-emerald-800/80 space-y-2 text-xs">
          <div className="flex items-center justify-between">
            <span className="font-semibold text-emerald-800 dark:text-emerald-300">✓ Live Web Ingestion & Pipeline Sync Complete</span>
            <span className="font-mono text-slate-600 dark:text-slate-400">Duration: {syncResult.ingestion?.duration_s}s</span>
          </div>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 font-mono text-[11px] text-slate-700 dark:text-slate-300 pt-1">
            <div>Fetched: <span className="text-emerald-600 dark:text-emerald-400 font-bold">{syncResult.ingestion?.total_fetched || 0}</span></div>
            <div>New Bronze: <span className="text-emerald-600 dark:text-emerald-400 font-bold">{syncResult.ingestion?.total_new_bronze || 0}</span></div>
            <div>Signals Promoted: <span className="text-blue-600 dark:text-blue-400 font-bold">{syncResult.pipeline?.signals_processed || 0}</span></div>
            <div>Confluences: <span className="text-purple-600 dark:text-purple-400 font-bold">{syncResult.pipeline?.confluences_count || 0}</span></div>
          </div>
        </div>
      )}

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
            <div key={i} className="h-44 rounded-xl bg-slate-100 dark:bg-slate-900/40 animate-pulse border border-slate-200 dark:border-slate-800" />
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
              className="rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900/60 p-5 space-y-4 shadow-sm hover:border-slate-300 dark:hover:border-slate-700 transition flex flex-col justify-between"
            >
              <div className="space-y-2">
                <div className="flex items-start justify-between gap-2">
                  <h3 className="text-sm font-semibold text-slate-900 dark:text-slate-100 truncate">{s.name}</h3>
                  <span className={`px-2 py-0.5 rounded text-[10px] font-semibold uppercase tracking-wider border shrink-0 ${getStatusBadge(s.connector_status)}`}>
                    {s.connector_status}
                  </span>
                </div>

                <div className="text-xs text-slate-600 dark:text-slate-400 font-mono">
                  Source ID: {s.source_id} • {s.freshness_class}
                </div>
              </div>

              <div className="grid grid-cols-2 gap-2 text-xs pt-2 border-t border-slate-100 dark:border-slate-800/60">
                <div className="p-2 rounded bg-slate-50 dark:bg-slate-950/60 border border-slate-200 dark:border-slate-800">
                  <div className="text-[10px] text-slate-500 uppercase">Latency</div>
                  <div className="font-mono text-slate-900 dark:text-slate-200 mt-0.5">{s.latency_ms !== null && s.latency_ms !== undefined ? `${s.latency_ms} ms` : 'N/A'}</div>
                </div>
                <div className="p-2 rounded bg-slate-50 dark:bg-slate-950/60 border border-slate-200 dark:border-slate-800">
                  <div className="text-[10px] text-slate-500 uppercase">Records Accepted</div>
                  <div className="font-mono text-emerald-600 dark:text-emerald-400 mt-0.5">{s.records_accepted || 0}</div>
                </div>
                <div className="p-2 rounded bg-slate-50 dark:bg-slate-950/60 border border-slate-200 dark:border-slate-800">
                  <div className="text-[10px] text-slate-500 uppercase">HTTP Status</div>
                  <div className="font-mono text-slate-900 dark:text-slate-200 mt-0.5">{s.http_status || '200 OK'}</div>
                </div>
                <div className="p-2 rounded bg-slate-50 dark:bg-slate-950/60 border border-slate-200 dark:border-slate-800">
                  <div className="text-[10px] text-slate-500 uppercase">Last Sync</div>
                  <div className="font-mono text-slate-700 dark:text-slate-300 mt-0.5 text-[11px] truncate">
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
