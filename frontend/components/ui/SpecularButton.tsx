'use client'

import React, { useEffect, useRef, useState, useCallback } from 'react'

export interface SpecularButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  size?: 'xs' | 'sm' | 'default' | 'lg' | 'icon'
  radius?: number
  tint?: string
  tintOpacity?: number
  blur?: number
  textColor?: string
  lineColor?: string
  baseColor?: string
  intensity?: number
  shineSize?: number
  shineFade?: number
  thickness?: number
  speed?: number
  followMouse?: boolean
  proximity?: number
  autoAnimate?: boolean
  loading?: boolean
  children?: React.ReactNode
  className?: string
  style?: React.CSSProperties
}

export function SpecularButton({
  size = 'default',
  radius = 12,
  tint,
  tintOpacity = 0.15,
  blur = 0,
  textColor,
  lineColor,
  baseColor,
  intensity = 1,
  shineSize = 12,
  shineFade = 40,
  thickness = 1,
  speed = 0.35,
  followMouse = true,
  proximity = 250,
  autoAnimate = false,
  loading = false,
  disabled = false,
  children,
  className = '',
  style,
  onClick,
  onMouseEnter,
  onMouseLeave,
  ...props
}: SpecularButtonProps) {
  const buttonRef = useRef<HTMLButtonElement | null>(null)
  const [mousePos, setMousePos] = useState<{ x: number; y: number; active: boolean; opacity: number }>({
    x: 50,
    y: 50,
    active: false,
    opacity: 0,
  })
  const [animAngle, setAnimAngle] = useState(0)

  // Auto animation loop if enabled or loading
  useEffect(() => {
    if (!autoAnimate && !loading) return

    let animId: number
    let start = performance.now()

    const loop = (now: number) => {
      const elapsed = (now - start) * 0.001
      setAnimAngle((elapsed * (speed * 360)) % 360)
      animId = requestAnimationFrame(loop)
    }

    animId = requestAnimationFrame(loop)
    return () => cancelAnimationFrame(animId)
  }, [autoAnimate, loading, speed])

  // Mouse move listener with proximity detection
  useEffect(() => {
    if (!followMouse) return

    const handleMouseMove = (e: MouseEvent) => {
      if (!buttonRef.current) return
      const rect = buttonRef.current.getBoundingClientRect()
      const centerX = rect.left + rect.width / 2
      const centerY = rect.top + rect.height / 2
      const dist = Math.hypot(e.clientX - centerX, e.clientY - centerY)

      if (dist < proximity) {
        const x = ((e.clientX - rect.left) / rect.width) * 100
        const y = ((e.clientY - rect.top) / rect.height) * 100
        const opacity = Math.max(0, Math.min(1, 1 - dist / proximity)) * intensity
        setMousePos({ x, y, active: true, opacity })
      } else if (mousePos.active) {
        setMousePos((prev) => ({ ...prev, active: false, opacity: 0 }))
      }
    }

    window.addEventListener('mousemove', handleMouseMove, { passive: true })
    return () => window.removeEventListener('mousemove', handleMouseMove)
  }, [followMouse, proximity, intensity, mousePos.active])

  // Size preset mappings
  const sizeStyles: Record<string, { height: string; padding: string; fontSize: string }> = {
    xs: { height: '1.5rem', padding: '0 0.5rem', fontSize: '0.7rem' },
    sm: { height: '1.75rem', padding: '0 0.65rem', fontSize: '0.75rem' },
    default: { height: '2rem', padding: '0 0.875rem', fontSize: '0.75rem' },
    lg: { height: '2.5rem', padding: '0 1.25rem', fontSize: '0.875rem' },
    icon: { height: '2rem', padding: '0', fontSize: '0.75rem' },
  }

  const currentSize = sizeStyles[size] || sizeStyles.default

  // Dynamic specular gradient calculation
  const specularX = mousePos.active ? mousePos.x : 50 + Math.cos((animAngle * Math.PI) / 180) * 40
  const specularY = mousePos.active ? mousePos.y : 50 + Math.sin((animAngle * Math.PI) / 180) * 40
  const specularOpacity = mousePos.active ? mousePos.opacity : autoAnimate || loading ? 0.85 * intensity : 0

  return (
    <button
      ref={buttonRef}
      disabled={disabled || loading}
      className={`group/specular relative inline-flex items-center justify-center font-medium select-none overflow-hidden transition-all duration-200 active:scale-[0.98] disabled:opacity-60 disabled:pointer-events-none disabled:active:scale-100 ${className}`}
      style={{
        borderRadius: `${radius}px`,
        height: currentSize.height,
        padding: currentSize.padding,
        fontSize: currentSize.fontSize,
        color: textColor || 'var(--foreground)',
        background: baseColor || 'var(--surface)',
        border: `${thickness}px solid ${lineColor || 'var(--border)'}`,
        boxShadow: `0 1px 3px rgba(0,0,0,0.12), 0 1px 2px rgba(0,0,0,0.08), inset 0 1px 0.5px rgba(255,255,255,0.15)`,
        ...style,
      }}
      onClick={onClick}
      onMouseEnter={onMouseEnter}
      onMouseLeave={onMouseLeave}
      {...props}
    >
      {/* 1. Base tint overlay */}
      {tint && (
        <div
          className="absolute inset-0 pointer-events-none transition-opacity duration-300"
          style={{
            background: tint,
            opacity: tintOpacity,
            borderRadius: `${radius}px`,
          }}
        />
      )}

      {/* 2. Specular border glow reflection */}
      <div
        className="absolute -inset-[1px] pointer-events-none transition-opacity duration-150"
        style={{
          borderRadius: `${radius}px`,
          background: `radial-gradient(${shineSize * 4}px circle at ${specularX}% ${specularY}%, ${lineColor || 'var(--primary)'} 0%, transparent ${shineFade * 2}%)`,
          opacity: specularOpacity,
          mixBlendMode: 'screen',
        }}
      />

      {/* 3. Surface specular sheen highlight */}
      <div
        className="absolute inset-0 pointer-events-none transition-opacity duration-150"
        style={{
          borderRadius: `${radius}px`,
          background: `radial-gradient(${shineSize * 8}px circle at ${specularX}% ${specularY}%, rgba(255, 255, 255, ${0.35 * intensity}) 0%, transparent ${shineFade * 2.5}%)`,
          opacity: specularOpacity,
          filter: blur > 0 ? `blur(${blur}px)` : undefined,
        }}
      />

      {/* 4. Top subtle bevel lighting */}
      <div
        className="absolute inset-x-0 top-0 h-[1px] pointer-events-none"
        style={{
          background: `linear-gradient(90deg, transparent 0%, rgba(255, 255, 255, 0.25) 50%, transparent 100%)`,
        }}
      />

      {/* 5. Interactive Content */}
      <span className="relative z-10 inline-flex items-center gap-1.5 leading-none">
        {children}
      </span>
    </button>
  )
}

export default SpecularButton
