'use client'

import React, { useState, useEffect, useCallback } from 'react'
import type { MissingSignalWatchItem } from '@/types/api'
import { fetchMissingSignals } from '@/lib/api'
import { formatError, FormattedError } from '@/lib/errors'
import { SectionTitle, Card, Badge } from '@/components/metaradar'
import { ErrorState } from '../common/ErrorState'
import { Eye, RefreshCw } from 'lucide-react'

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

  const getStatusTone = (status: string): 'critical' | 'high' | 'medium' | 'low' | 'neutral' => {
    switch (status?.toUpperCase()) {
      case 'OVERDUE':
        return 'critical'
      case 'DUE':
        return 'high'
      case 'WITHIN_WINDOW':
        return 'medium'
      case 'SATISFIED':
        return 'low'
      case 'SUPPRESSED':
      default:
        return 'neutral'
    }
  }

  return (
    <>
      <SectionTitle
        eyebrow="Absence-of-Evidence Surveillance"
        title="Missing Signals"
        detail="Surveillance of expected milestones and overdue clinical/regulatory disclosures."
      />

      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 mb-4">
        <div className="filter-bar">
          <button
            className={statusFilter === '' ? 'filter-active' : ''}
            onClick={() => setStatusFilter('')}
          >
            All Watch States
          </button>
          <button
            className={statusFilter === 'OVERDUE' ? 'filter-active' : ''}
            onClick={() => setStatusFilter('OVERDUE')}
          >
            Overdue
          </button>
          <button
            className={statusFilter === 'DUE' ? 'filter-active' : ''}
            onClick={() => setStatusFilter('DUE')}
          >
            Due Soon
          </button>
          <button
            className={statusFilter === 'WITHIN_WINDOW' ? 'filter-active' : ''}
            onClick={() => setStatusFilter('WITHIN_WINDOW')}
          >
            Within Window
          </button>
          <button
            className={statusFilter === 'SATISFIED' ? 'filter-active' : ''}
            onClick={() => setStatusFilter('SATISFIED')}
          >
            Satisfied
          </button>
        </div>

        <button
          onClick={loadMissingSignals}
          className="inline-flex items-center gap-1 px-3 py-1.5 rounded text-xs border border-[var(--border)] bg-[var(--surface)] text-[var(--foreground)] hover:border-[var(--signal)]"
        >
          <RefreshCw size={13} className={loading ? 'animate-spin' : ''} />
          <span>Refresh</span>
        </button>
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
        <div className="grid gap-4">
          {[1, 2, 3].map((i) => (
            <Card key={i} className="animate-pulse h-36" />
          ))}
        </div>
      )}

      {!loading && !error && items.length === 0 && (
        <Card className="empty-state">
          <Eye size={28} />
          <p>No missing filings or overdue milestones detected</p>
          <span>Watch items track expected milestone events (e.g. 180-day Phase III readout following trial completion).</span>
        </Card>
      )}

      {!loading && !error && items.length > 0 && (
        <div className="grid gap-4">
          {items.map((item) => (
            <Card key={item.watch_id}>
              <div className="flex items-start justify-between gap-4 mb-2">
                <div>
                  <div className="flex items-center gap-2 mb-1 flex-wrap">
                    <Badge tone={getStatusTone(item.status)}>
                      {item.status}
                    </Badge>
                    <Badge tone="neutral">
                      {item.responsible_function}
                    </Badge>
                    {item.days_overdue > 0 && (
                      <span className="text-xs font-mono font-semibold" style={{ color: 'var(--danger)' }}>
                        +{item.days_overdue} days overdue
                      </span>
                    )}
                  </div>
                  <h3 className="text-sm font-semibold text-[var(--foreground)] m-0">
                    {item.development_title || 'Portfolio Monitoring Asset'}
                  </h3>
                </div>

                <div className="text-right shrink-0">
                  <div className="text-xs font-mono font-semibold text-[var(--foreground)]">
                    Window: {item.monitoring_window_days} days
                  </div>
                  <div className="text-[10px] text-[var(--muted-foreground)] font-mono">
                    Confidence: {item.overdue_heuristic_score !== undefined ? `${Math.round(item.overdue_heuristic_score * 100)}%` : `${Math.round(item.confidence * 100)}%`}
                  </div>
                </div>
              </div>

              {/* Trigger vs Expected Event description */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-2 border-t border-[var(--border)] mt-2 text-xs">
                <div
                  className="p-3 rounded border border-[var(--border)]"
                  style={{ background: 'var(--surface-secondary)' }}
                >
                  <div className="text-[10px] font-semibold uppercase text-[var(--muted-foreground)] mb-1">Observed Trigger Event</div>
                  <div className="text-[var(--foreground)]">{item.trigger_event}</div>
                </div>
                <div
                  className="p-3 rounded border"
                  style={{
                    background: 'color-mix(in srgb, var(--warning) 6%, var(--surface))',
                    borderColor: 'color-mix(in srgb, var(--warning) 25%, var(--border))',
                  }}
                >
                  <div className="text-[10px] font-semibold uppercase mb-1" style={{ color: 'var(--warning)' }}>
                    Expected Milestone Event
                  </div>
                  <div className="text-[var(--foreground)] font-medium">{item.expected_event}</div>
                </div>
              </div>
            </Card>
          ))}
        </div>
      )}
    </>
  )
}
