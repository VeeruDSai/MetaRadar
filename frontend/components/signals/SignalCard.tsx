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
    neutral: 'bg-slate-100 border-slate-200 text-slate-700 dark:bg-slate-900 dark:border-slate-800 dark:text-slate-300',
  }

  const priorityKey = (signal.severity || 'medium').toLowerCase() as keyof typeof severityColors
  const badgeClass = severityColors[priorityKey] || severityColors.medium

  const breakdown = signal.score_breakdown

  return (
    <div
      onClick={() => onSelect?.(signal)}
      className="group relative rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900/50 p-5 hover:bg-slate-50 dark:hover:bg-slate-900 hover:border-slate-300 dark:hover:border-slate-700 transition cursor-pointer space-y-3 shadow-sm"
    >
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-center gap-2 flex-wrap">
          <span className={`px-2 py-0.5 rounded text-[10px] font-semibold uppercase tracking-wider border ${badgeClass}`}>
            {signal.priority || signal.severity}
          </span>
          <DataModeBadge mode={signal.data_mode} isSynthetic={signal.is_synthetic} />
          <span className="text-xs text-slate-500 dark:text-slate-400 font-mono">{signal.detectedAt}</span>
        </div>

        <div className="flex items-center gap-1.5 shrink-0">
          <div className="text-right">
            <div className="text-xs font-mono font-semibold text-emerald-600 dark:text-emerald-400">
              {breakdown?.total !== undefined ? `${breakdown.total} pts` : (signal.score ? `${signal.score} pts` : 'Unscored')}
            </div>
            <div className="text-[10px] text-slate-500">
              {signal.scoring_status === 'not_computed' ? 'Not computed' : 'Priority Score'}
            </div>
          </div>
        </div>
      </div>

      <div className="space-y-1">
        <h3 className="text-sm font-semibold text-slate-900 dark:text-slate-200 group-hover:text-blue-600 dark:group-hover:text-blue-400 transition line-clamp-2">
          {signal.title}
        </h3>
        <p className="text-xs text-slate-600 dark:text-slate-400 line-clamp-2 leading-relaxed">
          {signal.summary || signal.content}
        </p>
      </div>

      <div className="flex items-center justify-between pt-2 border-t border-slate-100 dark:border-slate-800/60 text-xs text-slate-500">
        <div className="flex items-center gap-2">
          {signal.sources?.map((s, i) => (
            <span key={i} className="text-[11px] font-mono bg-slate-100 dark:bg-slate-800/80 px-2 py-0.5 rounded text-slate-700 dark:text-slate-300">
              {s.name}
            </span>
          ))}
        </div>
        <span className="text-xs text-blue-600 dark:text-blue-400 group-hover:underline">
          View Evidence →
        </span>
      </div>
    </div>
  )
}
