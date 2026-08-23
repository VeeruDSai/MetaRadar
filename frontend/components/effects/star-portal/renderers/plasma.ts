/**
 * Plasma Button WebGL Renderer
 * Authored Chromatic Interference Wave Surface.
 */

import { RendererHandle } from './star-portal'

const VERT_SRC = `
attribute vec2 a_position;
varying vec2 v_uv;
void main() {
  v_uv = a_position * 0.5 + 0.5;
  gl_Position = vec4(a_position, 0.0, 1.0);
}
`

const FRAG_SRC = `
precision mediump float;
uniform vec2 u_resolution;
uniform float u_time;
uniform vec2 u_pointer;
uniform float u_hover;
uniform float u_warp;
varying vec2 v_uv;

void main() {
  vec2 uv = (gl_FragCoord.xy - 0.5 * u_resolution.xy) / min(u_resolution.x, u_resolution.y);
  float t = u_time * (0.6 + u_hover * 0.9 + u_warp * 1.5);
  
  float v1 = sin(uv.x * 6.0 + t);
  float v2 = sin(uv.y * 6.0 + t * 1.2);
  float v3 = sin((uv.x + uv.y) * 5.0 + t * 0.8);
  float cx = uv.x + 0.5 * sin(t / 2.0);
  float cy = uv.y + 0.5 * cos(t / 3.0);
  float v4 = sin(sqrt(100.0 * (cx*cx + cy*cy) + 1.0) + 1.5 * t);
  
  float v = (v1 + v2 + v3 + v4) * 0.25;
  
  // Chromatic spectrum: electric violet -> cyan -> neon rose
  vec3 col = vec3(
    sin(v * 3.1415 + 0.0) * 0.5 + 0.5,
    sin(v * 3.1415 + 2.0) * 0.5 + 0.5,
    sin(v * 3.1415 + 4.0) * 0.5 + 0.5
  );
  
  col = mix(vec3(0.04, 0.06, 0.14), col, 0.65 + u_hover * 0.35);
  col += vec3(0.2, 0.5, 1.0) * (0.2 + u_warp * 0.5);
  
  gl_FragColor = vec4(col, 1.0);
}
`

export function initPlasmaRenderer(
  canvas: HTMLCanvasElement,
  options?: { mode?: 'dark' | 'light' }
): RendererHandle | null {
  const gl = canvas.getContext('webgl', { alpha: false, antialias: true })
  if (!gl) return null

  const vs = gl.createShader(gl.VERTEX_SHADER)!
  gl.shaderSource(vs, VERT_SRC)
  gl.compileShader(vs)

  const fs = gl.createShader(gl.FRAGMENT_SHADER)!
  gl.shaderSource(fs, FRAG_SRC)
  gl.compileShader(fs)

  const prog = gl.createProgram()!
  gl.attachShader(prog, vs)
  gl.attachShader(prog, fs)
  gl.linkProgram(prog)
  gl.useProgram(prog)

  const posBuf = gl.createBuffer()
  gl.bindBuffer(gl.ARRAY_BUFFER, posBuf)
  gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1, -1, 1, -1, -1, 1, -1, 1, 1, -1, 1, 1]), gl.STATIC_DRAW)

  const aPos = gl.getAttribLocation(prog, 'a_position')
  gl.enableVertexAttribArray(aPos)
  gl.vertexAttribPointer(aPos, 2, gl.FLOAT, false, 0, 0)

  const uRes = gl.getUniformLocation(prog, 'u_resolution')
  const uTime = gl.getUniformLocation(prog, 'u_time')
  const uHover = gl.getUniformLocation(prog, 'u_hover')
  const uWarp = gl.getUniformLocation(prog, 'u_warp')

  let animId: number | null = null
  let start = performance.now()
  let hover = 0
  let isHovered = false
  let warp = 0

  const resize = () => {
    const dpr = Math.min(window.devicePixelRatio || 1, 2)
    const rect = canvas.getBoundingClientRect()
    canvas.width = Math.max(Math.floor(rect.width * dpr), 32)
    canvas.height = Math.max(Math.floor(rect.height * dpr), 32)
    gl.viewport(0, 0, canvas.width, canvas.height)
  }
  resize()

  const render = (now: number) => {
    hover += ((isHovered ? 1 : 0) - hover) * 0.1
    gl.useProgram(prog)
    gl.uniform2f(uRes, canvas.width, canvas.height)
    gl.uniform1f(uTime, (now - start) * 0.001)
    gl.uniform1f(uHover, hover)
    gl.uniform1f(uWarp, warp)
    gl.drawArrays(gl.TRIANGLES, 0, 6)
    animId = requestAnimationFrame(render)
  }
  animId = requestAnimationFrame(render)

  return {
    destroy: () => {
      if (animId !== null) cancelAnimationFrame(animId)
      gl.deleteBuffer(posBuf)
      gl.deleteShader(vs)
      gl.deleteShader(fs)
      gl.deleteProgram(prog)
    },
    setPointer: (x, y, h) => { isHovered = h },
    setWarp: (w) => { warp = w },
    resize,
  }
}
