'use client'

import React, { useState, useEffect, useCallback } from 'react'
import {
  ShieldAlert,
  CheckCircle2,
  XCircle,
  Clock,
  MessageSquare,
  Loader2,
  AlertCircle,
} from 'lucide-react'
import type { ApprovalRequest } from '@/types/api'
import { getPendingApprovals, resolveSignalApproval } from '@/lib/api'
import { useAuth } from '@/context/AuthContext'

const ROLE_COLOR_MAP: Record<
  string,
  { bg: string; text: string; border: string }
> = {
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

function formatTimeAgo(isoString: string): string {
  const date = new Date(isoString)
  const now = new Date()
  const diffMinutes = Math.floor((now.getTime() - date.getTime()) / (1000 * 60))

  if (diffMinutes < 1) return 'Just now'
  if (diffMinutes < 60) return `${diffMinutes}m ago`
  const diffHours = Math.floor(diffMinutes / 60)
  if (diffHours < 24) return `${diffHours}h ago`
  return `${Math.floor(diffHours / 24)}d ago`
}

export function PendingApprovalsPanel() {
  const { role } = useAuth()
  const [requests, setRequests] = useState<ApprovalRequest[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [resolvingId, setResolvingId] = useState<string | null>(null)
  const [decisionNotes, setDecisionNotes] = useState<Record<string, string>>({})
  const [actionSuccessMessage, setActionSuccessMessage] = useState<string | null>(
    null
  )

  const isExecutive = role === 'LEADERSHIP'

  const fetchRequests = useCallback(async () => {
    try {
      setError(null)
      const data = await getPendingApprovals()
      setRequests(data)
    } catch (err: any) {
      setError(err?.message || 'Failed to load approval requests')
    } finally {
      setIsLoading(false)
    }
  }, [])

  useEffect(() => {
    if (isExecutive) {
      fetchRequests()
      const interval = setInterval(fetchRequests, 15000)
      return () => clearInterval(interval)
    } else {
      setIsLoading(false)
    }
  }, [isExecutive, fetchRequests])

  if (!isExecutive) return null

  const handleResolve = async (
    req: ApprovalRequest,
    status: 'APPROVED' | 'REJECTED'
  ) => {
    setResolvingId(req.request_id)
    try {
      const note = decisionNotes[req.request_id]
      await resolveSignalApproval(
        req.signal_id,
        status,
        note?.trim() || undefined
      )

      setActionSuccessMessage(
        `Request for "${req.signal_title || 'Signal'}" marked as ${status}.`
      )
      setTimeout(() => setActionSuccessMessage(null), 4000)

      setRequests((prev) => prev.filter((r) => r.request_id !== req.request_id))
    } catch (err: any) {
      setError(err?.message || `Failed to ${status.toLowerCase()} request`)
    } finally {
      setResolvingId(null)
    }
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center p-8 bg-[var(--surface-secondary)] border border-[var(--border)] rounded-2xl mb-6">
        <Loader2 className="w-5 h-5 text-cyan-400 animate-spin mr-2" />
        <span className="text-xs font-medium text-[var(--muted-foreground)]">
          Loading Executive Approval Queue...
        </span>
      </div>
    )
  }

  if (requests.length === 0) {
    return (
      <div className="p-5 bg-[var(--surface-secondary)] border border-[var(--border)] rounded-2xl mb-6 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-400">
            <CheckCircle2 className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-xs sm:text-sm font-bold text-[var(--foreground)]">
              Executive Approval Queue Clear
            </h3>
            <p className="text-[11px] text-[var(--muted-foreground)]">
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
    <div className="bg-[var(--surface)] border border-amber-500/30 rounded-2xl p-5 mb-8 shadow-xl backdrop-blur-md">
      {/* Header */}
      <div className="flex items-center justify-between mb-4 pb-3 border-b border-[var(--border)]">
        <div className="flex items-center gap-2.5">
          <div className="p-2 rounded-xl bg-amber-500/15 border border-amber-500/30 text-amber-400">
            <ShieldAlert className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-sm sm:text-base font-bold text-[var(--foreground)]">
                Executive Leadership Approval Queue
              </h2>
              <span className="px-2 py-0.5 rounded-full bg-amber-500/20 text-amber-300 border border-amber-500/40 text-xs font-bold font-mono">
                {requests.length} Pending
              </span>
            </div>
            <p className="text-xs text-[var(--muted-foreground)]">
              Decisions escalated from Medical Affairs, Regulatory, Safety & Access
            </p>
          </div>
        </div>

        <button
          type="button"
          onClick={fetchRequests}
          className="text-xs text-[var(--muted-foreground)] hover:text-[var(--foreground)] transition-colors font-mono"
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
            bg: 'bg-[var(--surface-secondary)]',
            text: 'text-[var(--foreground)]',
            border: 'border-[var(--border)]',
          }
          const isResolving = resolvingId === req.request_id

          return (
            <div
              key={req.request_id}
              className="p-4 rounded-xl bg-[var(--surface-secondary)] border border-[var(--border)] hover:border-[var(--signal)] transition-all space-y-3"
            >
              {/* Top Meta */}
              <div className="flex flex-wrap items-center justify-between gap-2">
                <div className="flex items-center gap-2">
                  <span
                    className={`px-2.5 py-0.5 rounded-full text-xs font-semibold border ${roleColor.bg} ${roleColor.text} ${roleColor.border}`}
                  >
                    {req.requested_by_display_name || req.requested_by_role}
                  </span>
                  <span className="text-[11px] text-[var(--muted-foreground)] flex items-center gap-1 font-mono">
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
                    <span className="text-[11px] text-[var(--muted-foreground)] font-mono">
                      {req.signal_source}
                    </span>
                  )}
                </div>
              </div>

              {/* Signal Title */}
              <h4 className="text-sm font-semibold text-[var(--foreground)]">
                {req.signal_title || 'Signal Escalation'}
              </h4>

              {/* Request Note Box */}
              {req.request_note && (
                <div className="p-3 rounded-lg bg-[var(--surface)] border border-[var(--border)] text-xs text-[var(--foreground)] flex items-start gap-2">
                  <MessageSquare className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
                  <div>
                    <span className="font-semibold text-[var(--foreground)]">
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
                  className="flex-1 px-3 py-2 rounded-lg bg-[var(--surface)] border border-[var(--border)] text-xs text-[var(--foreground)] placeholder-[var(--muted-foreground)] focus:outline-none focus:ring-1 focus:ring-cyan-500/50"
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
