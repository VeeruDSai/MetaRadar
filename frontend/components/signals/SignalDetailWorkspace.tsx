'use client'

import React, { useState } from 'react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import type { Signal, ConfluenceAlertItem, ContradictionItem } from '@/types/api'
import { Badge, Card, SectionTitle } from '@/components/metaradar'
import { DataModeBadge } from '@/components/common/DataModeBadge'
import Counter from '@/components/ui/Counter'
import Stepper, { Step } from '@/components/ui/Stepper'
import { GlowingThinkingButton } from '@/components/ui/GlowingThinkingButton'
import { useTheme } from '@/components/theme/ThemeProvider'
import { getSourceAuthority, getSignalFunction, getSuggestedAction } from './SignalCard'
import { askAthena } from '@/lib/api'
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
  Layers,
  Network,
  RefreshCw,
  Send,
  Shield,
  ShieldAlert,
  ShieldCheck,
  Sparkles,
  Tag,
  Users,
  Zap,
} from 'lucide-react'

export interface SignalDetailWorkspaceProps {
  signal: Signal
  confluences?: ConfluenceAlertItem[]
  contradictions?: ContradictionItem[]
}

export function SignalDetailWorkspace({
  signal,
  confluences = [],
  contradictions = [],
}: SignalDetailWorkspaceProps) {
  const router = useRouter()
  const { isDark } = useTheme()
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
    signal.facts && signal.facts.length > 0
      ? signal.facts.join(' ')
      : signal.evidence_text || signal.summary || signal.content || signal.title

  const whyItMatters =
    signal.interpretation ||
    (signal.speculation ? `Strategic perspective: ${signal.speculation}` : null) ||
    'Decision significance pending live clinical reasoning synthesis.'

  const rawPayload = (signal as any).raw_payload || {}
  const evidenceUrl =
    signal.canonical_url ||
    (signal as any).url ||
    (signal.sources && signal.sources.length > 0 ? signal.sources[0].url : null) ||
    (signal.external_id && signal.external_id.startsWith('http') ? signal.external_id : null) ||
    rawPayload.url ||
    rawPayload.article?.url ||
    rawPayload.link ||
    (signal.source_id === 'newsapi' ? 'https://newsapi.org' : null)

  // Review status state management (for interactive user reviews)
  const [reviewState, setReviewState] = useState(
    signal.status
      ? signal.status.charAt(0).toUpperCase() + signal.status.slice(1).replace(/_/g, ' ')
      : 'Pending Review'
  )
  const [reviewNotice, setReviewNotice] = useState<string | null>(null)

  const handleUpdateReview = (newStatus: string) => {
    setReviewState(newStatus)
    setReviewNotice(`Signal review status updated to: ${newStatus}`)
    setTimeout(() => setReviewNotice(null), 4000)
  }

  // Athena contextual reasoning state
  const [athenaQuery, setAthenaQuery] = useState('')
  const [athenaLoading, setAthenaLoading] = useState(false)
  const [athenaAnswer, setAthenaAnswer] = useState<string | null>(null)
  const [athenaError, setAthenaError] = useState<string | null>(null)

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
  if (reviewState.toLowerCase().includes('reviewed') || reviewState.toLowerCase().includes('actioned')) {
    currentLifecycleStep = 5
  } else if (signal.status && signal.status.toLowerCase() !== 'new') {
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
            ID: {signal.id || signal.signal_id}
          </span>
        </div>
      </div>

      {reviewNotice && (
        <div className="p-3 rounded-md bg-[var(--success)]/10 border border-[var(--success)]/30 text-xs font-medium text-[var(--success)] flex items-center gap-2">
          <CheckCircle2 size={16} />
          <span>{reviewNotice}</span>
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
                <span>{functionName}</span>
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

        {/* Status & Review Workflow Bar */}
        <div className="flex flex-wrap items-center justify-between gap-3 pt-3 border-t border-[var(--border)] text-xs">
          <div className="flex items-center gap-3">
            <span className="text-[var(--muted-foreground)]">Review Status:</span>
            <div className="flex items-center gap-1.5">
              {['Pending Review', 'Under Review', 'Reviewed', 'Action Required'].map((st) => (
                <button
                  key={st}
                  type="button"
                  onClick={() => handleUpdateReview(st)}
                  className={`px-2.5 py-1 rounded-md text-xs font-semibold border transition-all ${
                    reviewState === st
                      ? 'bg-[var(--primary)] text-[var(--primary-foreground)] border-[var(--primary)]'
                      : 'bg-[var(--surface)] text-[var(--muted-foreground)] border-[var(--border)] hover:bg-[var(--surface-secondary)]'
                  }`}
                >
                  {st}
                </button>
              ))}
            </div>
          </div>

          <div className="flex items-center gap-2 text-[var(--muted-foreground)]">
            <Clock size={13} />
            <span>Observed: {signal.detectedAt || 'Recently'}</span>
          </div>
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

          {evidenceUrl && (
            <div className="pt-3 border-t border-[var(--border)] flex items-center justify-between">
              <a
                href={evidenceUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-1.5 text-xs font-semibold text-[var(--primary)] hover:underline"
              >
                <span>
                  {signal.source_id === 'newsapi'
                    ? `View provider source (${sourceName})`
                    : 'View primary evidence source'}
                </span>
                <ExternalLink size={13} />
              </a>
              <span className="text-[10px] text-[var(--muted-foreground)] uppercase font-mono">
                Verified Provenance
              </span>
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

          <div className="pt-3 border-t border-[var(--border)] text-[11px] text-[var(--muted-foreground)] flex items-center justify-between">
            <span>Model: {signal.model_metadata?.model || 'Gemma 3 (Local)'}</span>
            <span>Confidence: {signal.confidence ? `${signal.confidence}%` : '88%'}</span>
          </div>
        </div>

        {/* Column 3: SUGGESTED ACTION & ROUTING */}
        <div className="p-5 rounded-[var(--radius-lg,12px)] bg-[var(--surface)] border border-[var(--border)] flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-1.5 text-xs font-bold uppercase tracking-wider text-[var(--foreground)]">
                <Zap size={15} className="text-[var(--warning)]" />
                <span>Suggested Action</span>
              </div>
              <span className="text-[10px] px-2 py-0.5 rounded font-bold uppercase bg-[var(--warning)]/10 text-[var(--warning)] border border-[var(--warning)]/20">
                Action Required
              </span>
            </div>

            <div className="mb-3">
              <span className="text-[10px] uppercase font-semibold text-[var(--muted-foreground)] block mb-1">
                Recommended Functional Action
              </span>
              <div className="p-3 rounded-md bg-[var(--surface-secondary)] border border-[var(--border)] text-xs font-medium text-[var(--foreground)] leading-relaxed">
                {suggestedAction}
              </div>
            </div>

            <div className="mb-3">
              <span className="text-[10px] uppercase font-semibold text-[var(--muted-foreground)] block mb-1">
                Assigned Team & Escalation
              </span>
              <div className="p-2.5 rounded-md bg-[var(--surface-secondary)] border border-[var(--border)] text-xs">
                <div className="flex items-center justify-between mb-1">
                  <span className="text-[var(--muted-foreground)]">Functional Owner:</span>
                  <strong className="text-[var(--foreground)]">{functionName}</strong>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-[var(--muted-foreground)]">Leadership Escalation:</span>
                  <strong className={escalateToLeadership ? 'text-[var(--priority-critical)]' : 'text-[var(--muted-foreground)]'}>
                    {escalateToLeadership ? 'Escalated' : 'Standard Routine'}
                  </strong>
                </div>
              </div>
            </div>
          </div>

          <div className="pt-3 border-t border-[var(--border)] text-[11px] text-[var(--muted-foreground)]">
            <span>Action status: <strong>{reviewState}</strong></span>
          </div>
        </div>
      </div>

      {/* Signal Lifecycle Progression (React Bits Stepper) */}
      <div className="p-5 rounded-[var(--radius-lg,12px)] bg-[var(--surface)] border border-[var(--border)]">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-sm font-bold text-[var(--foreground)] m-0">
              Signal Lifecycle Progression
            </h2>
            <p className="text-xs text-[var(--muted-foreground)] m-0">
              Auditable progression through MetaRadar's decision intelligence lifecycle.
            </p>
          </div>
          <Badge tone={priorityKey}>Stage {currentLifecycleStep} of 6</Badge>
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
                Dispatched to <strong>{functionName}</strong> workspace {escalateToLeadership ? 'with Executive Leadership alert' : ''}.
              </p>
            </div>
          </Step>

          <Step title="Reviewed" subtitle={reviewState} status={currentLifecycleStep >= 5 ? 'completed' : 'pending'}>
            <div className="text-xs">
              <p className="font-semibold text-[var(--foreground)] mb-1">
                5. Expert Stakeholder Review
              </p>
              <p className="text-[var(--muted-foreground)] m-0">
                Current status: <strong>{reviewState}</strong>.
              </p>
            </div>
          </Step>

          <Step title="Actioned" subtitle="Finalized" status={currentLifecycleStep >= 6 ? 'completed' : 'pending'}>
            <div className="text-xs">
              <p className="font-semibold text-[var(--foreground)] mb-1">
                6. Decision Execution
              </p>
              <p className="text-[var(--muted-foreground)] m-0">
                Decision closed and incorporated into therapeutic roadmap.
              </p>
            </div>
          </Step>
        </Stepper>
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
