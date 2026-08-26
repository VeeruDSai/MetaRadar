'use client'

import React from 'react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import type { Signal } from '@/types/api'
import { Badge } from '@/components/metaradar'
import { DataModeBadge } from '../common/DataModeBadge'
import Counter from '@/components/ui/Counter'
import {
  ArrowRight,
  Building2,
  CheckCircle,
  Clock,
  ExternalLink,
  FileCheck,
  Globe,
  Layers,
  Network,
  Shield,
  ShieldAlert,
  Sparkles,
  Zap,
} from 'lucide-react'

export interface SignalCardProps {
  signal: Signal
  onSelect?: (signal: Signal) => void
  showFullDetails?: boolean
  className?: string
}

/** Helper to categorize source authority tier */
export function getSourceAuthority(sourceId?: string, sourceName?: string): {
  tier: 'authoritative' | 'discovery'
  category: string
  label: string
} {
  const s = (sourceId || sourceName || '').toLowerCase()
  if (s.includes('fda') || s.includes('ema') || s.includes('regulatory') || s.includes('mhra') || s.includes('pmda')) {
    return { tier: 'authoritative', category: 'Regulatory Agency', label: 'Authoritative' }
  }
  if (s.includes('trial') || s.includes('clinical') || s.includes('nct')) {
    return { tier: 'authoritative', category: 'Clinical Registry', label: 'Authoritative' }
  }
  if (s.includes('pubmed') || s.includes('ncbi') || s.includes('nejm') || s.includes('lancet') || s.includes('journal')) {
    return { tier: 'authoritative', category: 'Peer-Reviewed Journal', label: 'Authoritative' }
  }
  if (s.includes('ash') || s.includes('eha') || s.includes('wfh') || s.includes('congress') || s.includes('symposium')) {
    return { tier: 'authoritative', category: 'Medical Congress', label: 'Authoritative' }
  }
  return { tier: 'discovery', category: 'Discovery Feed', label: 'Discovery' }
}

/** Helper to deduce relevant functional team and escalation status */
export function getSignalFunction(signal: Signal): {
  functionName: string
  escalateToLeadership: boolean
} {
  const priority = (signal.priority || signal.severity || 'MEDIUM').toUpperCase()
  const score = signal.score_breakdown?.total ?? signal.score ?? 0
  const isHighImpact = priority === 'CRITICAL' || priority === 'HIGH' || score >= 75

  // Check explicit stakeholders from backend first
  if (signal.stakeholders && Object.keys(signal.stakeholders).length > 0) {
    const sorted = Object.entries(signal.stakeholders).sort((a, b) => b[1] - a[1])
    const top = sorted[0][0].replace(/_/g, ' ')
    const formatted = top.charAt(0).toUpperCase() + top.slice(1)
    return {
      functionName: formatted,
      escalateToLeadership: isHighImpact,
    }
  }

  // Type-based domain fallback
  const st = (signal.signal_type || '').toLowerCase()
  if (st.includes('regulatory') || st.includes('approval') || st.includes('label')) {
    return { functionName: 'Regulatory Affairs', escalateToLeadership: isHighImpact }
  }
  if (st.includes('safety') || st.includes('adverse') || st.includes('warning') || st.includes('blackbox')) {
    return { functionName: 'Safety & Pharmacovigilance', escalateToLeadership: isHighImpact }
  }
  if (st.includes('clinical') || st.includes('trial') || st.includes('phase') || st.includes('efficacy')) {
    return { functionName: 'Medical Affairs', escalateToLeadership: isHighImpact }
  }
  if (st.includes('commercial') || st.includes('market') || st.includes('reimbursement') || st.includes('pricing')) {
    return { functionName: 'Market Access & Pricing', escalateToLeadership: isHighImpact }
  }
  if (st.includes('patent') || st.includes('ip') || st.includes('exclusivity')) {
    return { functionName: 'Legal & Intellectual Property', escalateToLeadership: isHighImpact }
  }

  return { functionName: 'Medical Affairs', escalateToLeadership: isHighImpact }
}

/** Helper to deduce suggested action when not explicitly provided by scoring engine */
export function getSuggestedAction(signal: Signal): string {
  if (signal.score_breakdown?.reason) {
    return signal.score_breakdown.reason
  }
  const { functionName, escalateToLeadership } = getSignalFunction(signal)
  const priority = (signal.priority || signal.severity || 'MEDIUM').toUpperCase()

  if (escalateToLeadership && priority === 'CRITICAL') {
    return `Immediate escalation to Executive Leadership & ${functionName} committee for risk review.`
  }
  if (functionName.includes('Regulatory')) {
    return 'Review regulatory timeline and monitor upcoming milestone readout.'
  }
  if (functionName.includes('Safety')) {
    return 'Conduct internal safety evaluation and cross-reference with surveillance registry.'
  }
  if (functionName.includes('Medical')) {
    return 'Assess clinical trial endpoints and benchmark against competitive asset profile.'
  }
  if (functionName.includes('Market Access')) {
    return 'Assess reimbursement implications and formulary placement impact.'
  }
  return 'Monitor incoming evidence for multi-source corroboration.'
}

export function SignalCard({
  signal,
  onSelect,
  showFullDetails = false,
  className = '',
}: SignalCardProps) {
  const router = useRouter()
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
    'Decision significance pending automated cross-source synthesis.'

  const rawStatus = (signal.review_status || signal.status || 'UNREVIEWED').toUpperCase()
  const reviewStatusLabel = rawStatus.replace(/_/g, ' ')

  const sourcesCount = signal.sources?.length || 1
  const publishedDate = signal.published_at
    ? new Date(signal.published_at).toLocaleDateString('en-US', {
        day: 'numeric',
        month: 'short',
        year: 'numeric',
      })
    : signal.detectedAt || 'Recent'

  const signalUrl = `/signals/${encodeURIComponent(signal.id || signal.signal_id || '')}`

  const handleCardClick = (e: React.MouseEvent) => {
    if ((e.target as HTMLElement).closest('a, button')) return
    router.push(signalUrl)
  }

  return (
    <article
      onClick={handleCardClick}
      data-scroll-reveal="signal"
      className={`group relative flex flex-col justify-between p-4.5 rounded-[var(--radius-lg,12px)] bg-[var(--surface)] border border-[var(--border)] hover:border-[var(--border-selected)] transition-all duration-200 hover:shadow-md cursor-pointer ${className}`}
    >
      {/* 1. Header: Priority, Score Counter, Timestamp, Truthfulness */}
      <div>
        <div className="flex items-center justify-between gap-3 mb-3">
          <div className="flex items-center gap-2 flex-wrap">
            <Badge tone={priorityKey}>{priorityStr}</Badge>
            {escalateToLeadership && (
              <span className="inline-flex items-center gap-1 text-[11px] font-semibold px-2 py-0.5 rounded-full bg-[var(--priority-critical)]/10 text-[var(--priority-critical)] border border-[var(--priority-critical)]/20">
                <ShieldAlert size={12} />
                <span>Escalate: Leadership</span>
              </span>
            )}
            <DataModeBadge mode={signal.data_mode} isSynthetic={signal.is_synthetic} />
          </div>

          {/* Priority Score Counter */}
          <div className="flex items-center gap-1.5 text-right shrink-0 bg-[var(--surface-secondary)] px-2.5 py-1 rounded-md border border-[var(--border)]">
            <div className="flex flex-col items-end">
              <div className="flex items-baseline gap-0.5">
                <Counter
                  value={scoreValue}
                  places={[100, 10, 1]}
                  fontSize={20}
                  fontWeight={800}
                  textColor="var(--foreground)"
                  digitPlaceHolders
                  accessibleLabel={`Priority score ${scoreValue} out of 100`}
                />
                <span className="text-[10px] text-[var(--muted-foreground)] font-mono">/100</span>
              </div>
              <span className="text-[9px] uppercase tracking-wider text-[var(--muted-foreground)] font-semibold">
                Priority Score
              </span>
            </div>
          </div>
        </div>

        {/* 2. Signal Title */}
        <h3 className="text-[15px] font-bold text-[var(--foreground)] group-hover:text-[var(--primary)] transition-colors leading-snug m-0 mb-2.5">
          <Link
            href={signalUrl}
            className="hover:underline text-inherit inline-flex items-baseline gap-1"
          >
            {signal.title}
          </Link>
        </h3>

        {/* 3. WHAT CHANGED (Evidence Grounded) */}
        <div className="mb-2.5">
          <div className="text-[10px] font-bold uppercase tracking-wider text-[var(--muted-foreground)] mb-0.5 flex items-center gap-1">
            <span className="w-1.5 h-1.5 rounded-full bg-[var(--primary)]" />
            <span>What Changed</span>
          </div>
          <p className="text-xs text-[var(--foreground)]/90 leading-relaxed m-0 line-clamp-2">
            {whatChanged}
          </p>
        </div>

        {/* 4. WHY IT MATTERS (Decision Significance) */}
        <div className="mb-3 p-2 rounded-md bg-[var(--surface-secondary)]/60 border border-[var(--border)]">
          <div className="text-[10px] font-bold uppercase tracking-wider text-[var(--primary)] mb-0.5 flex items-center gap-1">
            <Sparkles size={11} />
            <span>Why It Matters</span>
          </div>
          <p className="text-xs text-[var(--muted-foreground)] leading-relaxed m-0 line-clamp-2">
            {whyItMatters}
          </p>
        </div>

        {/* 5. Functional Routing & Source Credibility Grid */}
        <div className="grid grid-cols-2 gap-2 my-2.5 pt-2 border-t border-[var(--border)] text-xs">
          <div>
            <span className="text-[10px] uppercase font-semibold text-[var(--muted-foreground)] block mb-0.5">
              Function
            </span>
            <div className="flex items-center gap-1 font-medium text-[var(--foreground)] truncate">
              <Network size={13} className="text-[var(--primary)] shrink-0" />
              <span className="truncate">{functionName}</span>
            </div>
          </div>

          <div>
            <span className="text-[10px] uppercase font-semibold text-[var(--muted-foreground)] block mb-0.5">
              Source & Credibility
            </span>
            <div className="flex items-center gap-1 font-medium text-[var(--foreground)] truncate">
              {authority.tier === 'authoritative' ? (
                <Shield size={13} className="text-[var(--success)] shrink-0" />
              ) : (
                <Globe size={13} className="text-[var(--warning)] shrink-0" />
              )}
              <span className="truncate">{sourceName}</span>
              <span
                className={`text-[9px] px-1 py-0.2 rounded font-semibold uppercase shrink-0 ${
                  authority.tier === 'authoritative'
                    ? 'bg-[var(--success)]/10 text-[var(--success)]'
                    : 'bg-[var(--warning)]/10 text-[var(--warning)]'
                }`}
              >
                {authority.label}
              </span>
            </div>
          </div>
        </div>

        {/* 6. SUGGESTED ACTION (Revealed clearly) */}
        <div className="my-2.5 p-2 rounded-md bg-[var(--surface-secondary)] border border-[var(--border)]">
          <div className="text-[10px] font-bold uppercase tracking-wider text-[var(--foreground)] mb-0.5 flex items-center gap-1">
            <Zap size={11} className="text-[var(--warning)]" />
            <span>Suggested Action</span>
          </div>
          <p className="text-xs text-[var(--foreground)] font-medium leading-relaxed m-0 line-clamp-2">
            {suggestedAction}
          </p>
        </div>
      </div>

      {/* 7. Footer: Review Status, Provenance Counts, & CTA */}
      <div className="flex items-center justify-between pt-2.5 border-t border-[var(--border)] text-xs text-[var(--muted-foreground)] mt-2">
        <div className="flex items-center gap-2 flex-wrap">
          <span className="inline-flex items-center gap-1.5 text-[11px] font-medium">
            <span
              className={`w-2 h-2 rounded-full shrink-0 ${
                rawStatus === 'UNREVIEWED'
                  ? 'bg-[var(--warning)]'
                  : rawStatus === 'IN_REVIEW'
                  ? 'bg-[var(--primary)]'
                  : rawStatus === 'REVIEWED'
                  ? 'bg-[var(--success)]'
                  : rawStatus === 'ACTIONED'
                  ? 'bg-[var(--accent)]'
                  : 'bg-[var(--muted-foreground)]'
              }`}
            />
            <span>Queue: <strong className="text-[var(--foreground)]">{reviewStatusLabel}</strong></span>
          </span>
          <span className="text-[11px] text-[var(--muted-foreground)]">·</span>
          <span className="text-[11px] text-[var(--muted-foreground)]">
            {sourcesCount} {sourcesCount === 1 ? 'source' : 'sources'} · {publishedDate}
          </span>
        </div>

        <Link
          href={signalUrl}
          className="inline-flex items-center gap-1 font-semibold text-[var(--primary)] hover:underline text-xs shrink-0"
        >
          <span>View signal</span>
          <ArrowRight size={13} />
        </Link>
      </div>
    </article>
  )
}
