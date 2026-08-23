import React from 'react'

export interface MetaRadarLogoProps extends React.SVGProps<SVGSVGElement> {
  size?: number
  className?: string
}

export function MetaRadarLogo({ size = 28, className = '', ...props }: MetaRadarLogoProps) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 180 180"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={className}
      aria-label="MetaRadar Logo"
      {...props}
    >
      <defs>
        <linearGradient id="logoBgGrad" x1="0" y1="0" x2="180" y2="180" gradientUnits="userSpaceOnUse">
          <stop offset="0%" stopColor="#0f172a" />
          <stop offset="100%" stopColor="#020617" />
        </linearGradient>
        <linearGradient id="logoCrossGrad" x1="34" y1="34" x2="146" y2="146" gradientUnits="userSpaceOnUse">
          <stop offset="0%" stopColor="#ff4b6e" />
          <stop offset="100%" stopColor="#e11d48" />
        </linearGradient>
        <linearGradient id="logoSweepGrad" x1="90" y1="90" x2="155" y2="40" gradientUnits="userSpaceOnUse">
          <stop offset="0%" stopColor="#ff4b6e" stopOpacity="0.5" />
          <stop offset="100%" stopColor="#ff4b6e" stopOpacity="0" />
        </linearGradient>
        <radialGradient id="logoCoreGlow" cx="90" cy="90" r="75" gradientUnits="userSpaceOnUse">
          <stop offset="0%" stopColor="#e11d48" stopOpacity="0.4" />
          <stop offset="100%" stopColor="#e11d48" stopOpacity="0" />
        </radialGradient>
        <filter id="logoGlow" x="-20%" y="-20%" width="140%" height="140%">
          <feGaussianBlur stdDeviation="3" result="blur" />
          <feComposite in="SourceGraphic" in2="blur" operator="over" />
        </filter>
      </defs>

      {/* Background container */}
      <rect width="180" height="180" rx="42" fill="url(#logoBgGrad)" />
      <rect x="1" y="1" width="178" height="178" rx="41" stroke="rgba(255,255,255,0.15)" strokeWidth="2" />

      {/* Radial Core Glow */}
      <circle cx="90" cy="90" r="75" fill="url(#logoCoreGlow)" />

      {/* Radar Concentric Rings */}
      <circle cx="90" cy="90" r="68" stroke="#ffffff" strokeWidth="2" strokeOpacity="0.18" strokeDasharray="4 4" />
      <circle cx="90" cy="90" r="48" stroke="#ffffff" strokeWidth="2" strokeOpacity="0.25" />
      <circle cx="90" cy="90" r="28" stroke="#ffffff" strokeWidth="2" strokeOpacity="0.35" />

      {/* Radar Crosshairs */}
      <line x1="90" y1="16" x2="90" y2="164" stroke="#ffffff" strokeWidth="2" strokeOpacity="0.22" strokeLinecap="round" />
      <line x1="16" y1="90" x2="164" y2="90" stroke="#ffffff" strokeWidth="2" strokeOpacity="0.22" strokeLinecap="round" />

      {/* Radar Sweep Arc */}
      <path d="M 90 90 L 150 42 A 68 68 0 0 0 90 22 Z" fill="url(#logoSweepGrad)" />

      {/* Pharma Medical Cross with Radar Intersections */}
      <path
        d="
          M 75 42
          C 75 37.5, 78.5 34, 83 34
          L 97 34
          C 101.5 34, 105 37.5, 105 42
          L 105 75
          L 138 75
          C 142.5 75, 146 78.5, 146 83
          L 146 97
          C 146 101.5, 142.5 105, 138 105
          L 105 105
          L 105 138
          C 105 142.5, 101.5 146, 97 146
          L 83 146
          C 78.5 146, 75 142.5, 75 138
          L 75 105
          L 42 105
          C 37.5 105, 34 101.5, 34 97
          L 34 83
          C 34 78.5, 37.5 75, 42 75
          L 75 75
          Z
        "
        fill="url(#logoCrossGrad)"
        filter="url(#logoGlow)"
      />

      {/* Inner Cross Accent */}
      <path
        d="
          M 79 48
          L 101 48
          L 101 79
          L 132 79
          L 132 101
          L 101 101
          L 101 132
          L 79 132
          L 79 101
          L 48 101
          L 48 79
          L 79 79
          Z
        "
        fill="#ffffff"
        fillOpacity="0.22"
      />

      {/* Active Signal Blip */}
      <circle cx="128" cy="52" r="5" fill="#38bdf8" />
      <circle cx="128" cy="52" r="9" stroke="#38bdf8" strokeWidth="1.5" strokeOpacity="0.6" />

      {/* Central Target Core */}
      <circle cx="90" cy="90" r="5" fill="#ffffff" />
      <circle cx="90" cy="90" r="9" stroke="#ffffff" strokeWidth="2" strokeOpacity="0.85" />
    </svg>
  )
}

export default MetaRadarLogo
