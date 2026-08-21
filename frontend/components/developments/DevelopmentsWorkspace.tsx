'use client'

import React, { useState, useEffect, useCallback } from 'react'
import type { DevelopmentSummary } from '@/types/api'
import { fetchDevelopments } from '@/lib/api'
import { formatError, FormattedError } from '@/lib/errors'
import { SectionTitle, Card, Badge } from '@/components/metaradar'
import { ErrorState } from '../common/ErrorState'
import { FlaskConical, RefreshCw } from 'lucide-react'

export function DevelopmentsWorkspace() {
  const [developments, setDevelopments] = useState<DevelopmentSummary[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<FormattedError | null>(null)

  const loadDevelopments = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await fetchDevelopments(50)
      setDevelopments(data)
    } catch (err) {
      setError(formatError(err, 'Failed to fetch clinical developments registry.'))
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    loadDevelopments()
  }, [loadDevelopments])

  const totalSignals = developments.reduce((acc, d) => acc + (d.signal_count || 0), 0)

  return (
    <>
      <SectionTitle
        eyebrow="Asset Tracking & Competitor Pipeline"
        title="Competitive Developments Registry"
        detail="Canonical disease-area development tracks linking clinical trials, regulatory filings, and competitor milestones."
      />

      <div className="kpi-grid">
        <div className="panel kpi">
          <p className="eyebrow">Tracked developments</p>
          <div className="kpi-value">
            <strong style={{ color: 'var(--signal)' }}>{developments.length}</strong>
            <span>Active programs</span>
          </div>
        </div>
        <div className="panel kpi">
          <p className="eyebrow">Indexed signals</p>
          <div className="kpi-value">
            <strong>{totalSignals}</strong>
            <span>Evidence records</span>
          </div>
        </div>
        <div className="panel kpi">
          <p className="eyebrow">Therapeutic area</p>
          <div className="kpi-value">
            <strong style={{ fontSize: '20px' }}>Haemophilia</strong>
            <span>Global</span>
          </div>
        </div>
        <div className="panel kpi">
          <p className="eyebrow">Pipeline engine</p>
          <div className="kpi-value">
            <strong style={{ color: 'var(--success)' }}>Active</strong>
            <span>FSM v5.1</span>
          </div>
        </div>
      </div>

      <div className="flex items-center justify-between gap-3 mb-4">
        <div className="text-xs text-[var(--muted-foreground)]">
          {developments.length} clinical & regulatory programs indexed
        </div>
        <button
          onClick={loadDevelopments}
          className="inline-flex items-center gap-1 px-3 py-1.5 rounded text-xs border border-[var(--border)] bg-[var(--surface)] text-[var(--foreground)] hover:border-[var(--signal)]"
        >
          <RefreshCw size={13} className={loading ? 'animate-spin' : ''} />
          <span>Refresh Registry</span>
        </button>
      </div>

      {error && (
        <ErrorState
          title={error.title}
          message={error.message}
          requestId={error.requestId}
          endpoint={error.endpoint}
          statusCode={error.statusCode}
          onRetry={loadDevelopments}
        />
      )}

      {loading && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {[1, 2, 3, 4].map((i) => (
            <Card key={i} className="animate-pulse h-36" />
          ))}
        </div>
      )}

      {!loading && !error && developments.length === 0 && (
        <Card className="empty-state">
          <FlaskConical size={28} />
          <p>No registered developments found</p>
          <span>Competitive developments are synthesized automatically when new clinical trials or regulatory filings are ingested.</span>
        </Card>
      )}

      {!loading && !error && developments.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {developments.map((d) => (
            <Card key={d.development_id} className="flex flex-col justify-between">
              <div>
                <div className="flex items-start justify-between gap-3 mb-2">
                  <div className="flex items-center gap-2 flex-wrap">
                    <Badge tone="high">Stage: {d.current_stage || 'Announced'}</Badge>
                    <span className="text-xs font-mono text-[var(--muted-foreground)]">
                      {d.disease || 'Haemophilia'}
                    </span>
                  </div>
                  <Badge tone="neutral">{d.signal_count} signals</Badge>
                </div>
                <h3 className="text-base font-semibold text-[var(--foreground)] m-0 mb-1">
                  {d.title}
                </h3>
              </div>

              <div className="flex items-center justify-between pt-2 border-t border-[var(--border)] text-xs text-[var(--muted-foreground)] mt-3">
                <div>Asset: <strong className="text-[var(--foreground)]">{d.asset_name || 'Investigational'}</strong></div>
                <div>Sponsor: <strong className="text-[var(--foreground)]">{d.company_name || 'Competitor'}</strong></div>
              </div>
            </Card>
          ))}
        </div>
      )}
    </>
  )
}
