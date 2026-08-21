'use client'

import React from 'react'
import type { Signal } from '@/types/api'
import { DataModeBadge } from '../common/DataModeBadge'

export interface SignalCardProps {
  signal: Signal
  onSelect?: (signal: Signal) => void
}

export function SignalCard({ signal, onSelect }: SignalCardProps) {
  const severityColors = {
    critical: 'bg-red-500/10 border-red-500/30 text-red-700 dark:bg-red-950/40 dark:border-red-800/60 dark:text-red-300',
    high: 'bg-orange-500/10 border-orange-500/30 text-orange-700 dark:bg-orange-950/40 dark:border-orange-800/60 dark:text-orange-300',
    medium: 'bg-amber-500/10 border-amber-500/30 text-amber-700 dark:bg-amber-950/40 dark:border-amber-800/60 dark:text-amber-300',
    low: 'bg-emerald-500/10 border-emerald-500/30 text-emerald-700 dark:bg-emerald-950/40 dark:border-emerald-800/60 dark:text-emerald-300',
    neutral: 'bg-[var(--surface-muted)] border-[var(--border)] text-[var(--muted-foreground)]',
  }

  const priorityKey = (signal.severity || 'medium').toLowerCase() as keyof typeof severityColors
  const badgeClass = severityColors[priorityKey] || severityColors.medium
  const breakdown = signal.score_breakdown
  const sourceName = signal.source_name || (signal.sources && signal.sources.length > 0 ? signal.sources[0].name : signal.source_id?.toUpperCase()) || 'SOURCE'
  const externalId = signal.external_id || signal.pmid || signal.nct_id || signal.regulatory_id

  return (
    <div
      onClick={() => onSelect?.(signal)}
      className="group relative rounded-xl border border-[var(--border)] bg-[var(--card)] p-5 hover:bg-[var(--surface-subtle)] hover:border-[var(--border-strong,var(--border))] transition cursor-pointer space-y-3 shadow-xs"
    >
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-center gap-2 flex-wrap">
          <span className={`px-2 py-0.5 rounded text-[10px] font-semibold uppercase tracking-wider border ${badgeClass}`}>
            {signal.priority || signal.severity}
          </span>
          <DataModeBadge mode={signal.data_mode} isSynthetic={signal.is_synthetic} />
          <span className="text-xs text-[var(--muted-foreground)] font-mono">{signal.detectedAt}</span>
        </div>

        <div className="flex items-center gap-1.5 shrink-0">
          <div className="text-right">
            <div className="text-xs font-mono font-semibold text-emerald-600 dark:text-emerald-400">
              {breakdown?.total !== undefined ? `${breakdown.total} pts` : (signal.score ? `${signal.score} pts` : 'Unscored')}
            </div>
            <div className="text-[10px] text-[var(--muted-foreground)]">
              {signal.scoring_status === 'not_computed' ? 'Not computed' : 'Priority Score'}
            </div>
          </div>
        </div>
      </div>

      <div className="space-y-1">
        <h3 className="text-sm font-semibold text-[var(--foreground)] group-hover:text-blue-600 dark:group-hover:text-blue-400 transition line-clamp-2">
          {signal.title}
        </h3>
        <p className="text-xs text-[var(--muted-foreground)] line-clamp-2 leading-relaxed">
          {signal.summary || signal.content}
        </p>
      </div>

      <div className="flex items-center justify-between pt-2 border-t border-[var(--border)] text-xs text-[var(--muted-foreground)]">
        <div className="flex items-center gap-2">
          <span className="text-[11px] font-mono bg-[var(--surface-muted)] px-2 py-0.5 rounded text-[var(--foreground)] border border-[var(--border)]">
            {sourceName}
          </span>
          {externalId && (
            <span className="text-[10px] font-mono text-[var(--muted-foreground)]">
              {externalId}
            </span>
          )}
        </div>
        <span className="text-xs text-blue-600 dark:text-blue-400 group-hover:underline">
          View Evidence →
        </span>
      </div>
    </div>
  )
}
