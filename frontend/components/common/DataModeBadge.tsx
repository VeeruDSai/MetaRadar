'use client'

import React from 'react'
import type { DataMode } from '@/types/api'

export interface DataModeBadgeProps {
  mode?: DataMode | string
  isSynthetic?: boolean
  className?: string
}

export function DataModeBadge({ mode = 'live', isSynthetic = false, className = '' }: DataModeBadgeProps) {
  if (isSynthetic || mode === 'recorded_demo' || mode === 'test_fixture') {
    return (
      <span
        className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-[10px] font-semibold uppercase tracking-wider bg-amber-950/60 text-amber-300 border border-amber-800/60 ${className}`}
        title="This view contains recorded or benchmark demo data"
      >
        <span className="w-1.5 h-1.5 rounded-full bg-amber-400" />
        Recorded Demo Data
      </span>
    )
  }

  return (
    <span
      className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-[10px] font-semibold uppercase tracking-wider bg-emerald-950/60 text-emerald-300 border border-emerald-800/60 ${className}`}
      title="Live validated pipeline data"
    >
      <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
      Live Intelligence
    </span>
  )
}
