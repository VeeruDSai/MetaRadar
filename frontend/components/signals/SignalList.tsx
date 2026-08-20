'use client'

import React, { useState, useEffect, useCallback } from 'react'
import type { Signal, SignalFilterParams } from '@/types/api'
import { fetchSignals, submitSignalFeedback } from '@/lib/api'
import { formatError, FormattedError } from '@/lib/errors'
import { SignalCard } from './SignalCard'
import { EvidenceDrawer } from '../common/EvidenceDrawer'
import { ErrorState } from '../common/ErrorState'
import { EmptyState } from '../common/EmptyState'

export function SignalList() {
  const [signals, setSignals] = useState<Signal[]>([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<FormattedError | null>(null)
  const [selectedSignal, setSelectedSignal] = useState<Signal | null>(null)

  // Filters
  const [severityFilter, setSeverityFilter] = useState<string>('')
  const [searchTerm, setSearchTerm] = useState<string>('')
  const [sourceFilter, setSourceFilter] = useState<string>('')

  const loadSignals = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const params: SignalFilterParams = {
        limit: 30,
        severity: severityFilter || undefined,
        entity: searchTerm.trim() || undefined,
        source: sourceFilter || undefined,
      }
      const data = await fetchSignals(params)
      setSignals(data.signals)
      setTotal(data.total)
    } catch (err) {
      setError(formatError(err, 'Failed to fetch signals.'))
    } finally {
      setLoading(false)
    }
  }, [severityFilter, searchTerm, sourceFilter])

  useEffect(() => {
    loadSignals()
  }, [loadSignals])

  const handleFeedback = async (feedback: any) => {
    await submitSignalFeedback(feedback)
  }

  return (
    <div className="space-y-6">
      {/* Header & Filter Controls */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-slate-100">Live Intelligence Signals</h1>
          <p className="text-xs text-slate-400 mt-1">
            Real-time competitive signals parsed and prioritized across biomedical sources.
          </p>
        </div>

        <div className="flex items-center gap-2 flex-wrap">
          <input
            type="text"
            placeholder="Search signals or entities..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-800 text-xs text-slate-200 focus:outline-none focus:border-blue-500"
          />

          <select
            value={severityFilter}
            onChange={(e) => setSeverityFilter(e.target.value)}
            className="px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-800 text-xs text-slate-200"
          >
            <option value="">All Priorities</option>
            <option value="CRITICAL">Critical</option>
            <option value="HIGH">High</option>
            <option value="MEDIUM">Medium</option>
            <option value="LOW">Low</option>
          </select>

          <select
            value={sourceFilter}
            onChange={(e) => setSourceFilter(e.target.value)}
            className="px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-800 text-xs text-slate-200"
          >
            <option value="">All Sources</option>
            <option value="pubmed">PubMed</option>
            <option value="clinical_trials">ClinicalTrials.gov</option>
            <option value="openfda">OpenFDA</option>
            <option value="ema_rss">EMA RSS</option>
            <option value="newsapi">NewsAPI</option>
          </select>

          <button
            onClick={loadSignals}
            className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-xs text-slate-300 transition"
          >
            Refresh
          </button>
        </div>
      </div>

      {/* Error state */}
      {error && (
        <ErrorState
          title={error.title}
          message={error.message}
          requestId={error.requestId}
          endpoint={error.endpoint}
          statusCode={error.statusCode}
          onRetry={loadSignals}
        />
      )}

      {/* Loading state */}
      {loading && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="h-36 rounded-xl bg-slate-900/40 animate-pulse border border-slate-800/60" />
          ))}
        </div>
      )}

      {/* Empty state */}
      {!loading && !error && signals.length === 0 && (
        <EmptyState
          title="No signals match the selected filters"
          description="Try broadening your search term or clearing priority filters to view available signals."
          actionLabel="Clear Filters"
          onAction={() => {
            setSeverityFilter('')
            setSearchTerm('')
            setSourceFilter('')
          }}
        />
      )}

      {/* Grid of Signal Cards */}
      {!loading && !error && signals.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {signals.map((sig) => (
            <SignalCard
              key={sig.id}
              signal={sig}
              onSelect={(s) => setSelectedSignal(s)}
            />
          ))}
        </div>
      )}

      {/* Provenance Evidence Drawer */}
      <EvidenceDrawer
        signal={selectedSignal}
        isOpen={Boolean(selectedSignal)}
        onClose={() => setSelectedSignal(null)}
        onFeedbackSubmit={handleFeedback}
      />
    </div>
  )
}
