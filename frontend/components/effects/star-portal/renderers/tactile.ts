/**
 * Tactile Button Canvas 2D Renderer
 * Authored Neuform Isometric Grid Mesh with Elastic Cursor Physics.
 */

import { RendererHandle } from './star-portal'

export function initTactileRenderer(
  canvas: HTMLCanvasElement,
  options?: { mode?: 'dark' | 'light' }
): RendererHandle | null {
  const ctx = canvas.getContext('2d')
  if (!ctx) return null

  let animId: number | null = null
  let start = performance.now()
  let pointerX = 0
  let pointerY = 0
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

    ctx.fillStyle = '#080d1a'
    ctx.fillRect(0, 0, w, h)

    const gridSize = 14 * (window.devicePixelRatio || 1)
    const cols = Math.ceil(w / gridSize) + 1
    const rows = Math.ceil(h / gridSize) + 1

    ctx.strokeStyle = 'rgba(255, 255, 255, 0.08)'
    ctx.lineWidth = 1

    for (let r = 0; r <= rows; r++) {
      for (let c = 0; c <= cols; c++) {
        let x = c * gridSize
        let y = r * gridSize

        if (isHovered) {
          const dx = pointerX * (window.devicePixelRatio || 1) - x
          const dy = pointerY * (window.devicePixelRatio || 1) - y
          const dist = Math.sqrt(dx * dx + dy * dy)
          if (dist < 80) {
            const force = (1 - dist / 80) * 8
            x -= (dx / (dist + 0.1)) * force
            y -= (dy / (dist + 0.1)) * force
          }
        }

        // Animated wave ripple
        const wave = Math.sin(elapsed * 2 + (c + r) * 0.4) * 2
        y += wave

        ctx.fillStyle = isHovered ? 'rgba(99, 102, 241, 0.4)' : 'rgba(255, 255, 255, 0.12)'
        ctx.beginPath()
        ctx.arc(x, y, 1.2, 0, Math.PI * 2)
        ctx.fill()
      }
    }

    animId = requestAnimationFrame(render)
  }
  animId = requestAnimationFrame(render)

  return {
    destroy: () => {
      if (animId !== null) cancelAnimationFrame(animId)
    },
    setPointer: (x, y, h) => {
      pointerX = x
      pointerY = y
      isHovered = h
    },
    setWarp: (w) => { warpFactor = w },
    resize,
  }
}
