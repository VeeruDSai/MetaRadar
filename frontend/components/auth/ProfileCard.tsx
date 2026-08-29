'use client'

import React, { useRef, useCallback, useState } from 'react'
import './ProfileCard.css'

export interface ProfileCardProps {
  avatarUrl?: string
  name: string
  title: string
  handle: string
  status?: string
  contactText?: string
  onContactClick?: () => void
  roleColor?: string
  roleId?: string
}

const ROLE_GLOW_MAP: Record<string, string> = {
  MEDICAL_AFFAIRS: 'rgba(52, 211, 153, 0.45)',
  REGULATORY: 'rgba(96, 165, 250, 0.45)',
  SAFETY: 'rgba(248, 113, 113, 0.45)',
  MARKET_ACCESS: 'rgba(251, 191, 36, 0.45)',
  COMMUNICATIONS: 'rgba(167, 139, 250, 0.45)',
  LEADERSHIP: 'rgba(129, 140, 248, 0.55)',
  ADMIN: 'rgba(148, 163, 184, 0.45)',
}

const ROLE_BORDER_MAP: Record<string, string> = {
  MEDICAL_AFFAIRS: '#34d399',
  REGULATORY: '#60a5fa',
  SAFETY: '#f87171',
  MARKET_ACCESS: '#fbbf24',
  COMMUNICATIONS: '#a78bfa',
  LEADERSHIP: '#818cf8',
  ADMIN: '#94a3b8',
}

export default function ProfileCard({
  avatarUrl,
  name,
  title,
  handle,
  status = 'Online',
  contactText = 'Select Role & Auto-Fill',
  onContactClick,
  roleId = 'MEDICAL_AFFAIRS',
}: ProfileCardProps) {
  const cardRef = useRef<HTMLDivElement>(null)
  const [isHovered, setIsHovered] = useState(false)

  const handleMouseMove = useCallback((e: React.MouseEvent<HTMLDivElement>) => {
    if (!cardRef.current) return
    const rect = cardRef.current.getBoundingClientRect()
    const x = e.clientX - rect.left
    const y = e.clientY - rect.top

    const centerX = rect.width / 2
    const centerY = rect.height / 2

    // Max rotation 12 degrees
    const rotateX = -((y - centerY) / centerY) * 12
    const rotateY = ((x - centerX) / centerX) * 12

    const pointerX = `${(x / rect.width) * 100}%`
    const pointerY = `${(y / rect.height) * 100}%`

    cardRef.current.style.setProperty('--pointer-x', pointerX)
    cardRef.current.style.setProperty('--pointer-y', pointerY)
    cardRef.current.style.setProperty('--rotate-x', `${rotateX.toFixed(2)}deg`)
    cardRef.current.style.setProperty('--rotate-y', `${rotateY.toFixed(2)}deg`)
  }, [])

  const handleMouseEnter = useCallback(() => {
    setIsHovered(true)
  }, [])

  const handleMouseLeave = useCallback(() => {
    setIsHovered(false)
    if (!cardRef.current) return
    cardRef.current.style.setProperty('--rotate-x', '0deg')
    cardRef.current.style.setProperty('--rotate-y', '0deg')
    cardRef.current.style.setProperty('--pointer-x', '50%')
    cardRef.current.style.setProperty('--pointer-y', '50%')
  }, [])

  const roleGlow = ROLE_GLOW_MAP[roleId] || 'rgba(52, 211, 153, 0.45)'
  const roleBorder = ROLE_BORDER_MAP[roleId] || '#34d399'

  const initials = name
    .split(' ')
    .map((w) => w[0])
    .filter(Boolean)
    .slice(0, 2)
    .join('')
    .toUpperCase()

  return (
    <div className="profile-card-wrapper">
      <div
        ref={cardRef}
        className="profile-card"
        style={
          {
            '--role-glow': roleGlow,
            borderColor: isHovered ? roleBorder : 'rgba(255, 255, 255, 0.12)',
          } as React.CSSProperties
        }
        onMouseMove={handleMouseMove}
        onMouseEnter={handleMouseEnter}
        onMouseLeave={handleMouseLeave}
      >
        <div className="profile-card-glare" />
        <div className="profile-card-content">
          <div className="profile-avatar-container">
            <div className="profile-avatar-inner">
              {avatarUrl ? (
                // eslint-disable-next-line @next/next/no-img-element
                <img
                  src={avatarUrl}
                  alt={name}
                  className="w-full h-full object-cover"
                />
              ) : (
                <span className="text-xl tracking-wider">{initials}</span>
              )}
            </div>
          </div>

          <div className="profile-role-badge">
            <span className="profile-live-dot" />
            <span>{status}</span>
          </div>

          <h3 className="profile-name">{name}</h3>
          <p className="profile-title">{title}</p>
          <span className="profile-handle">{handle}</span>

          {onContactClick && (
            <button
              type="button"
              className="profile-select-btn"
              onClick={(e) => {
                e.stopPropagation()
                onContactClick()
              }}
            >
              {contactText}
            </button>
          )}
        </div>
      </div>
    </div>
  )
}
