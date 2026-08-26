'use client'

import React, { useEffect, useRef, useState } from 'react'
import { initStarPortalRenderer, RendererHandle } from './renderers/star-portal'
import { initIgnitionRenderer } from './renderers/ignition'
import { initPlasmaRenderer } from './renderers/plasma'
import { initInductionRenderer } from './renderers/induction'
import { initTactileRenderer } from './renderers/tactile'
import { initThinkingRenderer } from './renderers/thinking'
import './styles.css'

export type ShaderButtonVariant =
  | 'star-portal'
  | 'ignition-button'
  | 'induction-button'
  | 'plasma-button'
  | 'tactile-button'
  | 'thinking-button'

export interface ShaderButtonsProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ShaderButtonVariant
  mode?: 'dark' | 'light' | 'auto'
  palette?: string
  loading?: boolean
  warp?: number
  children?: React.ReactNode
}

export function ShaderButtons({
  variant = 'star-portal',
  mode = 'dark',
  palette,
  loading = false,
  warp = 0,
  disabled = false,
  className = '',
  style,
  children,
  onClick,
  onMouseEnter,
  onMouseLeave,
  onMouseMove,
  ...props
}: ShaderButtonsProps) {
  const canvasRef = useRef<HTMLCanvasElement | null>(null)
  const rendererRef = useRef<RendererHandle | null>(null)
  const buttonRef = useRef<HTMLButtonElement | null>(null)
  const [activeVariant, setActiveVariant] = useState<ShaderButtonVariant>(variant)

  // Switch to thinking state when loading
  useEffect(() => {
    if (loading) {
      setActiveVariant('thinking-button')
    } else {
      setActiveVariant(variant)
    }
  }, [loading, variant])

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return

    // Cleanup previous renderer
    if (rendererRef.current) {
      rendererRef.current.destroy()
      rendererRef.current = null
    }

    let handle: RendererHandle | null = null

    try {
      switch (activeVariant) {
        case 'star-portal':
          handle = initStarPortalRenderer(canvas, { mode: mode === 'auto' ? 'dark' : mode })
          break
        case 'ignition-button':
          handle = initIgnitionRenderer(canvas, { mode: mode === 'auto' ? 'dark' : mode })
          break
        case 'plasma-button':
          handle = initPlasmaRenderer(canvas, { mode: mode === 'auto' ? 'dark' : mode })
          break
        case 'induction-button':
          handle = initInductionRenderer(canvas, { mode: mode === 'auto' ? 'dark' : mode })
          break
        case 'tactile-button':
          handle = initTactileRenderer(canvas, { mode: mode === 'auto' ? 'dark' : mode })
          break
        case 'thinking-button':
          handle = initThinkingRenderer(canvas, { mode: mode === 'auto' ? 'dark' : mode })
          break
        default:
          handle = initStarPortalRenderer(canvas, { mode: mode === 'auto' ? 'dark' : mode })
      }
    } catch (e) {
      console.warn('[ShaderButtons] Renderer initialization failed:', e)
    }

    rendererRef.current = handle

    // Set initial warp if active
    if (handle) {
      handle.setWarp(loading ? 1.5 : warp)
    }

    // Resize observer
    let ro: ResizeObserver | null = null
    if (typeof ResizeObserver !== 'undefined' && buttonRef.current) {
      ro = new ResizeObserver(() => {
        if (rendererRef.current) {
          rendererRef.current.resize()
        }
      })
      ro.observe(buttonRef.current)
    }

    return () => {
      if (ro) ro.disconnect()
      if (rendererRef.current) {
        rendererRef.current.destroy()
        rendererRef.current = null
      }
    }
  }, [activeVariant, mode, loading, warp])

  const handlePointerMove = (e: React.MouseEvent<HTMLButtonElement>) => {
    if (rendererRef.current && buttonRef.current) {
      const rect = buttonRef.current.getBoundingClientRect()
      const x = e.clientX - rect.left
      const y = e.clientY - rect.top
      rendererRef.current.setPointer(x, y, true)
    }
    if (onMouseMove) onMouseMove(e)
  }

  const handlePointerEnter = (e: React.MouseEvent<HTMLButtonElement>) => {
    if (rendererRef.current) {
      rendererRef.current.setWarp(loading ? 2.0 : 1.0)
    }
    if (onMouseEnter) onMouseEnter(e)
  }

  const handlePointerLeave = (e: React.MouseEvent<HTMLButtonElement>) => {
    if (rendererRef.current && buttonRef.current) {
      const rect = buttonRef.current.getBoundingClientRect()
      rendererRef.current.setPointer(rect.width * 0.5, rect.height * 0.5, false)
      rendererRef.current.setWarp(loading ? 1.2 : 0.0)
    }
    if (onMouseLeave) onMouseLeave(e)
  }

  return (
    <button
      ref={buttonRef}
      disabled={disabled}
      data-mode={mode}
      data-loading={loading ? 'true' : 'false'}
      data-variant={activeVariant}
      className={`shader-button-host ${className}`}
      style={style}
      onClick={onClick}
      onMouseMove={handlePointerMove}
      onMouseEnter={handlePointerEnter}
      onMouseLeave={handlePointerLeave}
      {...props}
    >
      <canvas ref={canvasRef} className="shader-button-canvas" />
      <div className="shader-button-overlay" />
      <div className="shader-button-content">{children}</div>
    </button>
  )
}
