/**
 * Induction Button Canvas 2D Renderer
 * Authored Counter-Rotating Electromagnetic Flux Rings & Ionization Arcs.
 */

import { RendererHandle } from './star-portal'

export function initInductionRenderer(
  canvas: HTMLCanvasElement,
  options?: { mode?: 'dark' | 'light' }
): RendererHandle | null {
  const ctx = canvas.getContext('2d')
  if (!ctx) return null

  let animId: number | null = null
  let start = performance.now()
  let isHovered = false
  let warpFactor = 0

  const resize = () => {
    const dpr = Math.min(window.devicePixelRatio || 1, 2)
    const rect = canvas.getBoundingClientRect()
    canvas.width = Math.max(Math.floor(rect.width * dpr), 32)
    canvas.height = Math.max(Math.floor(rect.height * dpr), 32)
  }
  resize()

  const render = (now: number) => {
    const elapsed = (now - start) * 0.001
    const w = canvas.width
    const h = canvas.height

    if (w === 0 || h === 0) {
      animId = requestAnimationFrame(render)
      return
    }

    // Base field
    ctx.fillStyle = '#070b14'
    ctx.fillRect(0, 0, w, h)

    const cx = w * 0.5
    const cy = h * 0.5
    const maxR = Math.max(w, h) * 0.7

    // Induction flux rings
    const ringCount = 5
    for (let i = 0; i < ringCount; i++) {
      const dir = i % 2 === 0 ? 1 : -1
      const speed = (0.5 + i * 0.2 + (isHovered ? 1.0 : 0) + warpFactor * 1.5) * dir
      const angle = elapsed * speed + (i * Math.PI) / ringCount
      const r = (maxR * (i + 1)) / (ringCount + 1)

      ctx.save()
      ctx.translate(cx, cy)
      ctx.rotate(angle)

      const grad = ctx.createLinearGradient(-r, 0, r, 0)
      grad.addColorStop(0, 'rgba(99, 102, 241, 0.05)')
      grad.addColorStop(0.5, 'rgba(6, 182, 212, 0.6)')
      grad.addColorStop(1, 'rgba(99, 102, 241, 0.05)')

      ctx.strokeStyle = grad
      ctx.lineWidth = 1.5
      ctx.beginPath()
      ctx.ellipse(0, 0, r, r * 0.35, 0, 0, Math.PI * 2)
      ctx.stroke()
      ctx.restore()
    }

    // Center focal glow
    const centerGrad = ctx.createRadialGradient(cx, cy, 0, cx, cy, Math.min(w, h) * 0.5)
    centerGrad.addColorStop(0, 'rgba(6, 182, 212, 0.4)')
    centerGrad.addColorStop(0.5, 'rgba(99, 102, 241, 0.2)')
    centerGrad.addColorStop(1, 'rgba(0, 0, 0, 0)')
    ctx.fillStyle = centerGrad
    ctx.fillRect(0, 0, w, h)

    animId = requestAnimationFrame(render)
  }
  animId = requestAnimationFrame(render)

  return {
    destroy: () => {
      if (animId !== null) cancelAnimationFrame(animId)
    },
    setPointer: (x, y, h) => { isHovered = h },
    setWarp: (w) => { warpFactor = w },
    resize,
  }
}
