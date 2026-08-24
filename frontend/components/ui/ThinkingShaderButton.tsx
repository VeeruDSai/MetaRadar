'use client'

import React, { useEffect, useState } from 'react'
import dynamic from 'next/dynamic'
import { useTheme } from '@/components/theme/ThemeProvider'
import '@designcodeio/threeui/style.css'
import { Sparkles } from 'lucide-react'

// Dynamically import ShaderButtons with SSR disabled to prevent Three.js SSR canvas issues
const ShaderButtonsComponent = dynamic(
  () =>
    import('@designcodeio/threeui/components/ShaderButtons').then(
      (mod) => mod.ShaderButtons
    ),
  { ssr: false }
)

export interface ThinkingShaderButtonProps {
  onClick?: () => void
  disabled?: boolean
  loading?: boolean
  label?: string
  loadingLabel?: string
  className?: string
  variant?: 'thinking-button' | 'ignition-button' | 'plasma-button' | 'tactile-button'
  hue?: number
  saturation?: number
  brightness?: number
}

export function ThinkingShaderButton({
  onClick,
  disabled = false,
  loading = false,
  label = 'Ask Athena',
  loadingLabel = 'Thinking...',
  className = '',
  variant = 'thinking-button',
  hue = 0,
  saturation = 1.0,
  brightness = 1.0,
}: ThinkingShaderButtonProps) {
  const { theme } = useTheme()
  const [mounted, setMounted] = useState(false)

  useEffect(() => {
    setMounted(true)
  }, [])

  const mode = theme === 'light' ? 'light' : 'dark'

  if (loading && mounted) {
    return (
      <div
        className={`shader-frame inline-flex items-center justify-center relative rounded-[10px] overflow-hidden ${className}`}
        style={{ minWidth: 120, height: 38 }}
      >
        <ShaderButtonsComponent
          variant={variant}
          mode={mode}
          hue={hue}
          saturation={saturation}
          brightness={brightness}
        />
      </div>
    )
  }

  return (
    <button
      type="button"
      onClick={onClick}
      disabled={disabled || loading}
      className={`relative inline-flex items-center justify-center gap-2 px-4 py-2 rounded-[8px] font-semibold text-xs transition-all duration-200 cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed ${className}`}
      style={{
        background: 'var(--primary)',
        color: 'var(--primary-foreground)',
        border: '1px solid var(--border)',
        boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
        height: 38,
      }}
    >
      <Sparkles size={14} className={loading ? 'animate-spin' : ''} />
      <span>{loading ? loadingLabel : label}</span>
    </button>
  )
}

export function Scene() {
  const { theme } = useTheme()
  const mode = theme === 'light' ? 'light' : 'dark'

  return (
    <div className="shader-frame">
      <ShaderButtonsComponent
        variant="thinking-button"
        mode={mode}
        hue={0}
        saturation={1.0}
        brightness={1.0}
      />
    </div>
  )
}
