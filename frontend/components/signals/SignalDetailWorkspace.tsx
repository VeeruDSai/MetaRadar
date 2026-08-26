'use client'

import React, { useState, useEffect, useCallback } from 'react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import type { Signal, ConfluenceAlertItem, ContradictionItem, AuditLogItem, SignalReviewPayload } from '@/types/api'
import { Badge, Card, SectionTitle } from '@/components/metaradar'
import { DataModeBadge } from '@/components/common/DataModeBadge'
import { useDemoOperator } from '@/components/common/DemoOperatorSelector'
import Counter from '@/components/ui/Counter'
import Stepper, { Step } from '@/components/ui/Stepper'
import { GlowingThinkingButton } from '@/components/ui/GlowingThinkingButton'
import { useTheme } from '@/components/theme/ThemeProvider'
import { getSourceAuthority, getSignalFunction, getSuggestedAction } from './SignalCard'
import { EvidenceConvergenceWidget } from './EvidenceConvergenceWidget'
import { PriorityScoreExplainer } from './PriorityScoreExplainer'
import { RedTeamCounterFactuals } from './RedTeamCounterFactuals'
import { askAthena, submitSignalReview, fetchSignalAuditHistory } from '@/lib/api'
import {
  Activity,
  AlertTriangle,
  ArrowLeft,
  ArrowRight,
  BookOpen,
  Bot,
  BrainCircuit,
  Building2,
  Check,
  CheckCircle2,
  Clock,
  ExternalLink,
  Eye,
  FileCheck,
  FileText,
  Filter,
  FlaskConical,
  Globe,
  History,
  Inbox,
  Layers,
  Network,
  RefreshCw,
  Send,
  Shield,
  ShieldAlert,
  ShieldCheck,
  Sparkles,
  Tag,
  ThumbsDown,
  ThumbsUp,
  User,
  UserCheck,
  Users,
  XCircle,
  Zap,
} from 'lucide-react'

export interface SignalDetailWorkspaceProps {
  signal: Signal
  confluences?: ConfluenceAlertItem[]
  contradictions?: ContradictionItem[]
}

export function SignalDetailWorkspace({
  signal: initialSignal,
  confluences = [],
  contradictions = [],
}: SignalDetailWorkspaceProps) {
  const router = useRouter()
  const { isDark } = useTheme()
  const { operator: demoOperator } = useDemoOperator()

  // State-persisted signal model
  const [signal, setSignal] = useState<Signal>(initialSignal)
  const targetId = signal.signal_id || signal.id || initialSignal.signal_id || initialSignal.id

  // Audit history state
  const [auditHistory, setAuditHistory] = useState<AuditLogItem[]>([])
  const [auditLoading, setAuditLoading] = useState(false)
  const [auditError, setAuditError] = useState<string | null>(null)

  // Review interaction state
  const [reviewLoading, setReviewLoading] = useState(false)
  const [reviewNotice, setReviewNotice] = useState<string | null>(null)
  const [reviewError, setReviewError] = useState<string | null>(null)
  const [inlineActionType, setInlineActionType] = useState<'REJECT' | 'EVIDENCE' | 'ACTION' | null>(null)
  const [inlineNotes, setInlineNotes] = useState('')

  const loadAuditHistory = useCallback(async () => {
    if (!targetId) return
    setAuditLoading(true)
    setAuditError(null)
    try {
      const history = await fetchSignalAuditHistory(targetId)
      setAuditHistory(history)
    } catch (err: any) {
      setAuditError(err?.message || 'Failed to load audit trail')
    } finally {
      setAuditLoading(false)
    }
  }, [targetId])

  useEffect(() => {
    loadAuditHistory()
  }, [loadAuditHistory])

  // Athena contextual reasoning state
  const [athenaQuery, setAthenaQuery] = useState('')
  const [athenaLoading, setAthenaLoading] = useState(false)
  const [athenaAnswer, setAthenaAnswer] = useState<string | null>(null)
  const [athenaError, setAthenaError] = useState<string | null>(null)

  const priorityStr = (signal.priority || signal.severity || 'MEDIUM').toUpperCase()
  const priorityKey = (priorityStr.toLowerCase() || 'medium') as
    | 'critical'
    | 'high'
    | 'medium'
    | 'low'
    | 'neutral'

  const scoreValue =
    signal.score_breakdown?.total !== undefined && signal.score_breakdown.total > 0
      ? Math.round(signal.score_breakdown.total)
      : signal.score !== undefined && signal.score > 0
      ? Math.round(signal.score)
      : 50

  const sourceName =
    signal.source_name ||
    (signal.sources && signal.sources.length > 0 ? signal.sources[0].name : null) ||
    (signal.source_id ? signal.source_id.toUpperCase().replace(/_/g, ' ') : 'Primary Source')

  const authority = getSourceAuthority(signal.source_id, sourceName)
  const { functionName, escalateToLeadership } = getSignalFunction(signal)
  const suggestedAction = getSuggestedAction(signal)

  const whatChanged =
    signal.what_changed ||
    (signal.facts && signal.facts.length > 0
      ? signal.facts.join(' ')
      : signal.evidence_text || signal.summary || signal.content || signal.title)

  const whyItMatters =
    signal.why_it_matters ||
    signal.interpretation ||
    (signal.speculation ? `Strategic perspective: ${signal.speculation}` : null) ||
    'Decision significance pending live clinical reasoning synthesis.'

  const rawPayload = (signal as any).raw_payload || {}

  // Canonical Evidence URL resolution: honest fallback chain, NO hardcoded newsapi.org
  const evidenceUrl =
    signal.canonical_url ||
    (signal as any).url ||
    (signal.sources && signal.sources.length > 0 ? signal.sources[0].url : null) ||
    (signal.external_id && signal.external_id.startsWith('http') ? signal.external_id : null) ||
    rawPayload.url ||
    rawPayload.article?.url ||
    rawPayload.link ||
    null

  const reviewStatus = (signal.review_status || signal.status || 'UNREVIEWED').toUpperCase()

  const handleReviewAction = async (
    newStatus: string,
    decision?: string,
    notes?: string,
    resultingAction?: string
  ) => {
    if (!targetId) return
    setReviewLoading(true)
    setReviewError(null)
    try {
      const payload: SignalReviewPayload = {
        status: newStatus as any,
        reviewer: demoOperator,
        decision,
        notes: notes || undefined,
        resulting_action: resultingAction || undefined,
      }
      const updated = await submitSignalReview(targetId, payload)
      setSignal(updated)
      setInlineActionType(null)
      setInlineNotes('')
      setReviewNotice(`Signal status updated to ${newStatus} by ${demoOperator}`)
      await loadAuditHistory()
      setTimeout(() => setReviewNotice(null), 5000)
    } catch (err: any) {
      setReviewError(err?.message || 'Review status update failed. Please retry.')
    } finally {
      setReviewLoading(false)
    }
  }

  const handleAskAthena = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!athenaQuery.trim()) return
    setAthenaLoading(true)
    setAthenaError(null)
    try {
      const contextualPrompt = `Regarding signal "${signal.title}": ${athenaQuery}`
      const res = await askAthena(contextualPrompt)
      setAthenaAnswer(res.answer)
    } catch (err: any) {
      setAthenaError(err?.message || 'Failed to retrieve Athena synthesis. Please retry.')
    } finally {
      setAthenaLoading(false)
    }
  }

  // Calculate actual lifecycle step from backend state
  let currentLifecycleStep = 3 // default: detected, classified, prioritized
  if (reviewStatus === 'ACTIONED') {
    currentLifecycleStep = 6
  } else if (reviewStatus === 'REVIEWED') {
    currentLifecycleStep = 5
  } else if (reviewStatus === 'IN_REVIEW' || reviewStatus === 'ACTION_REQUIRED') {
    currentLifecycleStep = 4
  }

  const publishedDate = signal.published_at
    ? new Date(signal.published_at).toLocaleDateString('en-US', {
        day: 'numeric',
        month: 'short',
        year: 'numeric',
      })
    : signal.detectedAt || 'Recent'

  const externalId = signal.external_id || signal.pmid || signal.nct_id || signal.regulatory_id

  // Related confluences matching this signal or development
  const relatedConfluences = confluences.filter(
    (c) =>
      c.development_id === signal.development_id ||
      c.development_title?.toLowerCase().includes(signal.disease?.toLowerCase() || '')
  )

  // Related contradictions
  const relatedContradictions = contradictions.filter(
    (c) =>
      c.claim_a_id === signal.id ||
      c.claim_b_id === signal.id ||
      c.claim_a_id === signal.signal_id ||
      c.claim_b_id === signal.signal_id
  )

  return (
    <div className="flex flex-col gap-6 max-w-6xl mx-auto py-2">
      {/* Top Breadcrumbs & Back Navigation */}
      <div className="flex items-center justify-between gap-4">
        <Link
          href="/signals"
          className="inline-flex items-center gap-1.5 text-xs font-semibold text-[var(--muted-foreground)] hover:text-[var(--foreground)] transition-colors"
        >
          <ArrowLeft size={14} />
          <span>Back to Signals</span>
        </Link>

        <div className="flex items-center gap-2">
          <DataModeBadge mode={signal.data_mode} isSynthetic={signal.is_synthetic} />
          <span className="text-xs text-[var(--muted-foreground)] font-mono">
            ID: {targetId}
          </span>
        </div>
      </div>

      {reviewNotice && (
        <div className="p-3 rounded-md bg-[var(--success)]/10 border border-[var(--success)]/30 text-xs font-medium text-[var(--success)] flex items-center justify-between gap-2 animate-in fade-in">
          <div className="flex items-center gap-2">
            <CheckCircle2 size={16} className="shrink-0" />
            <span>{reviewNotice}</span>
          </div>
          <button
            type="button"
            onClick={() => setReviewNotice(null)}
            className="text-[var(--success)] hover:opacity-80 text-xs font-bold"
          >
            Dismiss
          </button>
        </div>
      )}

      {reviewError && (
        <div className="p-3 rounded-md bg-[var(--danger)]/10 border border-[var(--danger)]/30 text-xs font-medium text-[var(--danger)] flex items-center justify-between gap-2 animate-in fade-in">
          <div className="flex items-center gap-2">
            <AlertTriangle size={16} className="shrink-0" />
            <span>{reviewError}</span>
          </div>
          <button
            type="button"
            onClick={() => setReviewError(null)}
            className="text-[var(--danger)] hover:opacity-80 text-xs font-bold"
          >
            Dismiss
          </button>
        </div>
      )}

      {/* Main Signal Header Card */}
      <div className="p-6 rounded-[var(--radius-lg,12px)] bg-[var(--surface)] border border-[var(--border)] shadow-sm">
        <div className="flex flex-col md:flex-row md:items-start justify-between gap-4 mb-4">
          <div className="flex-1">
            <div className="flex items-center gap-2.5 flex-wrap mb-2.5">
              <Badge tone={priorityKey}>{priorityStr}</Badge>
              {escalateToLeadership && (
                <span className="inline-flex items-center gap-1 text-xs font-bold px-2.5 py-0.5 rounded-full bg-[var(--priority-critical)]/10 text-[var(--priority-critical)] border border-[var(--priority-critical)]/20">
                  <ShieldAlert size={13} />
                  <span>Escalation: Executive Leadership</span>
                </span>
              )}
              <span className="inline-flex items-center gap-1 text-xs font-medium px-2.5 py-0.5 rounded-full bg-[var(--surface-secondary)] text-[var(--foreground)] border border-[var(--border)]">
                <Network size={13} className="text-[var(--primary)]" />
                <span>Destination: {functionName}</span>
              </span>
              <span className="text-xs text-[var(--muted-foreground)]">
                Published: {publishedDate}
              </span>
            </div>

            <h1 className="text-xl md:text-2xl font-bold text-[var(--foreground)] leading-tight m-0">
              {signal.title}
            </h1>
          </div>

          {/* Priority Score Hero Counter */}
          <div className="flex flex-col items-end shrink-0 p-3.5 rounded-xl bg-[var(--surface-secondary)] border border-[var(--border)]">
            <div className="flex items-baseline gap-1">
              <Counter
                value={scoreValue}
                places={[100, 10, 1]}
                fontSize={36}
                fontWeight={800}
                textColor="var(--foreground)"
                digitPlaceHolders
                accessibleLabel={`Priority score ${scoreValue} out of 100`}
              />
              <span className="text-xs text-[var(--muted-foreground)] font-mono">/100</span>
            </div>
            <span className="text-[10px] uppercase font-bold tracking-wider text-[var(--muted-foreground)] mt-0.5">
              Decision Priority
            </span>
          </div>
        </div>

        {/* Workflow & Review Queue Action Bar */}
        <div className="pt-4 border-t border-[var(--border)] flex flex-col gap-3">
          <div className="flex flex-wrap items-center justify-between gap-3 text-xs">
            <div className="flex items-center gap-2">
              <Inbox size={15} className="text-[var(--primary)]" />
              <span className="font-bold text-[var(--foreground)] uppercase text-[11px] tracking-wider">
                Review Workflow State:
              </span>
              <span
                className={`font-bold px-2 py-0.5 rounded text-[11px] uppercase ${
                  reviewStatus === 'UNREVIEWED'
                    ? 'bg-[var(--warning)]/15 text-[var(--warning)] border border-[var(--warning)]/30'
                    : reviewStatus === 'IN_REVIEW'
                    ? 'bg-[var(--primary)]/15 text-[var(--primary)] border border-[var(--primary)]/30'
                    : reviewStatus === 'REVIEWED'
                    ? 'bg-[var(--success)]/15 text-[var(--success)] border border-[var(--success)]/30'
                    : reviewStatus === 'ACTIONED'
                    ? 'bg-[var(--accent)]/15 text-[var(--accent)] border border-[var(--accent)]/30'
                    : 'bg-[var(--surface-secondary)] text-[var(--muted-foreground)] border border-[var(--border)]'
                }`}
              >
                {reviewStatus.replace(/_/g, ' ')}
              </span>
              {signal.reviewed_by && (
                <span className="text-[var(--muted-foreground)] text-[11px] ml-1">
                  by <strong>{signal.reviewed_by}</strong>
                </span>
              )}
            </div>

            <div className="flex items-center gap-2 text-[var(--muted-foreground)]">
              <UserCheck size={13} className="text-[var(--warning)]" />
              <span>Acting as: <strong>{demoOperator}</strong></span>
            </div>
          </div>

          {/* Interactive Workflow Buttons */}
          <div className="flex flex-wrap items-center gap-2 pt-1">
            {reviewStatus === 'UNREVIEWED' && (
              <button
                type="button"
                disabled={reviewLoading}
                onClick={() => handleReviewAction('IN_REVIEW', undefined, 'Acknowledged by destination reviewer')}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-semibold bg-[var(--primary)] text-[var(--primary-foreground)] hover:opacity-90 transition-opacity disabled:opacity-50 shadow-xs"
              >
                {reviewLoading ? <RefreshCw size={13} className="animate-spin" /> : <Eye size={13} />}
                <span>Acknowledge & Start Review</span>
              </button>
            )}

            {(reviewStatus === 'UNREVIEWED' || reviewStatus === 'IN_REVIEW') && (
              <>
                <button
                  type="button"
                  disabled={reviewLoading}
                  onClick={() => handleReviewAction('REVIEWED', 'APPROVED', 'Validated against clinical and regulatory baseline')}
                  className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-semibold bg-[var(--success)] text-white hover:opacity-90 transition-opacity disabled:opacity-50 shadow-xs"
                >
                  {reviewLoading ? <RefreshCw size={13} className="animate-spin" /> : <ThumbsUp size={13} />}
                  <span>Approve Signal</span>
                </button>

                <button
                  type="button"
                  disabled={reviewLoading}
                  onClick={() => setInlineActionType(inlineActionType === 'REJECT' ? null : 'REJECT')}
                  className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-semibold bg-[var(--surface-secondary)] text-[var(--danger)] border border-[var(--danger)]/30 hover:bg-[var(--danger)]/10 transition-colors disabled:opacity-50"
                >
                  <ThumbsDown size={13} />
                  <span>Reject / Contest</span>
                </button>

                <button
                  type="button"
                  disabled={reviewLoading}
                  onClick={() => setInlineActionType(inlineActionType === 'EVIDENCE' ? null : 'EVIDENCE')}
                  className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-semibold bg-[var(--surface-secondary)] text-[var(--foreground)] border border-[var(--border)] hover:bg-[var(--surface-secondary)]/80 transition-colors disabled:opacity-50"
                >
                  <FileCheck size={13} />
                  <span>Request Additional Evidence</span>
                </button>
              </>
            )}

            {reviewStatus === 'REVIEWED' && (
              <button
                type="button"
                disabled={reviewLoading}
                onClick={() => setInlineActionType(inlineActionType === 'ACTION' ? null : 'ACTION')}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-semibold bg-[var(--primary)] text-[var(--primary-foreground)] hover:opacity-90 transition-opacity disabled:opacity-50 shadow-xs"
              >
                <Zap size={13} />
                <span>Execute & Record Action</span>
              </button>
            )}

            {reviewStatus !== 'DISMISSED' && (
              <button
                type="button"
                disabled={reviewLoading}
                onClick={() => handleReviewAction('DISMISSED', 'DISMISSED', 'Dismissed by stakeholder')}
                className="inline-flex items-center gap-1 px-2.5 py-1.5 rounded-md text-xs font-medium text-[var(--muted-foreground)] hover:text-[var(--foreground)] hover:bg-[var(--surface-secondary)] transition-colors ml-auto"
              >
                <XCircle size={13} />
                <span>Dismiss</span>
              </button>
            )}
          </div>

          {/* Inline Action Note Inputs */}
          {inlineActionType && (
            <div className="p-3 rounded-md bg-[var(--surface-secondary)] border border-[var(--border)] flex flex-col gap-2 mt-1 animate-in fade-in">
              <span className="text-[11px] font-bold text-[var(--foreground)]">
                {inlineActionType === 'REJECT'
                  ? 'Rejection Rationale & Notes'
                  : inlineActionType === 'EVIDENCE'
                  ? 'Evidence Clarification Request'
                  : 'Action Taken / Operational Directive'}
              </span>
              <textarea
                value={inlineNotes}
                onChange={(e) => setInlineNotes(e.target.value)}
                placeholder={
                  inlineActionType === 'REJECT'
                    ? 'State reasons for contesting this signal (e.g. flawed study methodology, out of date cohort)...'
                    : inlineActionType === 'EVIDENCE'
                    ? 'Specify missing endpoints or data required before approval...'
                    : 'Describe operational follow-up (e.g. updated ICER dossier, briefed commercial lead)...'
                }
                rows={2}
                className="w-full px-3 py-2 text-xs rounded-md bg-[var(--surface)] border border-[var(--border)] text-[var(--foreground)] placeholder:text-[var(--muted-foreground)] focus:outline-none focus:border-[var(--primary)] resize-none"
              />
              <div className="flex items-center justify-end gap-2">
                <button
                  type="button"
                  onClick={() => {
                    setInlineActionType(null)
                    setInlineNotes('')
                  }}
                  className="px-2.5 py-1 rounded text-xs font-medium text-[var(--muted-foreground)] hover:text-[var(--foreground)]"
                >
                  Cancel
                </button>
                <button
                  type="button"
                  disabled={reviewLoading}
                  onClick={() => {
                    if (inlineActionType === 'REJECT') {
                      handleReviewAction('REVIEWED', 'REJECTED', inlineNotes || 'Contested by reviewer')
                    } else if (inlineActionType === 'EVIDENCE') {
                      handleReviewAction('ACTION_REQUIRED', 'REQUEST_EVIDENCE', inlineNotes || 'Additional evidence requested')
                    } else if (inlineActionType === 'ACTION') {
                      handleReviewAction('ACTIONED', undefined, undefined, inlineNotes || 'Action recorded in roadmap')
                    }
                  }}
                  className="px-3 py-1 rounded text-xs font-semibold bg-[var(--primary)] text-[var(--primary-foreground)] hover:opacity-90 disabled:opacity-50"
                >
                  {reviewLoading ? 'Submitting...' : 'Confirm'}
                </button>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* 3-Pillar Decision Intelligence Sections */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
        {/* Column 1: ORIGINAL EVIDENCE */}
        <div className="p-5 rounded-[var(--radius-lg,12px)] bg-[var(--surface)] border border-[var(--border)] flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-1.5 text-xs font-bold uppercase tracking-wider text-[var(--foreground)]">
                <BookOpen size={15} className="text-[var(--primary)]" />
                <span>Original Evidence</span>
              </div>
              <span
                className={`text-[10px] px-2 py-0.5 rounded font-bold uppercase ${
                  authority.tier === 'authoritative'
                    ? 'bg-[var(--success)]/10 text-[var(--success)] border border-[var(--success)]/20'
                    : 'bg-[var(--warning)]/10 text-[var(--warning)] border border-[var(--warning)]/20'
                }`}
              >
                {authority.label}
              </span>
            </div>

            <div className="mb-3">
              <span className="text-[10px] uppercase font-semibold text-[var(--muted-foreground)] block mb-1">
                Source & Origin
              </span>
              <div className="flex items-center gap-1.5 font-medium text-xs text-[var(--foreground)]">
                {authority.tier === 'authoritative' ? (
                  <Shield size={14} className="text-[var(--success)] shrink-0" />
                ) : (
                  <Globe size={14} className="text-[var(--warning)] shrink-0" />
                )}
                <span>{sourceName}</span>
                {externalId && (
                  <span className="font-mono text-[11px] text-[var(--muted-foreground)]">
                    ({externalId})
                  </span>
                )}
              </div>
            </div>

            <div className="mb-3">
              <span className="text-[10px] uppercase font-semibold text-[var(--muted-foreground)] block mb-1">
                Factual Evidence Excerpt
              </span>
              <div className="p-3 rounded-md bg-[var(--surface-secondary)] border border-[var(--border)] text-xs text-[var(--foreground)] leading-relaxed font-sans">
                {whatChanged}
              </div>
            </div>
          </div>

          {evidenceUrl ? (
            <div className="pt-3 border-t border-[var(--border)] flex items-center justify-between">
              <a
                href={evidenceUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-1.5 text-xs font-semibold text-[var(--primary)] hover:underline"
              >
                <span>View original source article</span>
                <ExternalLink size={13} />
              </a>
              <span className="text-[10px] text-[var(--muted-foreground)] uppercase font-mono">
                Verified Provenance
              </span>
            </div>
          ) : (
            <div className="pt-3 border-t border-[var(--border)] text-[11px] text-[var(--muted-foreground)] italic">
              Direct source URL unavailable in upstream feed.
            </div>
          )}
        </div>

        {/* Column 2: AI INTERPRETATION */}
        <div className="p-5 rounded-[var(--radius-lg,12px)] bg-[var(--surface)] border border-[var(--border)] flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-1.5 text-xs font-bold uppercase tracking-wider text-[var(--primary)]">
                <Sparkles size={15} />
                <span>AI Interpretation</span>
              </div>
              <span className="text-[10px] px-2 py-0.5 rounded font-semibold bg-[var(--surface-secondary)] text-[var(--muted-foreground)] border border-[var(--border)]">
                Machine Synthesized
              </span>
            </div>

            <div className="mb-3">
              <span className="text-[10px] uppercase font-semibold text-[var(--muted-foreground)] block mb-1">
                Clinical & Strategic Significance
              </span>
              <div className="p-3 rounded-md bg-[var(--surface-secondary)]/70 border border-[var(--border)] text-xs text-[var(--foreground)] leading-relaxed">
                {whyItMatters}
              </div>
            </div>

            {signal.speculation && (
              <div className="mb-3">
                <span className="text-[10px] uppercase font-semibold text-[var(--muted-foreground)] block mb-1">
                  Forward Projections & Assumptions
                </span>
                <div className="p-2.5 rounded-md bg-[var(--surface-secondary)] border border-[var(--border)] text-xs text-[var(--muted-foreground)] leading-relaxed">
                  {signal.speculation}
                </div>
              </div>
            )}
          </div>

          <div className="pt-3 border-t border-[var(--border)] flex items-center justify-between text-[11px] text-[var(--muted-foreground)]">
            <span>Model: {signal.model_metadata?.model || 'Local Gemma 3'}</span>
            <span className="font-mono">{signal.scoring_model_version || 'haemophilia_v2.0'}</span>
          </div>
        </div>

        {/* Column 3: SUGGESTED ACTION */}
        <div className="p-5 rounded-[var(--radius-lg,12px)] bg-[var(--surface)] border border-[var(--border)] flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-1.5 text-xs font-bold uppercase tracking-wider text-[var(--foreground)]">
                <ArrowRight size={15} className="text-[var(--accent)]" />
                <span>Suggested Action</span>
              </div>
              <span className="text-[10px] px-2 py-0.5 rounded font-semibold bg-[var(--accent)]/10 text-[var(--accent)] border border-[var(--accent)]/20">
                Actionable
              </span>
            </div>

            <div className="mb-3">
              <span className="text-[10px] uppercase font-semibold text-[var(--muted-foreground)] block mb-1">
                Target Organizational Destination
              </span>
              <div className="flex items-center gap-1.5 font-bold text-xs text-[var(--foreground)]">
                <Users size={14} className="text-[var(--primary)]" />
                <span>{functionName}</span>
              </div>
            </div>

            <div className="mb-3">
              <span className="text-[10px] uppercase font-semibold text-[var(--muted-foreground)] block mb-1">
                Action Recommendation
              </span>
              <div className="p-3 rounded-md bg-[var(--surface-secondary)] border border-[var(--border)] text-xs text-[var(--foreground)] leading-relaxed">
                {signal.suggested_action || suggestedAction}
              </div>
            </div>

            {signal.action_rationale && (
              <div className="mb-3">
                <span className="text-[10px] uppercase font-semibold text-[var(--muted-foreground)] block mb-1">
                  Action Rationale
                </span>
                <p className="text-[11px] text-[var(--muted-foreground)] m-0 leading-normal">
                  {signal.action_rationale}
                </p>
              </div>
            )}
          </div>

          <div className="pt-3 border-t border-[var(--border)] flex items-center justify-between text-[11px] text-[var(--muted-foreground)]">
            <span>Escalation: {escalateToLeadership ? 'Leadership Steering' : 'Direct Functional Queue'}</span>
            <span className="font-mono">Priority: {priorityStr}</span>
          </div>
        </div>
      </div>

      {/* Evidence Convergence Visual Tree (REQ-P10-05) */}
      <EvidenceConvergenceWidget signal={signal} />

      {/* Priority Scoring Factor Breakdown & Red-Team Falsification (REQ-P10-06, REQ-P10-07) */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
        <PriorityScoreExplainer signal={signal} />
        <RedTeamCounterFactuals signal={signal} hasContradictions={contradictions.length > 0} />
      </div>

      {/* Six-Stage Progression Stepper */}
      <div className="p-5 rounded-[var(--radius-lg,12px)] bg-[var(--surface)] border border-[var(--border)]">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <Layers size={16} className="text-[var(--primary)]" />
            <span className="text-xs font-bold uppercase tracking-wider text-[var(--foreground)]">
              Signal Intelligence Lifecycle
            </span>
          </div>
          <span className="text-xs text-[var(--muted-foreground)] font-mono">
            Stage {currentLifecycleStep} of 6
          </span>
        </div>

        <Stepper initialStep={currentLifecycleStep} showNavigationControls={false}>
          <Step title="Detected" subtitle={publishedDate} status="completed">
            <div className="text-xs">
              <p className="font-semibold text-[var(--foreground)] mb-1">
                1. Signal Ingested & Verified
              </p>
              <p className="text-[var(--muted-foreground)] m-0">
                Extracted from <strong>{sourceName}</strong> ({authority.category}) with provenance verification.
              </p>
            </div>
          </Step>

          <Step title="Classified" subtitle={signal.disease || 'Haemophilia'} status="completed">
            <div className="text-xs">
              <p className="font-semibold text-[var(--foreground)] mb-1">
                2. Classified by Domain & Target
              </p>
              <p className="text-[var(--muted-foreground)] m-0">
                Mapped to disease domain <strong>{signal.disease || 'Haemophilia'}</strong> and assigned to <strong>{functionName}</strong>.
              </p>
            </div>
          </Step>

          <Step title="Prioritized" subtitle={`${scoreValue} pts`} status={currentLifecycleStep >= 3 ? 'completed' : 'pending'}>
            <div className="text-xs">
              <p className="font-semibold text-[var(--foreground)] mb-1">
                3. Priority Assessment Computed
              </p>
              <p className="text-[var(--muted-foreground)] m-0">
                Computed priority score of <strong>{scoreValue}/100</strong> ({priorityStr}) based on clinical novelty and regulatory urgency.
              </p>
            </div>
          </Step>

          <Step title="Routed" subtitle={functionName} status={currentLifecycleStep >= 4 ? 'completed' : 'pending'}>
            <div className="text-xs">
              <p className="font-semibold text-[var(--foreground)] mb-1">
                4. Functional Routing & Escalation
              </p>
              <p className="text-[var(--muted-foreground)] m-0">
                Dispatched to <strong>{functionName}</strong> queue {escalateToLeadership ? 'with Executive Leadership alert' : ''}.
              </p>
            </div>
          </Step>

          <Step title="Reviewed" subtitle={reviewStatus} status={currentLifecycleStep >= 5 ? 'completed' : 'pending'}>
            <div className="text-xs">
              <p className="font-semibold text-[var(--foreground)] mb-1">
                5. Expert Stakeholder Review
              </p>
              <p className="text-[var(--muted-foreground)] m-0">
                Current status: <strong>{reviewStatus}</strong>.
              </p>
            </div>
          </Step>

          <Step title="Actioned" subtitle="Finalized" status={currentLifecycleStep >= 6 ? 'completed' : 'pending'}>
            <div className="text-xs">
              <p className="font-semibold text-[var(--foreground)] mb-1">
                6. Decision Execution
              </p>
              <p className="text-[var(--muted-foreground)] m-0">
                {signal.resulting_action || 'Decision closed and incorporated into therapeutic roadmap.'}
              </p>
            </div>
          </Step>
        </Stepper>
      </div>

      {/* Immutable Audit Trail Panel */}
      <div className="p-5 rounded-[var(--radius-lg,12px)] bg-[var(--surface)] border border-[var(--border)]">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            <History size={16} className="text-[var(--primary)]" />
            <h2 className="text-xs font-bold uppercase tracking-wider text-[var(--foreground)] m-0">
              Audit Trail & Workflow History
            </h2>
          </div>
          <button
            type="button"
            onClick={loadAuditHistory}
            disabled={auditLoading}
            className="inline-flex items-center gap-1 text-xs text-[var(--muted-foreground)] hover:text-[var(--foreground)] font-semibold transition-colors disabled:opacity-50"
          >
            <RefreshCw size={12} className={auditLoading ? 'animate-spin' : ''} />
            <span>Refresh</span>
          </button>
        </div>

        {auditLoading && auditHistory.length === 0 && (
          <div className="p-4 text-center text-xs text-[var(--muted-foreground)]">
            <Activity size={16} className="animate-spin inline mr-1 text-[var(--primary)]" />
            <span>Loading audit history...</span>
          </div>
        )}

        {auditError && (
          <div className="p-3 rounded-md bg-[var(--danger)]/10 text-[var(--danger)] text-xs mb-2">
            {auditError}
          </div>
        )}

        {!auditLoading && auditHistory.length === 0 && (
          <div className="p-4 rounded-md bg-[var(--surface-secondary)]/50 border border-[var(--border)] text-xs text-[var(--muted-foreground)] text-center">
            <span>No explicit review actions recorded yet. Initial lifecycle created on signal ingestion.</span>
          </div>
        )}

        {auditHistory.length > 0 && (
          <div className="flex flex-col gap-2.5">
            {auditHistory.map((item) => {
              const itemDate = new Date(item.timestamp).toLocaleString('en-US', {
                dateStyle: 'medium',
                timeStyle: 'short',
              })
              const details = item.details || {}
              return (
                <div
                  key={item.audit_id}
                  className="p-3 rounded-md bg-[var(--surface-secondary)] border border-[var(--border)] text-xs flex flex-col gap-1"
                >
                  <div className="flex items-center justify-between gap-2 flex-wrap">
                    <div className="flex items-center gap-2">
                      <span className="font-bold text-[var(--foreground)] font-mono text-[11px] px-1.5 py-0.5 rounded bg-[var(--surface)] border border-[var(--border)]">
                        {item.action}
                      </span>
                      {details.new_status && (
                        <span className="text-[var(--primary)] font-bold text-xs">
                          → {details.new_status}
                        </span>
                      )}
                    </div>
                    <span className="text-[11px] text-[var(--muted-foreground)]">{itemDate}</span>
                  </div>

                  <div className="text-[var(--muted-foreground)] text-[11px]">
                    Actor: <strong className="text-[var(--foreground)]">{item.performed_by}</strong>
                    {details.decision && (
                      <span className="ml-2">
                        · Decision: <strong className="text-[var(--success)]">{details.decision}</strong>
                      </span>
                    )}
                  </div>

                  {details.notes && (
                    <p className="text-[var(--foreground)] m-0 mt-1 pl-2 border-l-2 border-[var(--border)] italic">
                      "{details.notes}"
                    </p>
                  )}

                  {details.resulting_action && (
                    <p className="text-[var(--accent)] font-semibold m-0 mt-1 pl-2 border-l-2 border-[var(--accent)]">
                      Action: {details.resulting_action}
                    </p>
                  )}
                </div>
              )
            })}
          </div>
        )}
      </div>

      {/* Supporting Confluence & Contradiction Intelligence */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
        {/* Cross-Source Confluence */}
        <div className="p-5 rounded-[var(--radius-lg,12px)] bg-[var(--surface)] border border-[var(--border)]">
          <div className="flex items-center gap-1.5 text-xs font-bold uppercase tracking-wider text-[var(--foreground)] mb-3">
            <Zap size={15} className="text-[var(--accent)]" />
            <span>Cross-Source Confluence</span>
          </div>

          {relatedConfluences.length > 0 ? (
            <div className="flex flex-col gap-2.5">
              {relatedConfluences.map((c) => (
                <div
                  key={c.confluence_id}
                  className="p-3 rounded-md bg-[var(--surface-secondary)] border border-[var(--border)] text-xs"
                >
                  <div className="flex items-center justify-between mb-1">
                    <strong className="text-[var(--foreground)]">{c.development_title || 'Corroborating Development'}</strong>
                    <Badge tone="high">{c.score ? `${Math.round(c.score)} pts` : 'Active'}</Badge>
                  </div>
                  <p className="text-[var(--muted-foreground)] m-0 mb-1.5">
                    {c.reasoning || `${c.signal_count} corroborating signals across independent sources.`}
                  </p>
                  <span className="text-[10px] text-[var(--muted-foreground)]">
                    Type: {c.confluence_type} · {c.independent_sources_count || 2} independent sources
                  </span>
                </div>
              ))}
            </div>
          ) : (
            <div className="p-4 rounded-md bg-[var(--surface-secondary)]/50 border border-[var(--border)] text-xs text-[var(--muted-foreground)] text-center">
              <span>No cross-source confluence detected. Currently a single-source development.</span>
            </div>
          )}
        </div>

        {/* Red Team Contradictions */}
        <div className="p-5 rounded-[var(--radius-lg,12px)] bg-[var(--surface)] border border-[var(--border)]">
          <div className="flex items-center gap-1.5 text-xs font-bold uppercase tracking-wider text-[var(--foreground)] mb-3">
            <ShieldAlert size={15} className="text-[var(--danger)]" />
            <span>Red Team Contradictions</span>
          </div>

          {relatedContradictions.length > 0 ? (
            <div className="flex flex-col gap-2.5">
              {relatedContradictions.map((ct) => (
                <div
                  key={ct.contradiction_id}
                  className="p-3 rounded-md bg-[var(--danger)]/5 border border-[var(--danger)]/20 text-xs"
                >
                  <div className="flex items-center justify-between mb-1">
                    <strong className="text-[var(--danger)]">Conflicting Evidence Alert</strong>
                    <span className="text-[10px] font-bold text-[var(--danger)]">
                      {ct.severity || 'HIGH'}
                    </span>
                  </div>
                  <p className="text-[var(--foreground)] m-0 mb-1">
                    <strong>Claim A:</strong> {ct.claim_a_excerpt || ct.description || 'Primary claim'}
                  </p>
                  <p className="text-[var(--foreground)] m-0">
                    <strong>Claim B:</strong> {ct.claim_b_excerpt || ct.rule_name || 'Contradicting claim'}
                  </p>
                </div>
              ))}
            </div>
          ) : (
            <div className="p-4 rounded-md bg-[var(--surface-secondary)]/50 border border-[var(--border)] text-xs text-[var(--muted-foreground)] text-center">
              <span>No contradictions detected. Evidence is consistent across indexed registries.</span>
            </div>
          )}
        </div>
      </div>

      {/* Contextual Ask Athena Scoped Investigation */}
      <div className="p-5 rounded-[var(--radius-lg,12px)] bg-[var(--surface)] border border-[var(--border)]">
        <div className="flex items-center gap-2 mb-3">
          <BrainCircuit size={18} className="text-[var(--primary)]" />
          <h2 className="text-sm font-bold text-[var(--foreground)] m-0">
            Ask Athena About This Signal
          </h2>
        </div>
        <p className="text-xs text-[var(--muted-foreground)] mb-4 m-0">
          Query Athena with the specific context and evidence of this signal already injected into reasoning.
        </p>

        <form onSubmit={handleAskAthena} className="flex gap-2 mb-3 items-center">
          <input
            type="text"
            value={athenaQuery}
            onChange={(e) => setAthenaQuery(e.target.value)}
            placeholder={`e.g. "What are the regulatory approval risks for ${signal.disease || 'this asset'}?"`}
            className="flex-1 px-3 py-2 text-xs rounded-md bg-[var(--surface-secondary)] border border-[var(--border)] text-[var(--foreground)] placeholder:text-[var(--muted-foreground)] focus:outline-none focus:border-[var(--primary)]"
          />
          <GlowingThinkingButton
            type="submit"
            label="Analyze"
            loadingLabel="Thinking..."
            loading={athenaLoading}
            disabled={!athenaQuery.trim() || athenaLoading}
            width={120}
            height={36}
          />
        </form>

        {athenaAnswer && (
          <div className="p-4 rounded-md bg-[var(--surface-secondary)] border border-[var(--border)] text-xs leading-relaxed text-[var(--foreground)] mt-3">
            <div className="flex items-center gap-1.5 font-bold text-[var(--primary)] mb-2">
              <Bot size={14} />
              <span>Athena Clinical Synthesis:</span>
            </div>
            <div className="whitespace-pre-line">{athenaAnswer}</div>
          </div>
        )}

        {athenaError && (
          <div className="p-3 rounded-md bg-[var(--danger)]/10 border border-[var(--danger)]/20 text-xs text-[var(--danger)] mt-3">
            {athenaError}
          </div>
        )}
      </div>
    </div>
  )
}
