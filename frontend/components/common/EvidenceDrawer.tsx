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

  return (
    <div className="fixed inset-0 z-50 overflow-hidden bg-slate-950/80 backdrop-blur-sm flex justify-end">
      <div
        className="w-full max-w-2xl bg-slate-900 border-l border-slate-800 h-full overflow-y-auto p-6 space-y-6 shadow-2xl flex flex-col justify-between"
        role="dialog"
        aria-modal="true"
        aria-label="Evidence and Provenance Details"
      >
        <div className="space-y-6">
          {/* Header */}
          <div className="flex items-start justify-between gap-4 pb-4 border-b border-slate-800">
            <div className="space-y-1.5">
              <div className="flex items-center gap-2 flex-wrap">
                <DataModeBadge mode={signal.data_mode} isSynthetic={signal.is_synthetic} />
                <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-slate-800 text-slate-300">
                  {signal.signal_type || 'SIGNAL'}
                </span>
                <span className="px-2 py-0.5 rounded text-[10px] font-semibold uppercase tracking-wider bg-blue-950/80 text-blue-300 border border-blue-800/60">
                  Priority: {signal.priority || 'MEDIUM'}
                </span>
              </div>
              <h2 className="text-lg font-semibold text-slate-100">{signal.title}</h2>
            </div>
            <button
              onClick={onClose}
              className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-slate-200 transition"
              aria-label="Close evidence drawer"
            >
              ✕
            </button>
          </div>

          {/* Multi-Factor Priority Score Breakdown */}
          <div className="bg-slate-950/60 rounded-xl p-4 border border-slate-800/80 space-y-3">
            <div className="flex items-center justify-between">
              <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-400">
                Priority Score Breakdown
              </h3>
              <span className="text-xs font-mono text-emerald-400 font-medium">
                Total: {breakdown?.total !== undefined ? `${breakdown.total} / 100` : `${signal.score || 50} pts`}
              </span>
            </div>

            {breakdown ? (
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs">
                <div className="p-2.5 rounded-lg bg-slate-900 border border-slate-800">
                  <div className="text-[10px] text-slate-500 uppercase">Novelty (25%)</div>
                  <div className="text-sm font-semibold text-slate-200 mt-0.5">{breakdown.novelty} pts</div>
                </div>
                <div className="p-2.5 rounded-lg bg-slate-900 border border-slate-800">
                  <div className="text-[10px] text-slate-500 uppercase">Clinical (30%)</div>
                  <div className="text-sm font-semibold text-slate-200 mt-0.5">{breakdown.clinical} pts</div>
                </div>
                <div className="p-2.5 rounded-lg bg-slate-900 border border-slate-800">
                  <div className="text-[10px] text-slate-500 uppercase">Regulatory (25%)</div>
                  <div className="text-sm font-semibold text-slate-200 mt-0.5">{breakdown.regulatory} pts</div>
                </div>
                <div className="p-2.5 rounded-lg bg-slate-900 border border-slate-800">
                  <div className="text-[10px] text-slate-500 uppercase">Recency (20%)</div>
                  <div className="text-sm font-semibold text-slate-200 mt-0.5">{breakdown.recency} pts</div>
                </div>
              </div>
            ) : (
              <div className="text-xs text-slate-500 italic">
                Scoring status: {signal.scoring_status || 'not_computed'}
              </div>
            )}
          </div>

          {/* Verbatim Content & Excerpt */}
          <div className="space-y-2">
            <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-400">
              Verbatim Evidence Content
            </h3>
            <div className="p-4 rounded-xl bg-slate-950/80 border border-slate-800 text-sm text-slate-300 leading-relaxed font-sans select-text">
              {signal.content || signal.summary || 'No verbatim content available.'}
            </div>
          </div>

          {/* Extracted Facts & Structured Reasoning */}
          {signal.facts && signal.facts.length > 0 && (
            <div className="space-y-2">
              <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-400">
                Extracted Biomedical Facts
              </h3>
              <ul className="space-y-1.5 list-disc list-inside text-xs text-slate-300 bg-slate-950/40 p-3 rounded-lg border border-slate-800">
                {signal.facts.map((fact, i) => (
                  <li key={i}>{fact}</li>
                ))}
              </ul>
            </div>
          )}

          {/* Interpretation & Speculation */}
          {(signal.interpretation || signal.speculation) && (
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
              {signal.interpretation && (
                <div className="p-3 rounded-lg bg-slate-950/50 border border-slate-800 space-y-1">
                  <span className="text-[10px] font-semibold uppercase text-blue-400">[INFERENCE] Interpretation</span>
                  <p className="text-slate-300">{signal.interpretation}</p>
                </div>
              )}
              {signal.speculation && (
                <div className="p-3 rounded-lg bg-slate-950/50 border border-slate-800 space-y-1">
                  <span className="text-[10px] font-semibold uppercase text-amber-400">[SPECULATION] Strategic Context</span>
                  <p className="text-slate-300">{signal.speculation}</p>
                </div>
              )}
            </div>
          )}

          {/* Provenance Metadata */}
          <div className="space-y-2 pt-2 border-t border-slate-800 text-xs">
            <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-400">
              Ingestion Provenance
            </h3>
            <div className="grid grid-cols-2 gap-2 text-[11px] text-slate-400 font-mono">
              <div>Source ID: <span className="text-slate-200">{signal.source_id || 'N/A'}</span></div>
              <div>Published: <span className="text-slate-200">{signal.published_at || 'N/A'}</span></div>
              <div>Signal ID: <span className="text-slate-200 truncate">{signal.signal_id || signal.id}</span></div>
              <div>Fingerprint: <span className="text-slate-200 truncate">{signal.fingerprint || 'N/A'}</span></div>
              {signal.canonical_url && (
                <div className="col-span-2">
                  URL:{' '}
                  <a
                    href={signal.canonical_url}
                    target="_blank"
                    rel="noreferrer"
                    className="text-blue-400 hover:underline break-all"
                  >
                    {signal.canonical_url}
                  </a>
                </div>
              )}
            </div>
          </div>

          {/* Calibration Feedback Form */}
          {onFeedbackSubmit && (
            <form onSubmit={handleFeedback} className="pt-4 border-t border-slate-800 space-y-3">
              <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-400">
                Stakeholder Calibration Feedback
              </h3>
              <div className="grid grid-cols-2 gap-3 text-xs">
                <div>
                  <label className="block text-slate-400 mb-1">Your Function</label>
                  <select
                    value={selectedFunction}
                    onChange={(e) => setSelectedFunction(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded px-2.5 py-1.5 text-slate-200 text-xs"
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
                  <label className="block text-slate-400 mb-1">Relevance (1-5)</label>
                  <input
                    type="number"
                    min="1"
                    max="5"
                    value={relevance}
                    onChange={(e) => setRelevance(Number(e.target.value))}
                    className="w-full bg-slate-950 border border-slate-800 rounded px-2.5 py-1.5 text-slate-200 text-xs"
                  />
                </div>
              </div>

              <div>
                <label className="block text-slate-400 text-xs mb-1">Review Comments</label>
                <textarea
                  value={comments}
                  onChange={(e) => setComments(e.target.value)}
                  placeholder="Provide domain feedback or suggest monitoring watch rules..."
                  rows={2}
                  className="w-full bg-slate-950 border border-slate-800 rounded p-2 text-slate-200 text-xs"
                />
              </div>

              <div className="flex items-center justify-between">
                <button
                  type="submit"
                  disabled={submitting}
                  className="px-4 py-2 rounded-lg bg-blue-600 hover:bg-blue-500 text-xs font-medium text-white transition disabled:opacity-50"
                >
                  {submitting ? 'Submitting...' : 'Submit Calibration Rating'}
                </button>
                {feedbackSuccess && (
                  <span className="text-xs text-emerald-400 font-medium">✓ Feedback recorded!</span>
                )}
              </div>
            </form>
          )}
        </div>
      </div>
    </div>
  )
}
