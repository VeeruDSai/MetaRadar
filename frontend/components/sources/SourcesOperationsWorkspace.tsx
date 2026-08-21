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
        return 'bg-emerald-50 text-emerald-700 border border-emerald-200 dark:bg-emerald-950/80 dark:text-emerald-300 dark:border-emerald-800/80'
      case 'DEGRADED':
        return 'bg-amber-50 text-amber-700 border border-amber-200 dark:bg-amber-950/80 dark:text-amber-300 dark:border-amber-800/80'
      case 'CONFIGURATION_ERROR':
        return 'bg-rose-50 text-rose-700 border border-rose-200 dark:bg-rose-950/80 dark:text-rose-300 dark:border-rose-800/80'
      case 'RATE_LIMITED':
        return 'bg-orange-50 text-orange-700 border border-orange-200 dark:bg-orange-950/80 dark:text-orange-300 dark:border-orange-800/80'
      case 'AUTH_FAILED':
      case 'UNHEALTHY':
      case 'ERROR':
        return 'bg-red-50 text-red-700 border border-red-200 dark:bg-red-950/80 dark:text-red-300 dark:border-red-800/80'
      case 'STALE':
        return 'bg-yellow-50 text-yellow-700 border border-yellow-200 dark:bg-yellow-950/80 dark:text-yellow-300 dark:border-yellow-800/80'
      case 'DISABLED':
        return 'bg-[var(--surface-muted)] text-[var(--muted-foreground)] border border-[var(--border)]'
      case 'NEVER_CONNECTED':
      default:
        return 'bg-[var(--surface-muted)] text-[var(--muted-foreground)] border border-[var(--border)]'
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between gap-4 flex-wrap">
        <div>
          <h2 className="text-xl font-bold text-[var(--foreground)]">Source Connectors & Health Operations</h2>
          <p className="text-xs text-[var(--muted-foreground)] mt-1">
            Real-time connector status, latency metrics, HTTP return codes, and live public ingestion telemetry across configured providers.
          </p>
        </div>
        <div className="flex items-center gap-2.5">
          <button
            onClick={loadSources}
            className="px-3.5 py-1.5 rounded-lg bg-[var(--surface-muted)] hover:bg-[var(--surface-subtle)] text-xs text-[var(--foreground)] transition border border-[var(--border)]"
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
            <span className="font-mono text-[var(--muted-foreground)]">Duration: {syncResult.ingestion?.duration_s}s</span>
          </div>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 font-mono text-[11px] text-[var(--foreground)] pt-1">
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
            <div key={i} className="h-48 rounded-xl bg-[var(--surface-subtle)] animate-pulse border border-[var(--border)]" />
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
              className="rounded-xl border border-[var(--border)] bg-[var(--card)] p-5 space-y-4 shadow-xs hover:border-[var(--border-strong,var(--border))] transition flex flex-col justify-between"
            >
              <div className="space-y-2">
                <div className="flex items-start justify-between gap-2">
                  <h3 className="text-sm font-semibold text-[var(--foreground)] truncate">{s.name}</h3>
                  <span className={`px-2 py-0.5 rounded text-[10px] font-semibold uppercase tracking-wider border shrink-0 ${getStatusBadge(s.connector_status)}`}>
                    {s.connector_status}
                  </span>
                </div>

                <div className="text-xs text-[var(--muted-foreground)] font-mono">
                  Source ID: {s.source_id} • {s.freshness_class}
                </div>

                {s.configuration_error_message && (
                  <div className="p-2.5 rounded-lg bg-rose-50 text-rose-800 border border-rose-200 dark:bg-rose-950/60 dark:text-rose-300 dark:border-rose-800/80 text-[11px] font-sans leading-normal">
                    <span className="font-semibold block mb-0.5">⚠️ Credential Configuration Required</span>
                    {s.configuration_error_message}
                  </div>
                )}
              </div>

              <div className="grid grid-cols-2 gap-2 text-xs pt-2 border-t border-[var(--border)]">
                <div className="p-2 rounded bg-[var(--surface-subtle)] border border-[var(--border)]">
                  <div className="text-[10px] text-[var(--muted-foreground)] uppercase">Latency</div>
                  <div className="font-mono text-[var(--foreground)] mt-0.5">{s.latency_ms !== null && s.latency_ms !== undefined ? `${s.latency_ms} ms` : 'N/A'}</div>
                </div>
                <div className="p-2 rounded bg-[var(--surface-subtle)] border border-[var(--border)]">
                  <div className="text-[10px] text-[var(--muted-foreground)] uppercase">Records Accepted</div>
                  <div className="font-mono text-emerald-600 dark:text-emerald-400 mt-0.5">{s.records_accepted || 0}</div>
                </div>
                <div className="p-2 rounded bg-[var(--surface-subtle)] border border-[var(--border)]">
                  <div className="text-[10px] text-[var(--muted-foreground)] uppercase">HTTP Status</div>
                  <div className="font-mono text-[var(--foreground)] mt-0.5">{s.http_status ? `${s.http_status}` : '-'}</div>
                </div>
                <div className="p-2 rounded bg-[var(--surface-subtle)] border border-[var(--border)]">
                  <div className="text-[10px] text-[var(--muted-foreground)] uppercase">Last Sync</div>
                  <div className="font-mono text-[var(--foreground)] mt-0.5 text-[11px] truncate">
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
