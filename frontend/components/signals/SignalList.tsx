'use client'

import React, { useState, useEffect, useCallback, useMemo } from 'react'
import type { Signal, SignalFilterParams } from '@/types/api'
import { fetchSignals, submitSignalFeedback } from '@/lib/api'
import { formatError, FormattedError } from '@/lib/errors'
import { useAuth } from '@/context/AuthContext'
import { SectionTitle, Card, Badge } from '@/components/metaradar'
import { SignalCard, getSignalFunction, getSourceAuthority } from './SignalCard'
import { EvidenceDrawer } from '../common/EvidenceDrawer'
import { ErrorState } from '../common/ErrorState'
import {
  Activity,
  CheckCircle,
  Filter,
  Globe,
  LayoutGrid,
  Network,
  RefreshCw,
  Search,
  Shield,
  ShieldAlert,
  SlidersHorizontal,
} from 'lucide-react'

export function SignalList() {
  const { role } = useAuth()
  const [signals, setSignals] = useState<Signal[]>([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<FormattedError | null>(null)
  const [selectedSignal, setSelectedSignal] = useState<Signal | null>(null)

  // Filters
  const [severityFilter, setSeverityFilter] = useState<string>('')
  const [functionFilter, setFunctionFilter] = useState<string>('')
  const [authorityFilter, setAuthorityFilter] = useState<string>('')
  const [reviewFilter, setReviewFilter] = useState<string>('')
  const [searchTerm, setSearchTerm] = useState<string>('')
  const [debouncedSearchTerm, setDebouncedSearchTerm] = useState<string>('')
  const [sourceFilter, setSourceFilter] = useState<string>('')

  // Debounce search input
  useEffect(() => {
    const timer = setTimeout(() => setDebouncedSearchTerm(searchTerm), 300)
    return () => clearTimeout(timer)
  }, [searchTerm])

  const loadSignals = useCallback(
    async (signal?: AbortSignal) => {
      setLoading(true)
      setError(null)
      try {
        const isAbortSignal = typeof AbortSignal !== 'undefined' && signal instanceof AbortSignal
        const activeSignal = isAbortSignal ? signal : undefined
        const isPrivileged = ['LEADERSHIP', 'ADMIN', 'DEVELOPER'].includes(role?.toUpperCase() || '')
        const params: SignalFilterParams = {
          limit: 50,
          severity: severityFilter || undefined,
          entity: debouncedSearchTerm.trim() || undefined,
          source: sourceFilter || undefined,
          ...(isPrivileged ? { all_functions: true } : {}),
        }
        const data = await fetchSignals(params, activeSignal)
        if (activeSignal?.aborted) return
        setSignals(data.signals)
        setTotal(data.total)
      } catch (err) {
        if (signal instanceof AbortSignal && signal.aborted) return
        if (err instanceof Error && err.name === 'AbortError') return
        setError(formatError(err, 'Failed to fetch signals.'))
      } finally {
        if (!(signal instanceof AbortSignal && signal.aborted)) setLoading(false)
      }
    },
    [severityFilter, debouncedSearchTerm, sourceFilter, role]
  )

  useEffect(() => {
    const controller = new AbortController()
    loadSignals(controller.signal)
    return () => controller.abort()
  }, [loadSignals])

  const handleFeedback = async (feedback: any) => {
    await submitSignalFeedback(feedback)
  }

  // Client-side functional and authority refinements
  const filteredSignals = useMemo(() => {
    return signals.filter((sig) => {
      if (functionFilter) {
        const { functionName } = getSignalFunction(sig)
        if (!functionName.toLowerCase().includes(functionFilter.toLowerCase())) {
          return false
        }
      }
      if (authorityFilter) {
        const auth = getSourceAuthority(sig.source_id, sig.source_name)
        if (auth.tier !== authorityFilter) {
          return false
        }
      }
      if (reviewFilter) {
        const st = (sig.status || 'pending').toLowerCase()
        if (!st.includes(reviewFilter.toLowerCase())) {
          return false
        }
      }
      return true
    })
  }, [signals, functionFilter, authorityFilter, reviewFilter])

  return (
    <>
      <SectionTitle
        eyebrow="Decision Intelligence Workspace"
        title={`Priority Signals (${filteredSignals.length})`}
        detail="Evidence-grounded competitive intelligence parsed, scored, and routed for decisive action."
      />

      {/* Decision Intelligence Filter Toolbar */}
      <div className="p-4 rounded-[var(--radius-md,8px)] bg-[var(--surface)] border border-[var(--border)] mb-5 flex flex-col gap-3.5">
        {/* Priority and Function Filter Buttons */}
        <div className="flex items-center justify-between gap-3 flex-wrap">
          <div className="flex items-center gap-1.5 flex-wrap">
            <span className="text-xs font-semibold text-[var(--muted-foreground)] mr-1">
              Priority:
            </span>
            {[
              { label: 'All', val: '' },
              { label: 'Critical', val: 'CRITICAL' },
              { label: 'High', val: 'HIGH' },
              { label: 'Medium', val: 'MEDIUM' },
              { label: 'Low', val: 'LOW' },
            ].map(({ label, val }) => (
              <button
                key={val}
                type="button"
                onClick={() => setSeverityFilter(val)}
                className={`px-2.5 py-1 rounded text-xs font-semibold border transition-all ${
                  severityFilter === val
                    ? 'bg-[var(--primary)] text-[var(--primary-foreground)] border-[var(--primary)]'
                    : 'bg-[var(--surface-secondary)] text-[var(--muted-foreground)] border-[var(--border)] hover:text-[var(--foreground)]'
                }`}
              >
                {label}
              </button>
            ))}
          </div>

          <div className="flex items-center gap-2 flex-wrap">
            <div className="flex items-center gap-1.5 px-2.5 py-1 rounded border border-[var(--border)] bg-[var(--surface-secondary)] text-xs text-[var(--foreground)]">
              <Search size={13} className="text-[var(--muted-foreground)]" />
              <input
                type="text"
                placeholder="Search signals, therapies, trials..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="bg-transparent border-0 outline-none text-xs text-[var(--foreground)] placeholder:text-[var(--muted-foreground)] w-44 sm:w-56"
              />
            </div>

            <button
              onClick={() => loadSignals()}
              className="inline-flex items-center gap-1 px-3 py-1.5 rounded text-xs font-semibold border border-[var(--border)] bg-[var(--surface-secondary)] text-[var(--foreground)] hover:border-[var(--primary)] transition"
            >
              <RefreshCw size={13} className={loading ? 'animate-spin' : ''} />
              <span>Refresh</span>
            </button>
          </div>
        </div>

        {/* Secondary Dimension Filters: Function, Source Authority, Review Status */}
        <div className="flex items-center gap-3 pt-2.5 border-t border-[var(--border)] flex-wrap text-xs">
          <div className="flex items-center gap-1.5">
            <Network size={13} className="text-[var(--primary)] shrink-0" />
            <select
              value={functionFilter}
              onChange={(e) => setFunctionFilter(e.target.value)}
              className="px-2 py-1 rounded border border-[var(--border)] bg-[var(--surface-secondary)] text-xs text-[var(--foreground)] outline-none"
            >
              <option value="">All Functions</option>
              <option value="regulatory">Regulatory Affairs</option>
              <option value="medical">Medical Affairs</option>
              <option value="safety">Safety & PV</option>
              <option value="market">Market Access & Pricing</option>
              <option value="legal">Legal & IP</option>
            </select>
          </div>

          <div className="flex items-center gap-1.5">
            <Shield size={13} className="text-[var(--success)] shrink-0" />
            <select
              value={authorityFilter}
              onChange={(e) => setAuthorityFilter(e.target.value)}
              className="px-2 py-1 rounded border border-[var(--border)] bg-[var(--surface-secondary)] text-xs text-[var(--foreground)] outline-none"
            >
              <option value="">All Credibility Tiers</option>
              <option value="authoritative">Authoritative Only (Regulatory, Registries, Journals)</option>
              <option value="discovery">Discovery Only (NewsAPI, Web Feeds)</option>
            </select>
          </div>

          <div className="flex items-center gap-1.5">
            <Globe size={13} className="text-[var(--muted-foreground)] shrink-0" />
            <select
              value={sourceFilter}
              onChange={(e) => setSourceFilter(e.target.value)}
              className="px-2 py-1 rounded border border-[var(--border)] bg-[var(--surface-secondary)] text-xs text-[var(--foreground)] outline-none"
            >
              <option value="">All Sources</option>
              <option value="clinical_trials">ClinicalTrials.gov</option>
              <option value="pubmed">PubMed E-utilities</option>
              <option value="fda">OpenFDA Drug Events</option>
              <option value="ema">EMA RSS Feed</option>
              <option value="newsapi">NewsAPI Global Feed</option>
              <option value="fierce_pharma">Fierce Pharma</option>
              <option value="biopharma_dive">BioPharma Dive</option>
              <option value="et_pharma">ET Pharma (India)</option>
            </select>
          </div>

          {(severityFilter || functionFilter || authorityFilter || sourceFilter || searchTerm) && (
            <button
              onClick={() => {
                setSeverityFilter('')
                setFunctionFilter('')
                setAuthorityFilter('')
                setSourceFilter('')
                setSearchTerm('')
              }}
              className="text-[11px] font-semibold text-[var(--primary)] hover:underline ml-auto"
            >
              Clear All Filters
            </button>
          )}
        </div>
      </div>

      {error && (
        <ErrorState
          title={error.title}
          message={error.message}
          requestId={error.requestId}
          endpoint={error.endpoint}
          statusCode={error.statusCode}
          onRetry={() => loadSignals()}
        />
      )}

      {loading && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {[1, 2, 3, 4].map((i) => (
            <Card key={i} className="animate-pulse h-56" />
          ))}
        </div>
      )}

      {!loading && !error && filteredSignals.length === 0 && (
        <Card className="empty-state">
          <Activity size={32} className="text-[var(--muted-foreground)]" />
          <p className="font-semibold text-sm">No signals matched the selected criteria</p>
          <span className="text-xs text-[var(--muted-foreground)]">
            Broaden your search or adjust the priority and functional filters to view signals.
          </span>
          <button
            onClick={() => {
              setSeverityFilter('')
              setFunctionFilter('')
              setAuthorityFilter('')
              setSourceFilter('')
              setSearchTerm('')
            }}
            className="mt-3 px-3.5 py-1.5 rounded text-xs font-semibold border border-[var(--border)] bg-[var(--surface-secondary)] text-[var(--foreground)] hover:border-[var(--primary)]"
          >
            Reset Filters
          </button>
        </Card>
      )}

      {!loading && !error && filteredSignals.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4.5">
          {filteredSignals.map((sig) => (
            <SignalCard
              key={sig.id}
              signal={sig}
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
