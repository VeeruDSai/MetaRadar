'use client'

import React from 'react'
import type { Signal } from '@/types/api'
import { Card, Badge } from '@/components/metaradar'
import { DataModeBadge } from '../common/DataModeBadge'
import { ExternalLink } from 'lucide-react'

export interface SignalCardProps {
  signal: Signal
  onSelect?: (signal: Signal) => void
}

export function SignalCard({ signal, onSelect }: SignalCardProps) {
  const priorityKey = (signal.severity || signal.priority || 'medium').toLowerCase() as 'critical' | 'high' | 'medium' | 'low' | 'neutral'
  const breakdown = signal.score_breakdown
  const sourceName = signal.source_name || (signal.sources && signal.sources.length > 0 ? signal.sources[0].name : signal.source_id?.toUpperCase()) || 'SOURCE'
  const externalId = signal.external_id || signal.pmid || signal.nct_id || signal.regulatory_id

  return (
    <Card
      className="cursor-pointer transition hover:border-[var(--border-selected)] flex flex-col justify-between"
    >
      <div onClick={() => onSelect?.(signal)}>
        <div className="flex items-start justify-between gap-3 mb-2">
          <div className="flex items-center gap-2 flex-wrap">
            <Badge tone={priorityKey}>{signal.priority || signal.severity}</Badge>
            <DataModeBadge mode={signal.data_mode} isSynthetic={signal.is_synthetic} />
            <span className="text-[11px] text-[var(--muted-foreground)] font-mono">{signal.detectedAt}</span>
          </div>

          <div className="text-right shrink-0">
            <div className="text-xs font-mono font-bold" style={{ color: 'var(--success)' }}>
              {breakdown?.total !== undefined ? `${breakdown.total} pts` : (signal.score ? `${signal.score} pts` : 'Unscored')}
            </div>
            <div className="text-[9px] uppercase tracking-wider text-[var(--muted-foreground)]">
              {signal.scoring_status === 'not_computed' ? 'Not computed' : 'Priority Score'}
            </div>
          </div>
        </div>

        <div className="my-2">
          <h3 className="text-sm font-semibold text-[var(--foreground)] hover:text-[var(--primary)] transition line-clamp-2 m-0 mb-1">
            {signal.title}
          </h3>
          <p className="text-xs text-[var(--muted-foreground)] line-clamp-2 leading-relaxed m-0">
            {signal.summary || signal.content}
          </p>
        </div>

        {/* Provenance Metadata Row */}
        <div className="flex items-center gap-2.5 flex-wrap text-[10px] text-[var(--muted-foreground)] my-2 pt-1">
          {signal.pmid && (
            <span>PMID: <code className="font-mono">{signal.pmid}</code></span>
          )}
          {signal.nct_id && (
            <span>NCT: <code className="font-mono">{signal.nct_id}</code></span>
          )}
          {signal.published_at && (
            <span>Published: {new Date(signal.published_at).toLocaleDateString()}</span>
          )}
        </div>
      </div>

      <div className="flex items-center justify-between pt-2 border-t border-[var(--border)] text-xs text-[var(--muted-foreground)] mt-2">
        <div className="flex items-center gap-2">
          <Badge tone="neutral">{sourceName}</Badge>
          {externalId && (
            <span className="text-[10px] font-mono text-[var(--muted-foreground)]">
              {externalId}
            </span>
          )}
        </div>
        <button
          onClick={() => onSelect?.(signal)}
          className="text-link text-xs inline-flex items-center gap-1 border-0 bg-transparent p-0"
        >
          <span>View Evidence</span>
          <ExternalLink size={12} />
        </button>
      </div>
    </Card>
  )
}
