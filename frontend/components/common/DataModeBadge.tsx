'use client'

import React from 'react'
import type { DataMode } from '@/types/api'

export interface DataModeBadgeProps {
  mode?: DataMode | string
  isSynthetic?: boolean
  className?: string
}

export function DataModeBadge({ mode = 'live', isSynthetic = false, className = '' }: DataModeBadgeProps) {
  if (isSynthetic || mode === 'test_fixture' || mode === 'synthetic') {
    return (
      <span
        className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-[10px] font-semibold uppercase tracking-wider bg-rose-50 text-rose-700 border border-rose-200 dark:bg-rose-950/60 dark:text-rose-300 dark:border-rose-800/60 ${className}`}
        title="Test fixture / synthetic data — not from a live external source"
      >
        <span className="w-1.5 h-1.5 rounded-full bg-rose-500" />
        TEST FIXTURE
      </span>
    )
  }

  if (mode === 'recorded_demo' || mode === 'benchmark') {
    return (
      <span
        className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-[10px] font-semibold uppercase tracking-wider bg-amber-50 text-amber-700 border border-amber-200 dark:bg-amber-950/60 dark:text-amber-300 dark:border-amber-800/60 ${className}`}
        title="Recorded demonstration snapshot"
      >
        <span className="w-1.5 h-1.5 rounded-full bg-amber-500" />
        RECORDED DEMO
      </span>
    )
  }

  return (
    <span
      className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-[10px] font-semibold uppercase tracking-wider bg-emerald-50 text-emerald-700 border border-emerald-200 dark:bg-emerald-950/60 dark:text-emerald-300 dark:border-emerald-800/60 ${className}`}
      title="Live validated pipeline intelligence"
    >
      <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
      LIVE INTELLIGENCE
    </span>
  )
}
