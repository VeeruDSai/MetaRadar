'use client'

import React, { useState, useEffect, useCallback } from 'react'
import type { Signal, SignalFilterParams } from '@/types/api'
import { fetchSignals, submitSignalFeedback } from '@/lib/api'
import { formatError, FormattedError } from '@/lib/errors'
import { SectionTitle, Card, Badge } from '@/components/metaradar'
import { SignalCard } from './SignalCard'
import { EvidenceDrawer } from '../common/EvidenceDrawer'
import { ErrorState } from '../common/ErrorState'
import { Activity, RefreshCw, Search } from 'lucide-react'

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

  // Debounce search input
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
    <>
      <SectionTitle
        eyebrow="Ingested Signal Intelligence"
        title={`Live Signals (${total})`}
        detail="Real-time competitive signals parsed and prioritized across biomedical sources."
      />

      {/* Filter Bar */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 mb-4">
        <div className="filter-bar flex-wrap items-center">
          <button
            className={severityFilter === '' ? 'filter-active' : ''}
            onClick={() => setSeverityFilter('')}
          >
            All Priorities
          </button>
          <button
            className={severityFilter === 'CRITICAL' ? 'filter-active' : ''}
            onClick={() => setSeverityFilter('CRITICAL')}
          >
            Critical
          </button>
          <button
            className={severityFilter === 'HIGH' ? 'filter-active' : ''}
            onClick={() => setSeverityFilter('HIGH')}
          >
            High
          </button>
          <button
            className={severityFilter === 'MEDIUM' ? 'filter-active' : ''}
            onClick={() => setSeverityFilter('MEDIUM')}
          >
            Medium
          </button>
          <button
            className={severityFilter === 'LOW' ? 'filter-active' : ''}
            onClick={() => setSeverityFilter('LOW')}
          >
            Low
          </button>
        </div>

        <div className="flex items-center gap-2 flex-wrap">
          <div className="flex items-center gap-1.5 px-2.5 py-1 rounded border border-[var(--border)] bg-[var(--surface)] text-xs text-[var(--foreground)]">
            <Search size={13} className="text-[var(--muted-foreground)]" />
            <input
              type="text"
              placeholder="Filter signals..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="bg-transparent border-0 outline-none text-xs text-[var(--foreground)] placeholder-[var(--muted-foreground)] w-36 sm:w-44"
            />
          </div>

          <select
            value={sourceFilter}
            onChange={(e) => setSourceFilter(e.target.value)}
            className="px-2.5 py-1.5 rounded border border-[var(--border)] bg-[var(--surface)] text-xs text-[var(--foreground)] outline-none"
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
            className="inline-flex items-center gap-1 px-3 py-1.5 rounded text-xs border border-[var(--border)] bg-[var(--surface)] text-[var(--foreground)] hover:border-[var(--signal)]"
          >
            <RefreshCw size={13} className={loading ? 'animate-spin' : ''} />
            <span>Refresh</span>
          </button>
        </div>
      </div>

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

      {loading && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {[1, 2, 3, 4].map((i) => (
            <Card key={i} className="animate-pulse h-40" />
          ))}
        </div>
      )}

      {!loading && !error && signals.length === 0 && (
        <Card className="empty-state">
          <Activity size={28} />
          <p>No signals matched filter criteria</p>
          <span>Try broadening your search term or clearing priority filters to view available signals.</span>
          {(severityFilter || searchTerm || sourceFilter) && (
            <button
              onClick={() => {
                setSeverityFilter('')
                setSearchTerm('')
                setSourceFilter('')
              }}
              className="mt-2 px-3.5 py-1.5 rounded text-xs font-semibold border border-[var(--border)] bg-[var(--surface-secondary)] text-[var(--foreground)] hover:border-[var(--signal)]"
            >
              Reset Filters
            </button>
          )}
        </Card>
      )}

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
    </>
  )
}
