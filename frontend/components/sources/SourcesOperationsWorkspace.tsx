'use client'

import React, { useState, useEffect, useCallback } from 'react'
import type { SourceRegistryItem } from '@/types/api'
import { fetchSourcesHealth, triggerIngestAndPipelineSync } from '@/lib/api'
import { formatError, FormattedError } from '@/lib/errors'
import { SectionTitle, Card, Badge } from '@/components/metaradar'
import { ErrorState } from '../common/ErrorState'
import { SpecularButton } from '@/components/ui/SpecularButton'
import { Activity, AlertTriangle, BookOpen, CheckCircle2, RefreshCw, Zap } from 'lucide-react'

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

  const getBadgeTone = (status: string): 'critical' | 'high' | 'medium' | 'low' | 'neutral' => {
    switch (status?.toUpperCase()) {
      case 'HEALTHY':
        return 'low'
      case 'NO_NEW_DATA':
        return 'neutral'
      case 'STALE':
        return 'medium'
      case 'DEGRADED':
      case 'RATE_LIMITED':
        return 'high'
      case 'CONFIGURATION_ERROR':
      case 'AUTH_FAILED':
      case 'ERROR':
      case 'FAILED':
      case 'UNHEALTHY':
        return 'critical'
      case 'DISABLED':
      case 'NEVER_CONNECTED':
      default:
        return 'neutral'
    }
  }

  const healthyCount = sources.filter((s) => ['HEALTHY', 'NO_NEW_DATA'].includes(s.connector_status?.toUpperCase())).length
  const totalRecords = sources.reduce((acc, s) => acc + (s.records_accepted || 0), 0)
  const totalNew = sources.reduce((acc, s) => acc + (s.records_new || 0), 0)

  return (
    <>
      <SectionTitle
        eyebrow="Autonomous Ingestion & Telemetry"
        title="Sources & Connectors"
        detail="Truthful real-time connector health, autonomous background scheduler status, latency, and provenance telemetry across configured authoritative providers."
      />

      <div className="kpi-grid">
        <div className="panel kpi">
          <p className="eyebrow">Monitored sources</p>
          <div className="kpi-value">
            <strong>{sources.length}</strong>
            <span>Active providers</span>
          </div>
        </div>
        <div className="panel kpi">
          <p className="eyebrow">Operational connectors</p>
          <div className="kpi-value">
            <strong style={{ color: 'var(--success)' }}>{healthyCount}</strong>
            <span>{sources.length > 0 ? `${Math.round((healthyCount / sources.length) * 100)}% synchronized` : '0%'}</span>
          </div>
        </div>
        <div className="panel kpi">
          <p className="eyebrow">Records accepted</p>
          <div className="kpi-value">
            <strong>{totalRecords}</strong>
            <span>Bronze layer</span>
          </div>
        </div>
        <div className="panel kpi">
          <p className="eyebrow">Scheduler state</p>
          <div className="kpi-value">
            <strong style={{ color: 'var(--signal)' }}>Autonomous</strong>
            <span>Continuous background radar</span>
          </div>
        </div>
      </div>

      <div className="flex items-center justify-between gap-3 mb-4 flex-wrap">
        <div className="text-xs text-[var(--muted-foreground)]">
          {sources.length} active connectors · Autonomous background scheduler active
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={loadSources}
            className="inline-flex items-center gap-1.5 px-3.5 h-8 rounded text-xs font-medium border border-[var(--border)] bg-[var(--surface)] text-[var(--foreground)] hover:border-[var(--signal)] transition"
          >
            <RefreshCw size={13} className={loading ? 'animate-spin' : ''} />
            <span>Refresh Telemetry</span>
          </button>
          <SpecularButton
            size="default"
            radius={8}
            intensity={1.2}
            shineSize={14}
            shineFade={45}
            thickness={1}
            speed={0.4}
            followMouse
            proximity={220}
            loading={syncing}
            autoAnimate={syncing}
            onClick={handleLiveSync}
            disabled={syncing}
            title="Trigger live multi-source biomedical ingestion run"
            aria-label="Run live ingestion now"
            className="h-8 shadow-sm cursor-pointer"
          >
            {syncing ? (
              <>
                <RefreshCw size={13} className="animate-spin text-[var(--primary)]" />
                <span className="font-semibold">Ingesting Live Data...</span>
              </>
            ) : (
              <>
                <Zap size={13} className="text-amber-400" />
                <span className="font-semibold">Run Ingestion Now</span>
              </>
            )}
          </SpecularButton>
        </div>
      </div>

      {syncResult && (
        <Card className="mb-4" style={{ borderColor: 'var(--border-selected)', background: 'color-mix(in srgb, var(--signal) 8%, var(--surface))' }}>
          <div className="flex items-center justify-between mb-2">
            <span className="font-semibold text-xs text-[var(--foreground)] flex items-center gap-1.5">
              <CheckCircle2 size={15} style={{ color: 'var(--success)' }} /> Ingestion Execution Complete
            </span>
            <span className="font-mono text-[11px] text-[var(--muted-foreground)]">Duration: {syncResult.ingestion?.duration_s}s</span>
          </div>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 font-mono text-[11px] text-[var(--foreground)] pt-2 border-t border-[var(--border)]">
            <div>Fetched: <strong style={{ color: 'var(--success)' }}>{syncResult.ingestion?.total_fetched || 0}</strong></div>
            <div>New Bronze: <strong style={{ color: 'var(--success)' }}>{syncResult.ingestion?.total_new_bronze || 0}</strong></div>
            <div>Signals Promoted: <strong style={{ color: 'var(--primary)' }}>{syncResult.pipeline?.signals_processed || 0}</strong></div>
            <div>Confluences: <strong style={{ color: 'var(--accent)' }}>{syncResult.pipeline?.confluences_count || 0}</strong></div>
          </div>
        </Card>
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
            <Card key={i} className="animate-pulse h-48" />
          ))}
        </div>
      )}

      {!loading && !error && sources.length === 0 && (
        <Card className="empty-state">
          <BookOpen size={28} />
          <p>No source connectors configured</p>
          <span>Source connectors (PubMed, ClinicalTrials, OpenFDA, EMA, NewsAPI) populate automatically from the backend configuration.</span>
        </Card>
      )}

      {!loading && !error && sources.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {sources.map((s) => (
            <Card key={s.source_id} className="flex flex-col justify-between">
              <div>
                <div className="card-heading">
                  <div>
                    <div className="flex items-center gap-1.5 mb-1">
                      <span className="text-[10px] uppercase font-bold tracking-wider px-1.5 py-0.5 rounded bg-[var(--surface-secondary)] border border-[var(--border)] text-[var(--muted-foreground)]">
                        Tier {s.tier || 1}
                      </span>
                      <h2 className="text-sm font-semibold truncate">{s.name}</h2>
                    </div>
                    <p className="muted panel-subtitle font-mono text-[10px]">
                      {s.source_id} · {s.freshness_class}
                    </p>
                  </div>
                  <Badge tone={getBadgeTone(s.connector_status)}>
                    {s.connector_status === 'NO_NEW_DATA' ? 'NO NEW DATA' : s.connector_status}
                  </Badge>
                </div>

                {s.configuration_error_message && (
                  <div
                    className="p-2.5 rounded text-[11px] leading-normal my-2 border"
                    style={{
                      borderColor: 'color-mix(in srgb, var(--danger) 30%, transparent)',
                      background: 'color-mix(in srgb, var(--danger) 10%, var(--surface))',
                      color: 'var(--danger)',
                    }}
                  >
                    <strong className="block mb-0.5">⚠️ Credential Configuration Required</strong>
                    <span>{s.configuration_error_message}</span>
                  </div>
                )}
              </div>

              <div className="grid grid-cols-2 gap-2 text-xs pt-3 border-t border-[var(--border)] mt-3">
                <div className="p-2 rounded border border-[var(--border)]" style={{ background: 'var(--surface-secondary)' }}>
                  <div className="text-[9px] text-[var(--muted-foreground)] uppercase font-semibold">Latency</div>
                  <div className="font-mono text-[var(--foreground)] mt-0.5 text-xs">
                    {s.latency_ms !== null && s.latency_ms !== undefined ? `${s.latency_ms} ms` : 'N/A'}
                  </div>
                </div>
                <div className="p-2 rounded border border-[var(--border)]" style={{ background: 'var(--surface-secondary)' }}>
                  <div className="text-[9px] text-[var(--muted-foreground)] uppercase font-semibold">Accepted</div>
                  <div className="font-mono mt-0.5 text-xs font-semibold" style={{ color: 'var(--success)' }}>
                    {s.records_accepted || 0}
                  </div>
                </div>
                <div className="p-2 rounded border border-[var(--border)]" style={{ background: 'var(--surface-secondary)' }}>
                  <div className="text-[9px] text-[var(--muted-foreground)] uppercase font-semibold">New Records</div>
                  <div className="font-mono text-[var(--foreground)] mt-0.5 text-xs">
                    {s.records_new || 0}
                  </div>
                </div>
                <div className="p-2 rounded border border-[var(--border)]" style={{ background: 'var(--surface-secondary)' }}>
                  <div className="text-[9px] text-[var(--muted-foreground)] uppercase font-semibold">Last Success</div>
                  <div className="font-mono text-[var(--foreground)] mt-0.5 text-[10px] truncate">
                    {s.last_success ? new Date(s.last_success).toLocaleTimeString() : 'Never'}
                  </div>
                </div>
              </div>
            </Card>
          ))}
        </div>
      )}
    </>
  )
}
