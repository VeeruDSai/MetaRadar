/**
 * Ignition Button WebGL Renderer
 * Authored Kinetic Fiery Plasma Surface with Pointer Heat Distortion.
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

float hash(vec2 p) {
  return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453);
}

float noise(vec2 p) {
  vec2 i = floor(p);
  vec2 f = fract(p);
  f = f * f * (3.0 - 2.0 * f);
  return mix(
    mix(hash(i + vec2(0.0, 0.0)), hash(i + vec2(1.0, 0.0)), f.x),
    mix(hash(i + vec2(0.0, 1.0)), hash(i + vec2(1.0, 1.0)), f.x),
    f.y
  );
}

float fbm(vec2 p) {
  float v = 0.0;
  float a = 0.5;
  mat2 rot = mat2(cos(0.5), sin(0.5), -sin(0.5), cos(0.5));
  for (int i = 0; i < 4; i++) {
    v += a * noise(p);
    p = rot * p * 2.0 + vec2(0.2, 0.1);
    a *= 0.5;
  }
  return v;
}

void main() {
  vec2 uv = gl_FragCoord.xy / u_resolution.xy;
  vec2 aspectUV = (gl_FragCoord.xy - 0.5 * u_resolution.xy) / min(u_resolution.x, u_resolution.y);
  
  float t = u_time * (0.8 + u_hover * 1.2 + u_warp * 2.0);
  
  // Turbulent flame displacement
  vec2 q = vec2(fbm(aspectUV * 3.0 + vec2(0.0, -t * 0.8)), fbm(aspectUV * 3.0 + vec2(t * 0.5, 0.0)));
  vec2 r = vec2(fbm(aspectUV * 4.0 + 4.0 * q + vec2(t * 0.3, -t * 0.5)), fbm(aspectUV * 4.0 + 4.0 * q + vec2(0.0, t * 0.4)));
  
  float f = fbm(aspectUV * 2.5 + 3.0 * r);
  
  // Ignition color gradient (dark volcanic red -> vivid amber -> hot gold -> white core)
  vec3 col = mix(vec3(0.06, 0.02, 0.03), vec3(0.85, 0.18, 0.05), clamp(f * f * 2.5, 0.0, 1.0));
  col = mix(col, vec3(1.0, 0.55, 0.08), clamp(length(q), 0.0, 1.0));
  col = mix(col, vec3(1.0, 0.95, 0.7), clamp(pow(r.x, 3.0) * (1.2 + u_hover * 0.8), 0.0, 1.0));
  
  // Border intensity glow
  float borderDist = length(v_uv - 0.5);
  col += vec3(0.9, 0.3, 0.05) * smoothstep(0.35, 0.55, borderDist) * (0.4 + u_hover * 0.6);
  
  gl_FragColor = vec4(col, 1.0);
}
`

export function initIgnitionRenderer(
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
