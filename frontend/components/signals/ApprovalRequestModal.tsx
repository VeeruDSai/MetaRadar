'use client'

import React, { useState } from 'react'
import type { Signal, ApprovalRequest } from '@/types/api'
import { requestSignalApproval } from '@/lib/api'
import {
  X,
  Send,
  AlertTriangle,
  Loader2,
  CheckCircle2,
  ShieldAlert,
  Clock,
} from 'lucide-react'

interface ApprovalRequestModalProps {
  signal: Signal
  onClose: () => void
  onSubmitted?: (approval: ApprovalRequest) => void
}

export function ApprovalRequestModal({
  signal,
  onClose,
  onSubmitted,
}: ApprovalRequestModalProps) {
  const [requestNote, setRequestNote] = useState<string>('')
  const [urgency, setUrgency] = useState<'CRITICAL' | 'HIGH'>('HIGH')
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<boolean>(false)

  const isMinCharsMet = requestNote.trim().length >= 20

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!isMinCharsMet || isSubmitting) return

    setIsSubmitting(true)
    setError(null)

    const signalId = signal.signal_id || signal.id
    if (!signalId) {
      setError('Invalid signal reference identifier.')
      setIsSubmitting(false)
      return
    }

    try {
      const res = await requestSignalApproval(signalId, requestNote.trim(), urgency)
      setSuccess(true)
      if (onSubmitted) {
        onSubmitted(res)
      }
      setTimeout(() => {
        onClose()
      }, 1400)
    } catch (err: any) {
      setError(
        err?.message || 'Failed to submit approval request. Please try again.'
      )
      setIsSubmitting(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-md animate-in fade-in duration-150">
      <div
        className="relative w-full max-w-xl bg-slate-900 border border-slate-700/80 rounded-2xl shadow-2xl overflow-hidden animate-in zoom-in-95 duration-150"
        role="dialog"
        aria-modal="true"
        aria-labelledby="modal-title"
      >
        {/* Top Header Bar */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-800 bg-slate-950/60">
          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded-lg bg-amber-500/10 border border-amber-500/30 text-amber-400">
              <ShieldAlert className="w-5 h-5" />
            </div>
            <div>
              <h2 id="modal-title" className="text-base font-bold text-slate-100">
                Request Executive Leadership Approval
              </h2>
              <p className="text-xs text-slate-400">
                Escalate critical decision steer to Executive Leadership
              </p>
            </div>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-slate-200 hover:bg-slate-800 transition-colors"
            aria-label="Close modal"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Signal Context Summary */}
        <div className="px-6 py-3.5 bg-slate-950/30 border-b border-slate-800/60">
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
            <span className="text-xs text-slate-400 font-mono">
              {signal.source_name || signal.source_id || 'Signal'}
            </span>
          </div>
          <p className="text-xs font-medium text-slate-200 line-clamp-2">
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
            <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1.5">
              Escalation Urgency
            </label>
            <div className="grid grid-cols-2 gap-3">
              <button
                type="button"
                onClick={() => setUrgency('HIGH')}
                className={`flex items-center justify-center gap-2 py-2 px-3 rounded-lg border text-xs font-semibold transition-all ${
                  urgency === 'HIGH'
                    ? 'bg-amber-500/20 border-amber-500/60 text-amber-300 shadow-sm'
                    : 'bg-slate-950/40 border-slate-800 text-slate-400 hover:text-slate-200'
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
                    : 'bg-slate-950/40 border-slate-800 text-slate-400 hover:text-slate-200'
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
                className="block text-xs font-semibold text-slate-300 uppercase tracking-wider"
              >
                Strategic Rationale & Guidance Required
              </label>
              <span
                className={`text-[11px] font-mono ${
                  isMinCharsMet ? 'text-emerald-400' : 'text-slate-400'
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
              className="w-full px-3.5 py-2.5 rounded-lg bg-slate-950/70 border border-slate-800 text-slate-100 placeholder-slate-600 text-xs sm:text-sm focus:outline-none focus:ring-2 focus:ring-amber-500/50 focus:border-amber-500/80 transition-all resize-none font-sans"
            />
          </div>

          {/* Action Buttons */}
          <div className="flex items-center justify-end gap-3 pt-2">
            <button
              type="button"
              onClick={onClose}
              disabled={isSubmitting}
              className="px-4 py-2 rounded-lg text-xs font-medium text-slate-400 hover:text-slate-200 hover:bg-slate-800 transition-colors"
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
