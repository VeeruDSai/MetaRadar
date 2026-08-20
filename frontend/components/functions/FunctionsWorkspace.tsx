'use client'

import React, { useState, useEffect, useCallback } from 'react'
import type { FeedbackSummaryResponse } from '@/types/api'
import { fetchFeedbackSummary } from '@/lib/api'
import { formatError, FormattedError } from '@/lib/errors'
import { ErrorState } from '../common/ErrorState'
import { EmptyState } from '../common/EmptyState'

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

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-slate-100">Stakeholder Functions Intelligence</h1>
          <p className="text-xs text-slate-400 mt-1">
            Functional routing metrics, accuracy ratings, and action approval rates across the 6 canonical stakeholder roles.
          </p>
        </div>
        <button
          onClick={loadSummary}
          className="px-3.5 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-xs text-slate-200 transition"
        >
          Refresh Functions
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
            <div key={i} className="h-32 rounded-xl bg-slate-900/40 animate-pulse border border-slate-800" />
          ))}
        </div>
      )}

      {!loading && !error && (!summary || summary.roles.length === 0) && (
        <EmptyState
          title="No stakeholder ratings recorded yet"
          description="Stakeholder feedback submitted via the Evidence Drawer will populate real performance telemetry here."
        />
      )}

      {!loading && !error && summary && summary.roles.length > 0 && (
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4">
          {summary.roles.map((role) => (
            <div
              key={role.stakeholder_function}
              className="rounded-xl border border-slate-800 bg-slate-900/60 p-5 space-y-3 shadow-sm hover:border-slate-700 transition"
            >
              <div className="flex items-center justify-between">
                <h3 className="text-sm font-semibold text-slate-200">
                  {role.stakeholder_function.replace(/_/g, ' ')}
                </h3>
                <span className="text-xs font-mono bg-slate-800 px-2 py-0.5 rounded text-slate-300">
                  {role.total_feedback_count} reviews
                </span>
              </div>

              <div className="grid grid-cols-2 gap-2 text-xs pt-1">
                <div className="p-2.5 rounded-lg bg-slate-950/60 border border-slate-800">
                  <div className="text-[10px] text-slate-500 uppercase">Avg Relevance</div>
                  <div className="text-sm font-semibold text-emerald-400 mt-0.5">
                    {role.average_relevance ? role.average_relevance.toFixed(1) : 'N/A'} / 5.0
                  </div>
                </div>
                <div className="p-2.5 rounded-lg bg-slate-950/60 border border-slate-800">
                  <div className="text-[10px] text-slate-500 uppercase">Approval Rate</div>
                  <div className="text-sm font-semibold text-blue-400 mt-0.5">
                    {role.action_approval_rate ? `${Math.round(role.action_approval_rate * 100)}%` : '100%'}
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
