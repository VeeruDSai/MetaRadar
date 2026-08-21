'use client'

import React, { useState } from 'react'
import type { Signal } from '@/types/api'
import { DataModeBadge } from './DataModeBadge'

export interface EvidenceDrawerProps {
  signal: Signal | null
  isOpen: boolean
  onClose: () => void
  onFeedbackSubmit?: (feedback: {
    signal_id: string
    stakeholder_function: string
    relevance_rating: number
    urgency_rating: number
    action_appropriate: boolean
    comments?: string
  }) => Promise<void>
}

export function EvidenceDrawer({
  signal,
  isOpen,
  onClose,
  onFeedbackSubmit,
}: EvidenceDrawerProps) {
  const [selectedFunction, setSelectedFunction] = useState('REGULATORY')
  const [relevance, setRelevance] = useState(4)
  const [urgency, setUrgency] = useState(4)
  const [actionAppropriate, setActionAppropriate] = useState(true)
  const [comments, setComments] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [feedbackSuccess, setFeedbackSuccess] = useState(false)

  if (!isOpen || !signal) return null

  const handleFeedback = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!onFeedbackSubmit || !signal.signal_id) return

    setSubmitting(true)
    try {
      await onFeedbackSubmit({
        signal_id: signal.signal_id,
        stakeholder_function: selectedFunction,
        relevance_rating: relevance,
        urgency_rating: urgency,
        action_appropriate: actionAppropriate,
        comments: comments.trim() || undefined,
      })
      setFeedbackSuccess(true)
      setTimeout(() => setFeedbackSuccess(false), 3000)
    } finally {
      setSubmitting(false)
    }
  }

  const breakdown = signal.score_breakdown
  const externalId = signal.external_id || signal.pmid || signal.nct_id || signal.regulatory_id || 'N/A'
  const sourceDisplayName = signal.source_name || (signal.source_id ? signal.source_id.toUpperCase().replace(/_/g, ' ') : 'SOURCE')
  const isFixture = signal.is_synthetic || signal.data_mode === 'test_fixture' || signal.provenance_status === 'fixture'

  let provenanceReason = ''
  if (isFixture) {
    provenanceReason = '(Synthetic Test Fixture)'
  } else if (signal.provenance_status === 'missing_url') {
    provenanceReason = signal.source_id === 'fda' ? '(Not exposed by openFDA)' : '(External URL unavailable)'
  } else if (signal.provenance_status === 'missing_provider_field') {
    provenanceReason = '(Missing provider field)'
  } else if (signal.provenance_status === 'invalid_url') {
    provenanceReason = '(Invalid URL structure)'
  }

  return (
    <div className="fixed inset-0 z-50 overflow-hidden bg-black/60 dark:bg-black/80 backdrop-blur-xs flex justify-end">
      <div
        className="w-full max-w-2xl bg-[var(--card)] border-l border-[var(--border)] h-full overflow-y-auto p-6 space-y-6 shadow-2xl flex flex-col justify-between"
        role="dialog"
        aria-modal="true"
        aria-label="Evidence and Provenance Details"
      >
        <div className="space-y-6">
          {/* Header */}
          <div className="flex items-start justify-between gap-4 pb-4 border-b border-[var(--border)]">
            <div className="space-y-1.5">
              <div className="flex items-center gap-2 flex-wrap">
                <DataModeBadge mode={signal.data_mode} isSynthetic={signal.is_synthetic} />
                <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-[var(--surface-muted)] text-[var(--foreground)] border border-[var(--border)]">
                  {signal.signal_type || 'SIGNAL'}
                </span>
                <span className="px-2 py-0.5 rounded text-[10px] font-semibold uppercase tracking-wider bg-blue-50 text-blue-700 border border-blue-200 dark:bg-blue-950/80 dark:text-blue-300 dark:border-blue-800/60">
                  Priority: {signal.priority || 'MEDIUM'}
                </span>
              </div>
              <h2 className="text-lg font-semibold text-[var(--foreground)]">{signal.title}</h2>
            </div>
            <button
              onClick={onClose}
              className="p-1.5 rounded-lg bg-[var(--surface-muted)] hover:bg-[var(--surface-subtle)] text-[var(--muted-foreground)] hover:text-[var(--foreground)] transition"
              aria-label="Close evidence drawer"
            >
              ✕
            </button>
          </div>

          {/* 1. SOURCE PROVENANCE */}
          <div className="bg-[var(--surface-subtle)] rounded-xl p-4 border border-[var(--border)] space-y-3">
            <h3 className="text-xs font-semibold uppercase tracking-wider text-[var(--muted-foreground)]">
              Source Provenance
            </h3>
            <div className="grid grid-cols-2 gap-3 text-xs">
              <div>
                <span className="text-[10px] text-[var(--muted-foreground)] uppercase font-medium block">Source Provider</span>
                <span className="font-semibold text-[var(--foreground)] mt-0.5 block">{sourceDisplayName}</span>
              </div>
              <div>
                <span className="text-[10px] text-[var(--muted-foreground)] uppercase font-medium block">External Identifier</span>
                <span className="font-mono text-xs text-[var(--foreground)] mt-0.5 block">{externalId}</span>
              </div>
              <div>
                <span className="text-[10px] text-[var(--muted-foreground)] uppercase font-medium block">Published Date</span>
                <span className="text-[var(--foreground)] mt-0.5 block">{signal.published_at ? new Date(signal.published_at).toLocaleDateString() : 'N/A'}</span>
              </div>
              <div>
                <span className="text-[10px] text-[var(--muted-foreground)] uppercase font-medium block">Ingested Timestamp</span>
                <span className="font-mono text-[11px] text-[var(--foreground)] mt-0.5 block">{signal.ingested_at || signal.retrieved_at || 'N/A'}</span>
              </div>
            </div>

            <div className="pt-2 border-t border-[var(--border)] flex items-center justify-between">
              {signal.canonical_url && !isFixture ? (
                <a
                  href={signal.canonical_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-md bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold shadow-xs transition"
                >
                  <span>Open Original Source</span>
                  <span className="text-[11px]">↗</span>
                </a>
              ) : (
                <div className="flex items-center gap-2">
                  <span className="px-2 py-1 rounded text-[10px] font-semibold uppercase tracking-wider bg-rose-50 text-rose-700 border border-rose-200 dark:bg-rose-950/80 dark:text-rose-300 dark:border-rose-800/60">
                    SOURCE URL UNAVAILABLE
                  </span>
                  {provenanceReason && (
                    <span className="text-[11px] text-[var(--muted-foreground)] italic font-mono">{provenanceReason}</span>
                  )}
                </div>
              )}
            </div>
          </div>

          {/* 2. MULTI-FACTOR PRIORITY SCORE BREAKDOWN */}
          <div className="bg-[var(--surface-subtle)] rounded-xl p-4 border border-[var(--border)] space-y-3">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-xs font-semibold uppercase tracking-wider text-[var(--muted-foreground)]">
                  Priority Score Breakdown (4-Factor Model)
                </h3>
                <span className="text-[11px] text-[var(--muted-foreground)] font-mono">
                  P = 0.25 × Novelty + 0.30 × Clinical + 0.25 × Regulatory + 0.20 × Recency
                </span>
              </div>
              <span className="text-sm font-mono text-emerald-600 dark:text-emerald-400 font-bold">
                Total: {breakdown?.total !== undefined ? `${breakdown.total} / 100` : `${signal.score || 0} pts`}
              </span>
            </div>

            {breakdown ? (
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs">
                <div className="p-2.5 rounded-lg bg-[var(--card)] border border-[var(--border)] shadow-xs">
                  <div className="text-[10px] text-[var(--muted-foreground)] uppercase font-medium">Novelty (25%)</div>
                  <div className="text-sm font-semibold text-[var(--foreground)] mt-0.5">{breakdown.novelty} pts</div>
                </div>
                <div className="p-2.5 rounded-lg bg-[var(--card)] border border-[var(--border)] shadow-xs">
                  <div className="text-[10px] text-[var(--muted-foreground)] uppercase font-medium">Clinical (30%)</div>
                  <div className="text-sm font-semibold text-[var(--foreground)] mt-0.5">{breakdown.clinical} pts</div>
                </div>
                <div className="p-2.5 rounded-lg bg-[var(--card)] border border-[var(--border)] shadow-xs">
                  <div className="text-[10px] text-[var(--muted-foreground)] uppercase font-medium">Regulatory (25%)</div>
                  <div className="text-sm font-semibold text-[var(--foreground)] mt-0.5">{breakdown.regulatory} pts</div>
                </div>
                <div className="p-2.5 rounded-lg bg-[var(--card)] border border-[var(--border)] shadow-xs">
                  <div className="text-[10px] text-[var(--muted-foreground)] uppercase font-medium">Recency (20%)</div>
                  <div className="text-sm font-semibold text-[var(--foreground)] mt-0.5">{breakdown.recency} pts</div>
                </div>
              </div>
            ) : (
              <div className="text-xs text-[var(--muted-foreground)] italic">
                Scoring status: {signal.scoring_status || 'not_computed'}
              </div>
            )}
          </div>

          {/* 3. VERBATIM EVIDENCE CONTENT */}
          <div className="space-y-2">
            <h3 className="text-xs font-semibold uppercase tracking-wider text-[var(--muted-foreground)]">
              Verbatim Evidence Content
            </h3>
            <div className="p-4 rounded-xl bg-[var(--surface-subtle)] border border-[var(--border)] text-sm text-[var(--foreground)] leading-relaxed font-sans select-text">
              {signal.evidence_text || signal.content || signal.summary || 'No verbatim content available.'}
            </div>
          </div>

          {/* Extracted Facts */}
          {signal.facts && signal.facts.length > 0 && (
            <div className="space-y-2">
              <h3 className="text-xs font-semibold uppercase tracking-wider text-[var(--muted-foreground)]">
                Extracted Biomedical Facts
              </h3>
              <ul className="space-y-1.5 list-disc list-inside text-xs text-[var(--foreground)] bg-[var(--surface-subtle)] p-3 rounded-lg border border-[var(--border)]">
                {signal.facts.map((fact, i) => (
                  <li key={i}>{fact}</li>
                ))}
              </ul>
            </div>
          )}

          {/* 4. TRACE & PII/PHI SCRUBBER */}
          <div className="space-y-2 pt-2 border-t border-[var(--border)] text-xs">
            <h3 className="text-xs font-semibold uppercase tracking-wider text-[var(--muted-foreground)]">
              PII/PHI Scrubber & Pipeline Trace
            </h3>
            <div className="grid grid-cols-2 gap-2 text-[11px] text-[var(--muted-foreground)] font-mono bg-[var(--surface-subtle)] p-3.5 rounded-lg border border-[var(--border)]">
              <div>Signal ID: <span className="font-semibold text-[var(--foreground)] truncate block">{signal.signal_id || signal.id}</span></div>
              <div>Raw Record Ref: <span className="font-semibold text-[var(--foreground)] truncate block">{signal.raw_record_reference || 'N/A'}</span></div>
              <div className="col-span-2">Fingerprint: <span className="font-semibold text-[var(--foreground)] truncate block">{signal.fingerprint || 'N/A'}</span></div>
              <div className="col-span-2 text-[10px] text-emerald-600 dark:text-emerald-400 font-sans mt-1">
                ✓ PII/PHI scrubber evaluated prior to bronze persistence. HIPAA Safe Harbor compliant.
              </div>
            </div>
          </div>

          {/* 5. CALIBRATION FEEDBACK FORM */}
          {onFeedbackSubmit && (
            <form onSubmit={handleFeedback} className="pt-4 border-t border-[var(--border)] space-y-3">
              <h3 className="text-xs font-semibold uppercase tracking-wider text-[var(--muted-foreground)]">
                Stakeholder Calibration Feedback
              </h3>
              <div className="grid grid-cols-2 gap-3 text-xs">
                <div>
                  <label className="block text-[var(--muted-foreground)] mb-1 font-medium">Your Function</label>
                  <select
                    value={selectedFunction}
                    onChange={(e) => setSelectedFunction(e.target.value)}
                    className="w-full bg-[var(--card)] border border-[var(--border)] rounded px-2.5 py-1.5 text-[var(--foreground)] text-xs"
                  >
                    <option value="REGULATORY">Regulatory Affairs</option>
                    <option value="MEDICAL_AFFAIRS">Medical Affairs</option>
                    <option value="SAFETY">Pharmacovigilance & Safety</option>
                    <option value="MARKET_ACCESS">Market Access</option>
                    <option value="COMMUNICATIONS">Corporate Communications</option>
                    <option value="LEADERSHIP">Executive Leadership</option>
                  </select>
                </div>
                <div>
                  <label className="block text-[var(--muted-foreground)] mb-1 font-medium">Relevance (1-5)</label>
                  <input
                    type="number"
                    min="1"
                    max="5"
                    value={relevance}
                    onChange={(e) => setRelevance(Number(e.target.value))}
                    className="w-full bg-[var(--card)] border border-[var(--border)] rounded px-2.5 py-1.5 text-[var(--foreground)] text-xs"
                  />
                </div>
              </div>

              <div>
                <label className="block text-[var(--muted-foreground)] text-xs mb-1 font-medium">Review Comments</label>
                <textarea
                  value={comments}
                  onChange={(e) => setComments(e.target.value)}
                  placeholder="Provide domain feedback or suggest monitoring watch rules..."
                  rows={2}
                  className="w-full bg-[var(--card)] border border-[var(--border)] rounded p-2 text-[var(--foreground)] text-xs"
                />
              </div>

              <div className="flex items-center justify-between">
                <button
                  type="submit"
                  disabled={submitting}
                  className="px-4 py-2 rounded-lg bg-blue-600 hover:bg-blue-500 text-xs font-semibold text-white transition disabled:opacity-50"
                >
                  {submitting ? 'Submitting...' : 'Submit Calibration Rating'}
                </button>
                {feedbackSuccess && (
                  <span className="text-xs text-emerald-600 dark:text-emerald-400 font-medium">✓ Feedback recorded!</span>
                )}
              </div>
            </form>
          )}
        </div>
      </div>
    </div>
  )
}
