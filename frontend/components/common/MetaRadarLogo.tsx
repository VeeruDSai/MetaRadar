'use client'

import React from 'react'
import { useTheme } from '@/components/theme/ThemeProvider'

export interface MetaRadarLogoProps extends React.SVGProps<SVGSVGElement> {
  size?: number
  mode?: 'auto' | 'dark' | 'light'
  className?: string
}

export function MetaRadarLogo({
  size = 28,
  mode = 'auto',
  className = '',
  ...props
}: MetaRadarLogoProps) {
  const { isDark } = useTheme()
  const activeDark = mode === 'auto' ? isDark : mode === 'dark'

  if (!activeDark) {
    // Light Mode Logo Variant
    return (
      <svg
        width={size}
        height={size}
        viewBox="0 0 180 180"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        className={className}
        aria-label="MetaRadar Logo (Light Mode)"
        {...props}
      >
        <defs>
          <linearGradient id="logoBgLight" x1="0" y1="0" x2="180" y2="180" gradientUnits="userSpaceOnUse">
            <stop offset="0%" stopColor="#ffffff" />
            <stop offset="100%" stopColor="#f1f5f9" />
          </linearGradient>
          <linearGradient id="logoCrossLight" x1="50" y1="50" x2="130" y2="130" gradientUnits="userSpaceOnUse">
            <stop offset="0%" stopColor="#f43f5e" />
            <stop offset="100%" stopColor="#e11d48" />
          </linearGradient>
          <linearGradient id="logoSweepLight" x1="90" y1="90" x2="155" y2="35" gradientUnits="userSpaceOnUse">
            <stop offset="0%" stopColor="#e11d48" stopOpacity="0.2" />
            <stop offset="100%" stopColor="#e11d48" stopOpacity="0" />
          </linearGradient>
        </defs>

        {/* Card Background */}
        <rect width="180" height="180" rx="42" fill="url(#logoBgLight)" />
        <rect x="1" y="1" width="178" height="178" rx="41" stroke="#cbd5e1" strokeWidth="2" />

        {/* Radar Concentric Rings (Thick & Prominent) */}
        <circle cx="90" cy="90" r="66" stroke="#475569" strokeWidth="3" strokeOpacity="0.4" strokeDasharray="6 6" />
        <circle cx="90" cy="90" r="46" stroke="#334155" strokeWidth="3.5" strokeOpacity="0.55" />
        <circle cx="90" cy="90" r="26" stroke="#0f172a" strokeWidth="3.5" strokeOpacity="0.75" />

        {/* Radar Crosshairs */}
        <line x1="90" y1="18" x2="90" y2="162" stroke="#475569" strokeWidth="3" strokeOpacity="0.45" strokeLinecap="round" />
        <line x1="18" y1="90" x2="162" y2="90" stroke="#475569" strokeWidth="3" strokeOpacity="0.45" strokeLinecap="round" />

        {/* Radar Sweep Arc */}
        <path d="M 90 90 L 148 42 A 66 66 0 0 0 90 24 Z" fill="url(#logoSweepLight)" />

        {/* Sleek, Refined Medical Plus Icon (20px bar thickness, 80px span) */}
        <path
          d="
            M 80 50
            C 80 46, 84 42, 90 42
            C 96 42, 100 46, 100 50
            L 100 80
            L 130 80
            C 134 80, 138 84, 138 90
            C 138 96, 134 100, 130 100
            L 100 100
            L 100 130
            C 100 134, 96 138, 90 138
            C 84 138, 80 134, 80 130
            L 80 100
            L 50 100
            C 46 100, 42 96, 42 90
            C 42 84, 46 80, 50 80
            L 80 80
            Z
          "
          fill="url(#logoCrossLight)"
          filter="drop-shadow(0 2px 6px rgba(225, 29, 72, 0.35))"
        />

        {/* Inner Plus Shimmer Line */}
        <path
          d="
            M 88 52
            L 92 52
            L 92 88
            L 128 88
            L 128 92
            L 92 92
            L 92 128
            L 88 128
            L 88 92
            L 52 92
            L 52 88
            L 88 88
            Z
          "
          fill="#ffffff"
          fillOpacity="0.45"
        />
      </svg>
    )
  }

  // Dark Mode Logo Variant
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 180 180"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={className}
      aria-label="MetaRadar Logo (Dark Mode)"
      {...props}
    >
      <defs>
        <linearGradient id="logoBgDark" x1="0" y1="0" x2="180" y2="180" gradientUnits="userSpaceOnUse">
          <stop offset="0%" stopColor="#0e1726" />
          <stop offset="100%" stopColor="#030712" />
        </linearGradient>
        <linearGradient id="logoCrossDark" x1="50" y1="50" x2="130" y2="130" gradientUnits="userSpaceOnUse">
          <stop offset="0%" stopColor="#ff3b60" />
          <stop offset="100%" stopColor="#e11d48" />
        </linearGradient>
        <linearGradient id="logoSweepDark" x1="90" y1="90" x2="155" y2="35" gradientUnits="userSpaceOnUse">
          <stop offset="0%" stopColor="#ff3b60" stopOpacity="0.35" />
          <stop offset="100%" stopColor="#ff3b60" stopOpacity="0" />
        </linearGradient>
        <radialGradient id="logoGlowDark" cx="90" cy="90" r="70" gradientUnits="userSpaceOnUse">
          <stop offset="0%" stopColor="#e11d48" stopOpacity="0.35" />
          <stop offset="100%" stopColor="#e11d48" stopOpacity="0" />
        </radialGradient>
      </defs>

      {/* Card Background */}
      <rect width="180" height="180" rx="42" fill="url(#logoBgDark)" />
      <rect x="1" y="1" width="178" height="178" rx="41" stroke="rgba(255, 255, 255, 0.15)" strokeWidth="2" />

      {/* Radial Core Glow */}
      <circle cx="90" cy="90" r="70" fill="url(#logoGlowDark)" />

      {/* Radar Concentric Rings (Thicker & Prominent) */}
      <circle cx="90" cy="90" r="66" stroke="#94a3b8" strokeWidth="3" strokeOpacity="0.35" strokeDasharray="6 6" />
      <circle cx="90" cy="90" r="46" stroke="#cbd5e1" strokeWidth="3.5" strokeOpacity="0.5" />
      <circle cx="90" cy="90" r="26" stroke="#f1f5f9" strokeWidth="3.5" strokeOpacity="0.7" />

      {/* Radar Crosshairs */}
      <line x1="90" y1="18" x2="90" y2="162" stroke="#94a3b8" strokeWidth="3" strokeOpacity="0.4" strokeLinecap="round" />
      <line x1="18" y1="90" x2="162" y2="90" stroke="#94a3b8" strokeWidth="3" strokeOpacity="0.4" strokeLinecap="round" />

      {/* Radar Sweep Arc */}
      <path d="M 90 90 L 148 42 A 66 66 0 0 0 90 24 Z" fill="url(#logoSweepDark)" />

      {/* Sleek, Refined Medical Plus Icon (20px bar thickness, 80px span) */}
      <path
        d="
          M 80 50
          C 80 46, 84 42, 90 42
          C 96 42, 100 46, 100 50
          L 100 80
          L 130 80
          C 134 80, 138 84, 138 90
          C 138 96, 134 100, 130 100
          L 100 100
          L 100 130
          C 100 134, 96 138, 90 138
          C 84 138, 80 134, 80 130
          L 80 100
          L 50 100
          C 46 100, 42 96, 42 90
          C 42 84, 46 80, 50 80
          L 80 80
          Z
        "
        fill="url(#logoCrossDark)"
        filter="drop-shadow(0 2px 8px rgba(225, 29, 72, 0.5))"
      />

      {/* Inner Plus Shimmer Line */}
      <path
        d="
          M 88 52
          L 92 52
          L 92 88
          L 128 88
          L 128 92
          L 92 92
          L 92 128
          L 88 128
          L 88 92
          L 52 92
          L 52 88
          L 88 88
          Z
        "
        fill="#ffffff"
        fillOpacity="0.35"
      />
    </svg>
  )
}

export default MetaRadarLogo
