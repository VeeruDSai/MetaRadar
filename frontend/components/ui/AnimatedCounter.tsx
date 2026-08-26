'use client'

import React, { useEffect, useState } from 'react'

export interface AnimatedCounterProps {
  value: number
  duration?: number
  className?: string
}

export function AnimatedCounter({
  value,
  duration = 800,
  className = '',
}: AnimatedCounterProps) {
  const [displayValue, setDisplayValue] = useState(0)

  useEffect(() => {
    let startTimestamp: number | null = null
    const startVal = 0
    const endVal = typeof value === 'number' && !isNaN(value) ? value : 0

    if (endVal === 0) {
      setDisplayValue(0)
      return
    }

    let animId: number

    const step = (timestamp: number) => {
      if (!startTimestamp) startTimestamp = timestamp
      const progress = Math.min((timestamp - startTimestamp) / duration, 1)
      // Ease out cubic: snappy start, silky smooth deceleration to final value
      const ease = 1 - Math.pow(1 - progress, 3)
      const current = Math.round(startVal + (endVal - startVal) * ease)
      setDisplayValue(current)

      if (progress < 1) {
        animId = requestAnimationFrame(step)
      }
    }

    animId = requestAnimationFrame(step)
    return () => {
      if (animId) cancelAnimationFrame(animId)
    }
  }, [value, duration])

  return <span className={className}>{displayValue}</span>
}

export default AnimatedCounter
