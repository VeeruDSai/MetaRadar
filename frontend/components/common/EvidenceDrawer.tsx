'use client'

import React, { useState } from 'react'
import type { Signal } from '@/types/api'
import { Badge } from '@/components/metaradar'
import { DataModeBadge } from './DataModeBadge'
import { AlertTriangle, ExternalLink, X } from 'lucide-react'

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
  const [feedbackError, setFeedbackError] = useState<string | null>(null)

  if (!isOpen || !signal) return null

  const handleFeedback = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!onFeedbackSubmit || !signal.signal_id) return

    setSubmitting(true)
    setFeedbackSuccess(false)
    setFeedbackError(null)
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
    } catch (err) {
      setFeedbackError(
        err instanceof Error && err.message
          ? `Feedback submission failed: ${err.message}`
          : 'Feedback submission failed. Please try again.'
      )
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

  const priorityKey = (signal.severity || signal.priority || 'medium').toLowerCase() as 'critical' | 'high' | 'medium' | 'low' | 'neutral'

  return (
    <div className="drawer-backdrop" onClick={onClose}>
      <aside
        className="signal-drawer overflow-y-auto max-h-screen"
        style={{ width: 'min(640px, 100%)' }}
        onClick={(e) => e.stopPropagation()}
        role="dialog"
        aria-modal="true"
        aria-label="Evidence and Provenance Details"
      >
        <div className="drawer-top">
          <div className="flex items-center gap-2 flex-wrap">
            <DataModeBadge mode={signal.data_mode} isSynthetic={signal.is_synthetic} />
            <Badge tone="neutral">{signal.signal_type || 'SIGNAL'}</Badge>
            <Badge tone={priorityKey}>Priority: {signal.priority || signal.severity || 'MEDIUM'}</Badge>
          </div>
          <button
            onClick={onClose}
            className="icon-button"
            aria-label="Close evidence drawer"
          >
            <X size={18} />
          </button>
        </div>

        <h2>{signal.title}</h2>
        <p className="drawer-summary">{signal.summary || signal.content}</p>

        {/* 1. SOURCE PROVENANCE */}
        <div className="drawer-sections">
          <h3>Source Provenance</h3>
          <div
            className="p-3.5 rounded border border-[var(--border)] grid grid-cols-2 gap-3 text-xs"
            style={{ background: 'var(--surface-secondary)' }}
          >
            <div>
              <span className="text-[10px] text-[var(--muted-foreground)] uppercase font-semibold block">Source Provider</span>
              <span className="font-semibold text-[var(--foreground)] mt-0.5 block">{sourceDisplayName}</span>
            </div>
            <div>
              <span className="text-[10px] text-[var(--muted-foreground)] uppercase font-semibold block">External Identifier</span>
              <span className="font-mono text-xs text-[var(--foreground)] mt-0.5 block">{externalId}</span>
            </div>
            <div>
              <span className="text-[10px] text-[var(--muted-foreground)] uppercase font-semibold block">Published Date</span>
              <span className="text-[var(--foreground)] mt-0.5 block">{signal.published_at ? new Date(signal.published_at).toLocaleDateString() : 'N/A'}</span>
            </div>
            <div>
              <span className="text-[10px] text-[var(--muted-foreground)] uppercase font-semibold block">Ingested Timestamp</span>
              <span className="font-mono text-[10px] text-[var(--foreground)] mt-0.5 block">{signal.ingested_at || signal.retrieved_at || 'N/A'}</span>
            </div>
          </div>

          <div className="mt-2">
            {signal.canonical_url && !signal.canonical_url.includes('metaradar.internal') ? (
              <a
                href={signal.canonical_url}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded text-xs font-semibold text-white transition hover:opacity-90"
                style={{ background: 'var(--primary)' }}
              >
                <span>Open Original Source</span>
                <ExternalLink size={13} />
              </a>
            ) : signal.is_synthetic || signal.provenance_status === 'fixture' ? (
              <div className="flex items-center gap-2">
                <Badge tone="low">TEST FIXTURE (SYNTHETIC BENCHMARK)</Badge>
                <span className="text-[11px] text-[var(--muted-foreground)] italic font-mono">
                  Offline pipeline validation baseline
                </span>
              </div>
            ) : (
              <div className="flex items-center gap-2">
                <Badge tone="high">SOURCE URL UNAVAILABLE</Badge>
                {provenanceReason && (
                  <span className="text-[11px] text-[var(--muted-foreground)] italic font-mono">{provenanceReason}</span>
                )}
              </div>
            )}
          </div>

          {/* 2. MULTI-FACTOR PRIORITY SCORE BREAKDOWN */}
          <h3 className="mt-4">Priority Score Breakdown (4-Factor Model)</h3>
          <p className="text-[11px] text-[var(--muted-foreground)] font-mono m-0 mb-2">
            P = 0.25 × Novelty + 0.30 × Clinical + 0.25 × Regulatory + 0.20 × Recency
          </p>

          {breakdown ? (
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs">
              <div className="p-2.5 rounded border border-[var(--border)]" style={{ background: 'var(--surface-secondary)' }}>
                <div className="text-[9px] text-[var(--muted-foreground)] uppercase font-semibold">Novelty (25%)</div>
                <div className="text-sm font-semibold text-[var(--foreground)] mt-0.5">{breakdown.novelty} pts</div>
              </div>
              <div className="p-2.5 rounded border border-[var(--border)]" style={{ background: 'var(--surface-secondary)' }}>
                <div className="text-[9px] text-[var(--muted-foreground)] uppercase font-semibold">Clinical (30%)</div>
                <div className="text-sm font-semibold text-[var(--foreground)] mt-0.5">{breakdown.clinical} pts</div>
              </div>
              <div className="p-2.5 rounded border border-[var(--border)]" style={{ background: 'var(--surface-secondary)' }}>
                <div className="text-[9px] text-[var(--muted-foreground)] uppercase font-semibold">Regulatory (25%)</div>
                <div className="text-sm font-semibold text-[var(--foreground)] mt-0.5">{breakdown.regulatory} pts</div>
              </div>
              <div className="p-2.5 rounded border border-[var(--border)]" style={{ background: 'var(--surface-secondary)' }}>
                <div className="text-[9px] text-[var(--muted-foreground)] uppercase font-semibold">Recency (20%)</div>
                <div className="text-sm font-semibold text-[var(--foreground)] mt-0.5">{breakdown.recency} pts</div>
              </div>
            </div>
          ) : (
            <div className="text-xs text-[var(--muted-foreground)] italic">
              Scoring status: {signal.scoring_status || 'not_computed'}
            </div>
          )}

          {/* 3. VERBATIM EVIDENCE CONTENT */}
          <h3 className="mt-4">Verbatim Evidence Content</h3>
          <div
            className="p-3.5 rounded border border-[var(--border)] text-xs text-[var(--foreground)] leading-relaxed font-sans select-text"
            style={{ background: 'var(--surface-secondary)' }}
          >
            {signal.evidence_text || signal.content || signal.summary || 'No verbatim content available.'}
          </div>

          {/* 4. TRACE & PII/PHI SCRUBBER */}
          <h3 className="mt-4">PII/PHI Scrubber & Pipeline Trace</h3>
          <div
            className="grid grid-cols-2 gap-2 text-[10px] text-[var(--muted-foreground)] font-mono p-3 rounded border border-[var(--border)]"
            style={{ background: 'var(--surface-secondary)' }}
          >
            <div>Signal ID: <span className="font-semibold text-[var(--foreground)] truncate block">{signal.signal_id || signal.id}</span></div>
            <div>Raw Record Ref: <span className="font-semibold text-[var(--foreground)] truncate block">{signal.raw_record_reference || 'N/A'}</span></div>
            <div className="col-span-2">Fingerprint: <span className="font-semibold text-[var(--foreground)] truncate block">{signal.fingerprint || 'N/A'}</span></div>
            {signal.pii_scrubbed === true ? (
              <div className="col-span-2 text-[10px] font-sans mt-1" style={{ color: 'var(--success)' }}>
                ✓ PII/PHI scrubber evaluated prior to bronze persistence.
              </div>
            ) : (
              <div className="col-span-2 text-[10px] font-sans italic mt-1 text-[var(--muted-foreground)]">
                PII/PHI scrub status checked.
              </div>
            )}
          </div>

          {/* 5. CALIBRATION FEEDBACK FORM */}
          {onFeedbackSubmit && (
            <form onSubmit={handleFeedback} className="pt-3 border-t border-[var(--border)] space-y-3 mt-3">
              <h3>Stakeholder Calibration Feedback</h3>
              <div className="grid grid-cols-2 sm:grid-cols-3 gap-2 text-xs">
                <div>
                  <label className="block text-[var(--muted-foreground)] mb-1 font-semibold text-[10px]">Your Function</label>
                  <select
                    value={selectedFunction}
                    onChange={(e) => setSelectedFunction(e.target.value)}
                    className="w-full border border-[var(--border)] rounded px-2.5 py-1.5 text-xs text-[var(--foreground)] outline-none"
                    style={{ background: 'var(--surface)' }}
                  >
                    <option value="REGULATORY">Regulatory Affairs</option>
                    <option value="MEDICAL_AFFAIRS">Medical Affairs</option>
                    <option value="SAFETY">Safety</option>
                    <option value="MARKET_ACCESS">Market Access</option>
                    <option value="COMMUNICATIONS">Communications</option>
                    <option value="LEADERSHIP">Leadership</option>
                  </select>
                </div>
                <div>
                  <label className="block text-[var(--muted-foreground)] mb-1 font-semibold text-[10px]">Relevance (1-5)</label>
                  <input
                    type="number"
                    min="1"
                    max="5"
                    value={relevance}
                    onChange={(e) => setRelevance(Number(e.target.value))}
                    className="w-full border border-[var(--border)] rounded px-2.5 py-1.5 text-xs text-[var(--foreground)] outline-none"
                    style={{ background: 'var(--surface)' }}
                  />
                </div>
                <div>
                  <label className="block text-[var(--muted-foreground)] mb-1 font-semibold text-[10px]">Urgency (1-5)</label>
                  <input
                    type="number"
                    min="1"
                    max="5"
                    value={urgency}
                    onChange={(e) => setUrgency(Number(e.target.value))}
                    className="w-full border border-[var(--border)] rounded px-2.5 py-1.5 text-xs text-[var(--foreground)] outline-none"
                    style={{ background: 'var(--surface)' }}
                  />
                </div>
              </div>

              <div>
                <label className="block text-[var(--muted-foreground)] text-[10px] font-semibold mb-1">Review Comments</label>
                <textarea
                  value={comments}
                  onChange={(e) => setComments(e.target.value)}
                  placeholder="Provide domain feedback or suggest monitoring watch rules..."
                  rows={2}
                  className="w-full border border-[var(--border)] rounded p-2 text-xs text-[var(--foreground)] outline-none"
                  style={{ background: 'var(--surface)' }}
                />
              </div>

              <div className="flex items-center justify-between gap-2 flex-wrap pt-1">
                <button
                  type="submit"
                  disabled={submitting}
                  className="px-4 py-1.5 rounded text-xs font-semibold text-white transition disabled:opacity-50"
                  style={{ background: 'var(--primary)' }}
                >
                  {submitting ? 'Submitting...' : 'Submit Calibration Rating'}
                </button>
                {feedbackSuccess && (
                  <span className="text-xs font-medium" style={{ color: 'var(--success)' }}>✓ Feedback recorded!</span>
                )}
                {feedbackError && (
                  <span role="alert" className="text-xs font-medium" style={{ color: 'var(--danger)' }}>
                    {feedbackError}
                  </span>
                )}
              </div>
            </form>
          )}
        </div>
      </aside>
    </div>
  )
}
