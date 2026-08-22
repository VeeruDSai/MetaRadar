'use client'

import React, { useState, useEffect, useCallback } from 'react'
import type { FeedbackSummaryResponse } from '@/types/api'
import { fetchFeedbackSummary } from '@/lib/api'
import { formatError, FormattedError } from '@/lib/errors'
import { SectionTitle, Card, Badge } from '@/components/metaradar'
import { ErrorState } from '../common/ErrorState'
import { Network, RefreshCw } from 'lucide-react'

export function FunctionsWorkspace() {
  const [summary, setSummary] = useState<FeedbackSummaryResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<FormattedError | null>(null)

  const loadSummary = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await fetchFeedbackSummary()
      setSummary(data)
    } catch (err) {
      setError(formatError(err, 'Failed to fetch stakeholder functions telemetry.'))
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    loadSummary()
  }, [loadSummary])

  const defaultRoles = [
    { stakeholder_function: 'MEDICAL_AFFAIRS', total_feedback_count: 0, average_relevance: 0, average_urgency: 0, action_approval_rate: 0 },
    { stakeholder_function: 'REGULATORY', total_feedback_count: 0, average_relevance: 0, average_urgency: 0, action_approval_rate: 0 },
    { stakeholder_function: 'SAFETY', total_feedback_count: 0, average_relevance: 0, average_urgency: 0, action_approval_rate: 0 },
    { stakeholder_function: 'MARKET_ACCESS', total_feedback_count: 0, average_relevance: 0, average_urgency: 0, action_approval_rate: 0 },
    { stakeholder_function: 'COMMUNICATIONS', total_feedback_count: 0, average_relevance: 0, average_urgency: 0, action_approval_rate: 0 },
    { stakeholder_function: 'LEADERSHIP', total_feedback_count: 0, average_relevance: 0, average_urgency: 0, action_approval_rate: 0 },
  ]

  const activeRoles = summary?.roles && summary.roles.length > 0 ? summary.roles : defaultRoles

  return (
    <>
      <SectionTitle
        eyebrow="Cross-Functional Alignment"
        title="Functions Intelligence"
        detail="Function-specific signal routing, relevance calibration, and approval metrics across the 6 canonical stakeholder roles."
      />

      <div className="flex items-center justify-between gap-3 mb-4">
        <div className="text-xs text-[var(--muted-foreground)]">
          6 canonical stakeholder functions actively monitored
        </div>
        <button
          onClick={loadSummary}
          className="inline-flex items-center gap-1 px-3 py-1.5 rounded text-xs border border-[var(--border)] bg-[var(--surface)] text-[var(--foreground)] hover:border-[var(--signal)]"
        >
          <RefreshCw size={13} className={loading ? 'animate-spin' : ''} />
          <span>Refresh Functions</span>
        </button>
      </div>

      {error && (
        <ErrorState
          title={error.title}
          message={error.message}
          requestId={error.requestId}
          endpoint={error.endpoint}
          statusCode={error.statusCode}
          onRetry={loadSummary}
        />
      )}

      {loading && (
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4">
          {[1, 2, 3, 4, 5, 6].map((i) => (
            <Card key={i} className="animate-pulse h-36" />
          ))}
        </div>
      )}

      {!loading && !error && (
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4">
          {activeRoles.map((role) => (
            <Card key={role.stakeholder_function} className="flex flex-col justify-between">
              <div>
                <div className="flex items-center justify-between mb-2">
                  <h3 className="text-xs font-bold uppercase tracking-wider text-[var(--foreground)] m-0">
                    {role.stakeholder_function.replace(/_/g, ' ')}
                  </h3>
                  <Badge tone={role.action_approval_rate && role.action_approval_rate > 0 ? 'high' : 'neutral'}>
                    {role.action_approval_rate ? `${role.action_approval_rate}% Approval` : 'No reviews'}
                  </Badge>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-2 text-xs pt-2 border-t border-[var(--border)] mt-3">
                <div
                  className="p-2 rounded border border-[var(--border)]"
                  style={{ background: 'var(--surface-secondary)' }}
                >
                  <div className="text-[9px] text-[var(--muted-foreground)] uppercase font-semibold">Avg Relevance</div>
                  <div className="text-xs font-semibold mt-0.5" style={{ color: 'var(--signal)' }}>
                    {role.average_relevance ? `★ ${role.average_relevance.toFixed(1)} / 5.0` : '—'}
                  </div>
                </div>
                <div
                  className="p-2 rounded border border-[var(--border)]"
                  style={{ background: 'var(--surface-secondary)' }}
                >
                  <div className="text-[9px] text-[var(--muted-foreground)] uppercase font-semibold">Feedback Count</div>
                  <div className="text-xs font-semibold text-[var(--foreground)] mt-0.5">
                    {role.total_feedback_count} reviews
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
