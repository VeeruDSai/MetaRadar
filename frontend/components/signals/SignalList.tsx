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
  const [debouncedSearchTerm, setDebouncedSearchTerm] = useState<string>('')
  const [sourceFilter, setSourceFilter] = useState<string>('')

  // Debounce search input so typing does not fire one request per keystroke.
  useEffect(() => {
    const timer = setTimeout(() => setDebouncedSearchTerm(searchTerm), 300)
    return () => clearTimeout(timer)
  }, [searchTerm])

  const loadSignals = useCallback(async (signal?: AbortSignal) => {
    setLoading(true)
    setError(null)
    try {
      const params: SignalFilterParams = {
        limit: 30,
        severity: severityFilter || undefined,
        entity: debouncedSearchTerm.trim() || undefined,
        source: sourceFilter || undefined,
      }
      const data = await fetchSignals(params, signal)
      if (signal?.aborted) return
      setSignals(data.signals)
      setTotal(data.total)
    } catch (err) {
      // Superseded requests are aborted by the effect cleanup; ignore them
      // so a slow earlier response can never clobber newer results.
      if (signal?.aborted || (err instanceof Error && err.name === 'AbortError')) return
      setError(formatError(err, 'Failed to fetch signals.'))
    } finally {
      if (!signal?.aborted) setLoading(false)
    }
  }, [severityFilter, debouncedSearchTerm, sourceFilter])

  useEffect(() => {
    const controller = new AbortController()
    loadSignals(controller.signal)
    return () => controller.abort()
  }, [loadSignals])

  const handleFeedback = async (feedback: any) => {
    await submitSignalFeedback(feedback)
  }

  return (
    <div className="space-y-6">
      {/* Header & Filter Controls */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <div className="text-[11px] font-semibold tracking-wider uppercase text-[var(--muted-foreground)] mb-0.5">
            Ingested Signal Intelligence
          </div>
          <h2 className="text-xl font-bold text-[var(--foreground)]">Live Signals ({total})</h2>
          <p className="text-xs text-[var(--muted-foreground)] mt-1">
            Real-time competitive signals parsed and prioritized across biomedical sources.
          </p>
        </div>

        <div className="flex items-center gap-2 flex-wrap">
          <input
            type="text"
            placeholder="Search signals or entities..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="px-3 py-1.5 rounded-lg bg-[var(--card)] border border-[var(--border)] text-xs text-[var(--foreground)] focus:outline-none focus:border-blue-500 shadow-xs"
          />

          <select
            value={severityFilter}
            onChange={(e) => setSeverityFilter(e.target.value)}
            className="px-3 py-1.5 rounded-lg bg-[var(--card)] border border-[var(--border)] text-xs text-[var(--foreground)] shadow-xs"
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
            className="px-3 py-1.5 rounded-lg bg-[var(--card)] border border-[var(--border)] text-xs text-[var(--foreground)] shadow-xs"
          >
            <option value="">All Sources</option>
            <option value="pubmed">PubMed</option>
            <option value="clinical_trials">ClinicalTrials.gov</option>
            <option value="fda">OpenFDA</option>
            <option value="ema">EMA RSS</option>
            <option value="newsapi">NewsAPI</option>
          </select>

          <button
            onClick={() => loadSignals()}
            className="px-3.5 py-1.5 rounded-lg bg-[var(--surface-muted)] hover:bg-[var(--surface-subtle)] text-xs text-[var(--foreground)] transition border border-[var(--border)]"
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
            <div key={i} className="h-36 rounded-xl bg-[var(--surface-subtle)] animate-pulse border border-[var(--border)]" />
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
