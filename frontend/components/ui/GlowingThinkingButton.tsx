'use client'

import React, { useEffect, useRef } from 'react'

export interface GlowingThinkingButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  label?: string
  loadingLabel?: string
  loading?: boolean
  disabled?: boolean
  className?: string
  style?: React.CSSProperties
  width?: number | string
  height?: number
}

export function GlowingThinkingButton({
  label = 'Ask Athena',
  loadingLabel = 'Thinking...',
  loading = false,
  disabled = false,
  className = '',
  style,
  width = 140,
  height = 38,
  onClick,
  ...props
}: GlowingThinkingButtonProps) {
  const canvasRef = useRef<HTMLCanvasElement | null>(null)
  const containerRef = useRef<HTMLButtonElement | null>(null)
  const animRef = useRef<number | null>(null)

  const activeText = loading ? loadingLabel : label

  useEffect(() => {
    const cv = canvasRef.current
    if (!cv) return
    const ctx = cv.getContext('2d')
    if (!ctx) return

    // Offscreen layers for the comet glow & core
    const gl = document.createElement('canvas')
    const gx = gl.getContext('2d')
    const co = document.createElement('canvas')
    const cox = co.getContext('2d')
    if (!gx || !cox) return

    /* Reference frame constants from verified authoring */
    const CX = 1002
    const CY = 1035.5
    const PW = 976
    const PH = 345
    const PR = 100
    const GAP = 50
    const TW = PW + 2 * GAP
    const TH = PH + 2 * GAP
    const TR = PR + GAP
    const TRACK_W = 13
    const CORE_W = 14
    const GLOW_W = 12

    const DUR = loading ? 1.6 : 2.7
    const TAIL = 0.389
    const SHIM_OFF = 0.898
    const FONT =
      '600 100px -apple-system, "Plus Jakarta Sans", "SF Pro Display", "Helvetica Neue", Inter, system-ui, sans-serif'

    let k = 1
    let dpr = 1
    const canFilter = (() => {
      try {
        const t = document.createElement('canvas').getContext('2d')
        if (t) {
          t.filter = 'blur(2px)'
          return t.filter !== 'none'
        }
      } catch {}
      return false
    })()

    /* Rounded rect path */
    function rrPath(
      c: CanvasRenderingContext2D,
      cx: number,
      cy: number,
      w: number,
      h: number,
      r: number
    ) {
      const x = cx - w / 2
      const y = cy - h / 2
      c.beginPath()
      c.moveTo(x + r, y)
      c.lineTo(x + w - r, y)
      c.arcTo(x + w, y, x + w, y + r, r)
      c.lineTo(x + w, y + h - r)
      c.arcTo(x + w, y + h, x + w - r, y + h, r)
      c.lineTo(x + r, y + h)
      c.arcTo(x, y + h, x, y + h - r, r)
      c.lineTo(x, y + r)
      c.arcTo(x, y, x + r, y, r)
      c.closePath()
    }

    const SW = TW - 2 * TR
    const SH = TH - 2 * TR
    const ARC = (Math.PI * TR) / 2
    const PERIM = 2 * SW + 2 * SH + 4 * ARC
    const L = CX - TW / 2
    const T = CY - TH / 2
    const R = CX + TW / 2
    const B = CY + TH / 2

    function ptAt(s: number): [number, number] {
      s = s - Math.floor(s / PERIM) * PERIM
      let a: number
      if (s < SW) return [L + TR + s, T]
      s -= SW
      if (s < ARC) {
        a = s / TR
        return [R - TR + TR * Math.sin(a), T + TR - TR * Math.cos(a)]
      }
      s -= ARC
      if (s < SH) return [R, T + TR + s]
      s -= SH
      if (s < ARC) {
        a = s / TR
        return [R - TR + TR * Math.cos(a), B - TR + TR * Math.sin(a)]
      }
      s -= ARC
      if (s < SW) return [R - TR - s, B]
      s -= SW
      if (s < ARC) {
        a = s / TR
        return [L + TR - TR * Math.sin(a), B - TR + TR * Math.cos(a)]
      }
      s -= ARC
      if (s < SH) return [L, B - TR - s]
      s -= SH
      a = s / TR
      return [L + TR - TR * Math.cos(a), T + TR - TR * Math.sin(a)]
    }

    const TAPER = [
      1.16, 1.09, 1.03, 1.0, 1.02, 1.0, 1.0, 1.0, 1.0, 0.98, 0.97, 0.94, 0.91,
      0.89, 0.84, 0.77, 0.74, 0.65, 0.61, 0.52, 0.43, 0.4, 0.27, 0.23, 0.17,
      0.12, 0.075, 0.02, 0,
    ]
    const TSTEP = TAIL / (TAPER.length - 1)
    function taper(u: number): number {
      if (u < 0 || u >= TAIL) return 0
      const f = u / TSTEP
      const i = Math.floor(f)
      return TAPER[i] + (TAPER[i + 1] - TAPER[i]) * (f - i)
    }

    function paintComet(
      c: CanvasRenderingContext2D,
      head: number,
      col: number[],
      hot: number[],
      width: number
    ) {
      c.setTransform(1, 0, 0, 1, 0, 0)
      c.clearRect(0, 0, c.canvas.width, c.canvas.height)

      const tx = cv!.width / 2 - CX * k
      const ty = cv!.height / 2 - CY * k
      c.setTransform(1, 0, 0, 1, tx, ty)

      c.lineCap = 'round'
      c.lineWidth = width * k
      const step = 6
      const n = Math.ceil((TAIL * PERIM) / step)
      for (let i = n; i >= 1; i--) {
        const s1 = head - i * step
        const s0 = head - (i - 1) * step
        const a = taper((i * step) / PERIM)
        if (a <= 0.002) continue
        const f = Math.min(a, 1.3)
        const x = Math.max(0, f - 1)
        const r = Math.round(Math.min(255, col[0] * f + hot[0] * x))
        const g = Math.round(Math.min(255, col[1] * f + hot[1] * x))
        const b = Math.round(Math.min(255, col[2] * f + hot[2] * x))
        const p1 = ptAt(s1)
        const mid = ptAt((s1 + s0) / 2)
        const p0 = ptAt(s0)
        c.strokeStyle = `rgb(${r},${g},${b})`
        c.beginPath()
        c.moveTo(p1[0] * k, p1[1] * k)
        c.lineTo(mid[0] * k, mid[1] * k)
        c.lineTo(p0[0] * k, p0[1] * k)
        c.stroke()
      }
    }

    function plate(c: CanvasRenderingContext2D) {
      const x = CX - PW / 2
      const y = CY - PH / 2
      const grd = c.createLinearGradient(0, y * k, 0, (y + PH) * k)
      grd.addColorStop(0, '#1a2236')
      grd.addColorStop(0.55, '#131b2e')
      grd.addColorStop(1, '#0e1524')
      rrPath(c, CX * k, CY * k, PW * k, PH * k, PR * k)
      c.fillStyle = grd
      c.fill()

      c.lineWidth = 4 * k
      const hg = c.createLinearGradient(0, y * k, 0, (y + PH) * k)
      hg.addColorStop(0, 'rgba(226,233,255,0.25)')
      hg.addColorStop(0.12, 'rgba(226,233,255,0.05)')
      hg.addColorStop(0.88, 'rgba(80,100,255,0.05)')
      hg.addColorStop(1, 'rgba(99,102,241,0.35)')
      rrPath(c, CX * k, CY * k, (PW - 12) * k, (PH - 12) * k, (PR - 6) * k)
      c.strokeStyle = hg
      c.stroke()
    }

    function label(c: CanvasRenderingContext2D, ph: number) {
      const q = (ph - SHIM_OFF + 10) % 1
      const u = q < 0.5 ? q / 0.5 : (1 - q) / 0.5
      const fontPx = Math.round(135 * k)
      c.font = FONT.replace('100px', `${fontPx}px`)

      const textMetrics = c.measureText(activeText)
      const txtW = textMetrics.width || 400 * k

      const bc = CX * k - txtW / 2 + txtW * (-0.2 + 1.4 * u)
      const bw = txtW * 0.35
      const g = c.createLinearGradient(bc - bw, 0, bc + bw, 0)
      g.addColorStop(0, 'rgb(180,195,230)')
      g.addColorStop(0.3, 'rgb(215,225,255)')
      g.addColorStop(0.5, 'rgb(255,255,255)')
      g.addColorStop(0.7, 'rgb(215,225,255)')
      g.addColorStop(1, 'rgb(180,195,230)')
      c.fillStyle = g
      c.textBaseline = 'middle'
      c.textAlign = 'center'
      c.fillText(activeText, CX * k, CY * k)
    }

    function render(t: number) {
      if (!ctx || !cv) return
      let ph = (t / DUR) % 1
      if (ph < 0) ph += 1
      const head = ph * PERIM

      ctx.setTransform(1, 0, 0, 1, 0, 0)
      ctx.globalCompositeOperation = 'source-over'
      ctx.globalAlpha = 1
      ctx.filter = 'none'
      ctx.clearRect(0, 0, cv.width, cv.height)

      const tx = cv.width / 2 - CX * k
      const ty = cv.height / 2 - CY * k

      /* Faint track */
      ctx.setTransform(1, 0, 0, 1, tx, ty)
      rrPath(ctx, CX * k, CY * k, TW * k, TH * k, TR * k)
      ctx.lineWidth = TRACK_W * k
      ctx.strokeStyle = 'rgba(99,102,241,0.18)'
      ctx.stroke()

      /* Travelling comet glow & core */
      paintComet(gx!, head, [99, 102, 241], [130, 180, 255], GLOW_W)
      paintComet(cox!, head, [140, 180, 255], [230, 245, 255], CORE_W)

      ctx.setTransform(1, 0, 0, 1, 0, 0)
      ctx.globalCompositeOperation = 'lighter'
      if (canFilter) {
        ctx.filter = `blur(${Math.max(2, 20 * k)}px)`
        ctx.globalAlpha = 0.8
        ctx.drawImage(gl, 0, 0)
        ctx.filter = `blur(${Math.max(1, 7 * k)}px)`
        ctx.globalAlpha = 0.6
        ctx.drawImage(gl, 0, 0)
        ctx.filter = `blur(${Math.max(0.5, 1.5 * k)}px)`
        ctx.globalAlpha = 1
        ctx.drawImage(co, 0, 0)
        ctx.filter = 'none'
      } else {
        ctx.shadowColor = 'rgba(99,102,241,0.9)'
        ctx.shadowBlur = 18 * k
        ctx.globalAlpha = 0.8
        ctx.drawImage(gl, 0, 0)
        ctx.shadowBlur = 6 * k
        ctx.globalAlpha = 0.9
        ctx.drawImage(gl, 0, 0)
        ctx.shadowBlur = 0
        ctx.globalAlpha = 1
        ctx.drawImage(co, 0, 0)
      }
      ctx.globalAlpha = 1
      ctx.globalCompositeOperation = 'source-over'

      ctx.setTransform(1, 0, 0, 1, tx, ty)
      plate(ctx)
      label(ctx, ph)
    }

    function resize() {
      if (!cv || !containerRef.current) return
      const rect = containerRef.current.getBoundingClientRect()
      dpr = Math.min(window.devicePixelRatio || 1, 2.5)
      const clientW = rect.width || 140
      const clientH = rect.height || 38
      cv.width = gl.width = co.width = Math.round(clientW * dpr)
      cv.height = gl.height = co.height = Math.round(clientH * dpr)
      k = Math.min((cv.width * 0.92) / TW, (cv.height * 0.88) / TH)
    }

    resize()

    let now = 0
    let last: number | null = null

    function frame(ts: number) {
      if (last != null) now = (now + (ts - last) / 1000) % DUR
      last = ts
      render(now)
      animRef.current = requestAnimationFrame(frame)
    }

    animRef.current = requestAnimationFrame(frame)

    const ro =
      typeof ResizeObserver !== 'undefined'
        ? new ResizeObserver(() => {
            resize()
          })
        : null

    if (ro && containerRef.current) {
      ro.observe(containerRef.current)
    }

    return () => {
      if (animRef.current) cancelAnimationFrame(animRef.current)
      if (ro) ro.disconnect()
    }
  }, [activeText, loading])

  return (
    <button
      ref={containerRef}
      type="button"
      disabled={disabled}
      onClick={onClick}
      className={`relative inline-flex items-center justify-center shrink-0 overflow-hidden rounded-[8px] cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed transition-transform active:scale-95 ${className}`}
      style={{
        width: typeof width === 'number' ? `${width}px` : width,
        height: `${height}px`,
        background: 'transparent',
        border: 'none',
        padding: 0,
        ...style,
      }}
      {...props}
    >
      <canvas
        ref={canvasRef}
        className="w-full h-full block pointer-events-none"
        style={{ width: '100%', height: '100%' }}
      />
    </button>
  )
}
