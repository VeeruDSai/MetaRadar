/**
 * Thinking Button Canvas 2D / Neural Pulse Renderer
 * Authored Synaptic Neural Grid & High-Energy Data Ingestion Scan Wave.
 */

import { RendererHandle } from './star-portal'

interface PulseNode {
  x: number
  y: number
  vx: number
  vy: number
  radius: number
  phase: number
}

export function initThinkingRenderer(
  canvas: HTMLCanvasElement,
  options?: { mode?: 'dark' | 'light' }
): RendererHandle | null {
  const ctx = canvas.getContext('2d')
  if (!ctx) return null

  let animId: number | null = null
  let startTime = performance.now()
  let isHovered = false
  let warpFactor = 1.0
  let nodes: PulseNode[] = []

  const initNodes = (w: number, h: number) => {
    nodes = []
    const count = Math.max(12, Math.floor((w * h) / 1200))
    for (let i = 0; i < count; i++) {
      nodes.push({
        x: Math.random() * w,
        y: Math.random() * h,
        vx: (Math.random() - 0.5) * 0.8,
        vy: (Math.random() - 0.5) * 0.8,
        radius: Math.random() * 2 + 1.5,
        phase: Math.random() * Math.PI * 2,
      })
    }
  }

  const resize = () => {
    const dpr = Math.min(window.devicePixelRatio || 1, 2)
    const rect = canvas.getBoundingClientRect()
    const w = Math.max(Math.floor(rect.width * dpr), 32)
    const h = Math.max(Math.floor(rect.height * dpr), 32)

    if (canvas.width !== w || canvas.height !== h) {
      canvas.width = w
      canvas.height = h
      initNodes(w, h)
    }
  }

  resize()

  const render = (now: number) => {
    const elapsed = (now - startTime) * 0.001
    const w = canvas.width
    const h = canvas.height

    if (w === 0 || h === 0) {
      animId = requestAnimationFrame(render)
      return
    }

    // Base background gradient
    const bgGrad = ctx.createLinearGradient(0, 0, w, h)
    bgGrad.addColorStop(0, '#060d1f')
    bgGrad.addColorStop(0.5, '#0c1630')
    bgGrad.addColorStop(1, '#050a18')
    ctx.fillStyle = bgGrad
    ctx.fillRect(0, 0, w, h)

    // Scanning wave sweep
    const scanPos = ((elapsed * 0.6 * warpFactor) % 1.4) - 0.2
    const scanGrad = ctx.createLinearGradient(
      (scanPos - 0.15) * w,
      0,
      (scanPos + 0.15) * w,
      0
    )
    scanGrad.addColorStop(0, 'rgba(6, 182, 212, 0)')
    scanGrad.addColorStop(0.5, 'rgba(99, 102, 241, 0.45)')
    scanGrad.addColorStop(1, 'rgba(6, 182, 212, 0)')
    ctx.fillStyle = scanGrad
    ctx.fillRect(0, 0, w, h)

    // Neural connections
    ctx.lineWidth = 1
    for (let i = 0; i < nodes.length; i++) {
      const a = nodes[i]
      a.x += a.vx * (isHovered ? 1.8 : 1.0) * warpFactor
      a.y += a.vy * (isHovered ? 1.8 : 1.0) * warpFactor

      if (a.x < 0 || a.x > w) a.vx *= -1
      if (a.y < 0 || a.y > h) a.vy *= -1

      for (let j = i + 1; j < nodes.length; j++) {
        const b = nodes[j]
        const dx = a.x - b.x
        const dy = a.y - b.y
        const dist = Math.sqrt(dx * dx + dy * dy)
        const maxDist = Math.min(w, h) * 0.45

        if (dist < maxDist) {
          const alpha = (1 - dist / maxDist) * 0.35 * (0.8 + Math.sin(elapsed * 4 + a.phase) * 0.2)
          ctx.strokeStyle = `rgba(99, 102, 241, ${alpha})`
          ctx.beginPath()
          ctx.moveTo(a.x, a.y)
          ctx.lineTo(b.x, b.y)
          ctx.stroke()
        }
      }

      // Draw node glow
      const pulse = Math.sin(elapsed * 5 + a.phase) * 0.5 + 0.5
      ctx.fillStyle = pulse > 0.6 ? 'rgba(6, 182, 212, 0.9)' : 'rgba(129, 140, 248, 0.7)'
      ctx.beginPath()
      ctx.arc(a.x, a.y, a.radius * (1 + pulse * 0.4), 0, Math.PI * 2)
      ctx.fill()
    }

    // Outer border radiant aura
    const edgeGrad = ctx.createLinearGradient(0, 0, w, 0)
    edgeGrad.addColorStop(0, 'rgba(99, 102, 241, 0.6)')
    edgeGrad.addColorStop(0.5, 'rgba(6, 182, 212, 0.8)')
    edgeGrad.addColorStop(1, 'rgba(99, 102, 241, 0.6)')
    ctx.strokeStyle = edgeGrad
    ctx.lineWidth = 2
    ctx.strokeRect(1, 1, w - 2, h - 2)

    animId = requestAnimationFrame(render)
  }

  animId = requestAnimationFrame(render)

  return {
    destroy: () => {
      if (animId !== null) cancelAnimationFrame(animId)
    },
    setPointer: (x, y, h) => {
      isHovered = h
    },
    setWarp: (w) => {
      warpFactor = Math.max(w, 1.0)
    },
    resize,
  }
}
