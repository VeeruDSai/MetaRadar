'use client'

import React, { useState, useEffect, useCallback } from 'react'
import type { ApprovalRequest } from '@/types/api'
import { getPendingApprovals, resolveSignalApproval } from '@/lib/api'
import { formatTimeAgo } from '@/lib/mappers'
import {
  ShieldAlert,
  CheckCircle2,
  XCircle,
  Clock,
  Loader2,
  Sparkles,
  MessageSquare,
  AlertCircle,
} from 'lucide-react'

const ROLE_COLOR_MAP: Record<string, { bg: string; text: string; border: string }> = {
  MEDICAL_AFFAIRS: {
    bg: 'bg-emerald-500/10',
    text: 'text-emerald-400',
    border: 'border-emerald-500/30',
  },
  REGULATORY: {
    bg: 'bg-blue-500/10',
    text: 'text-blue-400',
    border: 'border-blue-500/30',
  },
  SAFETY: {
    bg: 'bg-rose-500/10',
    text: 'text-rose-400',
    border: 'border-rose-500/30',
  },
  MARKET_ACCESS: {
    bg: 'bg-amber-500/10',
    text: 'text-amber-400',
    border: 'border-amber-500/30',
  },
  COMMUNICATIONS: {
    bg: 'bg-purple-500/10',
    text: 'text-purple-400',
    border: 'border-purple-500/30',
  },
}

export function PendingApprovalsPanel() {
  const [requests, setRequests] = useState<ApprovalRequest[]>([])
  const [isLoading, setIsLoading] = useState<boolean>(true)
  const [error, setError] = useState<string | null>(null)
  const [decisionNotes, setDecisionNotes] = useState<Record<string, string>>({})
  const [resolvingId, setResolvingId] = useState<string | null>(null)
  const [actionSuccessMessage, setActionSuccessMessage] = useState<string | null>(null)

  const fetchRequests = useCallback(async () => {
    setIsLoading(true)
    setError(null)
    try {
      const data = await getPendingApprovals()
      setRequests(data)
    } catch (err: any) {
      setError(err?.message || 'Failed to load pending approval requests.')
    } finally {
      setIsLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchRequests()
  }, [fetchRequests])

  const handleResolve = async (
    request: ApprovalRequest,
    status: 'APPROVED' | 'REJECTED'
  ) => {
    setResolvingId(request.request_id)
    setError(null)
    const note = decisionNotes[request.request_id] || ''

    try {
      await resolveSignalApproval(request.signal_id, status, note.trim())
      setRequests((prev) => prev.filter((r) => r.request_id !== request.request_id))
      setActionSuccessMessage(
        status === 'APPROVED'
          ? `Signal "${request.signal_title || 'Signal'}" approved successfully.`
          : `Signal "${request.signal_title || 'Signal'}" returned with decision note.`
      )
      setTimeout(() => setActionSuccessMessage(null), 3500)
    } catch (err: any) {
      setError(err?.message || `Failed to ${status.toLowerCase()} request.`)
    } finally {
      setResolvingId(null)
    }
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center p-8 bg-slate-900/60 border border-slate-800 rounded-2xl mb-6">
        <Loader2 className="w-5 h-5 text-cyan-400 animate-spin mr-2" />
        <span className="text-xs font-medium text-slate-400">
          Loading Executive Approval Queue...
        </span>
      </div>
    )
  }

  if (requests.length === 0) {
    return (
      <div className="p-5 bg-slate-900/40 border border-slate-800/80 rounded-2xl mb-6 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-400">
            <CheckCircle2 className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-xs sm:text-sm font-bold text-slate-200">
              Executive Approval Queue Clear
            </h3>
            <p className="text-[11px] text-slate-400">
              All cross-functional escalation requests have been reviewed and resolved.
            </p>
          </div>
        </div>
        <span className="text-[10px] font-mono font-semibold px-2.5 py-1 rounded-full bg-emerald-500/15 text-emerald-300 border border-emerald-500/30">
          0 Pending
        </span>
      </div>
    )
  }

  return (
    <div className="bg-slate-900/80 border border-amber-500/30 rounded-2xl p-5 mb-8 shadow-xl backdrop-blur-md">
      {/* Header */}
      <div className="flex items-center justify-between mb-4 pb-3 border-b border-slate-800">
        <div className="flex items-center gap-2.5">
          <div className="p-2 rounded-xl bg-amber-500/15 border border-amber-500/30 text-amber-400">
            <ShieldAlert className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-sm sm:text-base font-bold text-slate-100">
                Executive Leadership Approval Queue
              </h2>
              <span className="px-2 py-0.5 rounded-full bg-amber-500/20 text-amber-300 border border-amber-500/40 text-xs font-bold font-mono">
                {requests.length} Pending
              </span>
            </div>
            <p className="text-xs text-slate-400">
              Decisions escalated from Medical Affairs, Regulatory, Safety & Access
            </p>
          </div>
        </div>

        <button
          type="button"
          onClick={fetchRequests}
          className="text-xs text-slate-400 hover:text-slate-200 transition-colors font-mono"
        >
          Refresh Queue
        </button>
      </div>

      {actionSuccessMessage && (
        <div className="flex items-center gap-2 p-3 mb-4 rounded-lg bg-emerald-950/60 border border-emerald-800/80 text-emerald-300 text-xs animate-in fade-in">
          <CheckCircle2 className="w-4 h-4 shrink-0 text-emerald-400" />
          <span>{actionSuccessMessage}</span>
        </div>
      )}

      {error && (
        <div className="flex items-center gap-2 p-3 mb-4 rounded-lg bg-rose-950/60 border border-rose-800/80 text-rose-300 text-xs">
          <AlertCircle className="w-4 h-4 shrink-0 text-rose-400" />
          <span>{error}</span>
        </div>
      )}

      {/* Cards List */}
      <div className="space-y-4">
        {requests.map((req) => {
          const roleColor = ROLE_COLOR_MAP[req.requested_by_role] || {
            bg: 'bg-slate-800',
            text: 'text-slate-300',
            border: 'border-slate-700',
          }
          const isResolving = resolvingId === req.request_id

          return (
            <div
              key={req.request_id}
              className="p-4 rounded-xl bg-slate-950/70 border border-slate-800 hover:border-slate-700 transition-all space-y-3"
            >
              {/* Top Meta */}
              <div className="flex flex-wrap items-center justify-between gap-2">
                <div className="flex items-center gap-2">
                  <span
                    className={`px-2.5 py-0.5 rounded-full text-xs font-semibold border ${roleColor.bg} ${roleColor.text} ${roleColor.border}`}
                  >
                    {req.requested_by_display_name || req.requested_by_role}
                  </span>
                  <span className="text-[11px] text-slate-400 flex items-center gap-1 font-mono">
                    <Clock className="w-3 h-3" />
                    {formatTimeAgo(req.requested_at)}
                  </span>
                </div>

                <div className="flex items-center gap-2">
                  <span
                    className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase ${
                      req.signal_priority === 'CRITICAL'
                        ? 'bg-rose-500/20 text-rose-400 border border-rose-500/30'
                        : 'bg-amber-500/20 text-amber-400 border border-amber-500/30'
                    }`}
                  >
                    {req.signal_priority || 'HIGH'}
                  </span>
                  {req.signal_source && (
                    <span className="text-[11px] text-slate-400 font-mono">
                      {req.signal_source}
                    </span>
                  )}
                </div>
              </div>

              {/* Signal Title */}
              <h4 className="text-sm font-semibold text-slate-100">
                {req.signal_title || 'Signal Escalation'}
              </h4>

              {/* Request Note Box */}
              {req.request_note && (
                <div className="p-3 rounded-lg bg-slate-900/90 border border-slate-800 text-xs text-slate-300 flex items-start gap-2">
                  <MessageSquare className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
                  <div>
                    <span className="font-semibold text-slate-200">
                      Rationale from {req.requested_by_role}:{' '}
                    </span>
                    <span>&ldquo;{req.request_note}&rdquo;</span>
                  </div>
                </div>
              )}

              {/* Decision Note & Actions */}
              <div className="pt-2 flex flex-col sm:flex-row items-stretch sm:items-center gap-3">
                <input
                  type="text"
                  placeholder="Directive or strategic guidance note (e.g. Authorized to proceed with DSMB)..."
                  value={decisionNotes[req.request_id] || ''}
                  onChange={(e) =>
                    setDecisionNotes((prev) => ({
                      ...prev,
                      [req.request_id]: e.target.value,
                    }))
                  }
                  disabled={isResolving}
                  className="flex-1 px-3 py-2 rounded-lg bg-slate-900 border border-slate-800 text-xs text-slate-100 placeholder-slate-600 focus:outline-none focus:ring-1 focus:ring-cyan-500/50"
                />

                <div className="flex items-center gap-2 shrink-0">
                  <button
                    type="button"
                    onClick={() => handleResolve(req, 'REJECTED')}
                    disabled={isResolving}
                    className="flex items-center gap-1.5 px-3.5 py-2 rounded-lg bg-rose-500/15 hover:bg-rose-500/25 border border-rose-500/30 text-rose-300 text-xs font-semibold transition-colors disabled:opacity-50"
                  >
                    <XCircle className="w-3.5 h-3.5" />
                    <span>Return</span>
                  </button>

                  <button
                    type="button"
                    onClick={() => handleResolve(req, 'APPROVED')}
                    disabled={isResolving}
                    className="flex items-center gap-1.5 px-4 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-bold shadow-lg shadow-emerald-950/40 transition-colors disabled:opacity-50"
                  >
                    {isResolving ? (
                      <Loader2 className="w-3.5 h-3.5 animate-spin" />
                    ) : (
                      <CheckCircle2 className="w-3.5 h-3.5" />
                    )}
                    <span>Approve Decision</span>
                  </button>
                </div>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
