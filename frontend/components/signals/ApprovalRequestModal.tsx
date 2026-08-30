'use client'

import React, { useState } from 'react'
import {
  ShieldAlert,
  Send,
  X,
  Loader2,
  CheckCircle2,
  AlertTriangle,
  Clock,
} from 'lucide-react'
import type { Signal, ApprovalRequest } from '@/types/api'
import { requestSignalApproval } from '@/lib/api'

interface ApprovalRequestModalProps {
  signal: Signal
  isOpen?: boolean
  onClose: () => void
  onSuccess?: () => void
  onSubmitted?: (approval: ApprovalRequest) => void
}

export function ApprovalRequestModal({
  signal,
  isOpen = true,
  onClose,
  onSuccess,
  onSubmitted,
}: ApprovalRequestModalProps) {
  const [urgency, setUrgency] = useState<'HIGH' | 'CRITICAL'>('HIGH')
  const [requestNote, setRequestNote] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState(false)

  if (isOpen === false) return null

  const isMinCharsMet = requestNote.trim().length >= 20

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!isMinCharsMet) return

    setIsSubmitting(true)
    setError(null)

    try {
      const res = await requestSignalApproval(
        signal.signal_id || signal.id,
        requestNote.trim(),
        urgency
      )
      setSuccess(true)
      setTimeout(() => {
        onSuccess?.()
        onSubmitted?.(res)
        onClose()
      }, 1500)
    } catch (err: any) {
      setError(
        err?.message || 'Failed to submit approval request. Please try again.'
      )
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm animate-in fade-in duration-200"
      onClick={(e) => {
        if (e.target === e.currentTarget && !isSubmitting) onClose()
      }}
    >
      <div
        className="relative w-full max-w-lg rounded-2xl bg-[var(--surface)] border border-[var(--border)] shadow-2xl overflow-hidden animate-in zoom-in-95 duration-200"
        role="dialog"
        aria-modal="true"
        aria-labelledby="modal-title"
      >
        {/* Top Header Bar */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-[var(--border)] bg-[var(--surface-secondary)]">
          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded-lg bg-amber-500/10 border border-amber-500/30 text-amber-400">
              <ShieldAlert className="w-5 h-5" />
            </div>
            <div>
              <h2 id="modal-title" className="text-base font-bold text-[var(--foreground)]">
                Request Executive Leadership Approval
              </h2>
              <p className="text-xs text-[var(--muted-foreground)]">
                Escalate critical decision steer to Executive Leadership
              </p>
            </div>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="p-1.5 rounded-lg text-[var(--muted-foreground)] hover:text-[var(--foreground)] hover:bg-[var(--surface-hover)] transition-colors"
            aria-label="Close modal"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Signal Context Summary */}
        <div className="px-6 py-3.5 bg-[var(--background-secondary)] border-b border-[var(--border)]">
          <div className="flex items-center gap-2 mb-1.5">
            <span
              className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider ${
                (signal.priority || 'MEDIUM') === 'CRITICAL'
                  ? 'bg-rose-500/20 text-rose-400 border border-rose-500/30'
                  : 'bg-amber-500/20 text-amber-400 border border-amber-500/30'
              }`}
            >
              {signal.priority || 'MEDIUM'} Priority
            </span>
            <span className="text-xs text-[var(--muted-foreground)] font-mono">
              {signal.source_name || signal.source_id || 'Signal'}
            </span>
          </div>
          <p className="text-xs font-medium text-[var(--foreground)] line-clamp-2">
            {signal.title}
          </p>
        </div>

        {/* Form Body */}
        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          {error && (
            <div className="flex items-center gap-2 p-3 rounded-lg bg-rose-950/50 border border-rose-800/80 text-rose-300 text-xs">
              <AlertTriangle className="w-4 h-4 shrink-0 text-rose-400" />
              <span>{error}</span>
            </div>
          )}

          {success && (
            <div className="flex items-center gap-2 p-3 rounded-lg bg-emerald-950/50 border border-emerald-800/80 text-emerald-300 text-xs animate-in fade-in">
              <CheckCircle2 className="w-4 h-4 shrink-0 text-emerald-400" />
              <span>
                Approval request submitted successfully. Leadership has been notified.
              </span>
            </div>
          )}

          {/* Urgency Level Selector */}
          <div>
            <label className="block text-xs font-semibold text-[var(--foreground)] uppercase tracking-wider mb-1.5">
              Escalation Urgency
            </label>
            <div className="grid grid-cols-2 gap-3">
              <button
                type="button"
                onClick={() => setUrgency('HIGH')}
                className={`flex items-center justify-center gap-2 py-2 px-3 rounded-lg border text-xs font-semibold transition-all ${
                  urgency === 'HIGH'
                    ? 'bg-amber-500/20 border-amber-500/60 text-amber-300 shadow-sm'
                    : 'bg-[var(--surface-secondary)] border-[var(--border)] text-[var(--muted-foreground)] hover:text-[var(--foreground)]'
                }`}
              >
                <Clock className="w-3.5 h-3.5" />
                <span>High Priority (Next Briefing)</span>
              </button>
              <button
                type="button"
                onClick={() => setUrgency('CRITICAL')}
                className={`flex items-center justify-center gap-2 py-2 px-3 rounded-lg border text-xs font-semibold transition-all ${
                  urgency === 'CRITICAL'
                    ? 'bg-rose-500/20 border-rose-500/60 text-rose-300 shadow-sm'
                    : 'bg-[var(--surface-secondary)] border-[var(--border)] text-[var(--muted-foreground)] hover:text-[var(--foreground)]'
                }`}
              >
                <ShieldAlert className="w-3.5 h-3.5" />
                <span>Critical (Immediate Steer)</span>
              </button>
            </div>
          </div>

          {/* Strategic Rationale */}
          <div>
            <div className="flex items-center justify-between mb-1.5">
              <label
                htmlFor="request-note"
                className="block text-xs font-semibold text-[var(--foreground)] uppercase tracking-wider"
              >
                Strategic Rationale & Guidance Required
              </label>
              <span
                className={`text-[11px] font-mono ${
                  isMinCharsMet ? 'text-emerald-400' : 'text-[var(--muted-foreground)]'
                }`}
              >
                {requestNote.trim().length} / 20 min chars
              </span>
            </div>
            <textarea
              id="request-note"
              value={requestNote}
              onChange={(e) => setRequestNote(e.target.value)}
              disabled={isSubmitting || success}
              rows={4}
              placeholder="Provide context on why this signal requires executive sign-off (e.g. competitor Phase III trial hold, unexpected AE signal, regulatory submission acceleration)..."
              required
              className="w-full px-3.5 py-2.5 rounded-lg bg-[var(--surface-secondary)] border border-[var(--border)] text-[var(--foreground)] placeholder-[var(--muted-foreground)] text-xs sm:text-sm focus:outline-none focus:ring-2 focus:ring-amber-500/50 focus:border-amber-500/80 transition-all resize-none font-sans"
            />
          </div>

          {/* Action Buttons */}
          <div className="flex items-center justify-end gap-3 pt-2">
            <button
              type="button"
              onClick={onClose}
              disabled={isSubmitting}
              className="px-4 py-2 rounded-lg text-xs font-medium text-[var(--muted-foreground)] hover:text-[var(--foreground)] hover:bg-[var(--surface-hover)] transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={!isMinCharsMet || isSubmitting || success}
              className="flex items-center gap-2 px-5 py-2 rounded-lg bg-gradient-to-r from-amber-600 to-amber-500 hover:from-amber-500 hover:to-amber-400 text-white text-xs font-bold shadow-lg shadow-amber-950/40 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-150"
            >
              {isSubmitting ? (
                <>
                  <Loader2 className="w-3.5 h-3.5 animate-spin" />
                  <span>Submitting Request...</span>
                </>
              ) : success ? (
                <>
                  <CheckCircle2 className="w-3.5 h-3.5" />
                  <span>Request Sent</span>
                </>
              ) : (
                <>
                  <Send className="w-3.5 h-3.5" />
                  <span>Submit Approval Request</span>
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
