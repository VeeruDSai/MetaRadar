'use client'

import React from 'react'
import type { DataMode } from '@/types/api'
import { Badge } from '@/components/metaradar'

export interface DataModeBadgeProps {
  mode?: DataMode | string
  isSynthetic?: boolean
  className?: string
}

export function DataModeBadge({ mode = 'live', isSynthetic = false, className = '' }: DataModeBadgeProps) {
  if (isSynthetic || mode === 'test_fixture' || mode === 'synthetic') {
    return (
      <Badge tone="critical">
        TEST FIXTURE
      </Badge>
    )
  }

  if (mode === 'recorded_demo' || mode === 'benchmark') {
    return (
      <Badge tone="high">
        RECORDED DEMO
      </Badge>
    )
  }

  return (
    <Badge tone="low">
      LIVE INTELLIGENCE
    </Badge>
  )
}
