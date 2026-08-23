/**
 * Star Portal WebGL Renderer
 * Authored Starfield Warp Tunnel Shader with Interactive Pointer Gravitational Lensing.
 */

export interface RendererHandle {
  destroy: () => void
  setPointer: (x: number, y: number, hover: boolean) => void
  setWarp: (warp: number) => void
  resize: () => void
}

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
uniform float u_mode; // 0.0 = dark, 1.0 = light
varying vec2 v_uv;

#define NUM_LAYERS 4.0
#define PI 3.14159265359

mat2 rotate2d(float angle) {
  return mat2(cos(angle), -sin(angle), sin(angle), cos(angle));
}

// Pseudo-random hash
float hash21(vec2 p) {
  p = fract(p * vec2(123.34, 456.21));
  p += dot(p, p + 45.32);
  return fract(p.x * p.y);
}

// Procedural starfield layer
vec3 starLayer(vec2 uv, float t, float layerIndex) {
  vec2 gv = fract(uv) - 0.5;
  vec2 id = floor(uv);
  
  vec3 col = vec3(0.0);
  
  for (int y = -1; y <= 1; y++) {
    for (int x = -1; x <= 1; x++) {
      vec2 offs = vec2(float(x), float(y));
      vec2 nId = id + offs;
      float n = hash21(nId + layerIndex * 17.13);
      
      // Star position with jitter
      vec2 starPos = gv - offs - vec2(n - 0.5, fract(n * 34.0) - 0.5) * 0.7;
      
      // Streak elongation in warp direction
      float streak = 1.0 + (u_warp + u_hover * 1.5) * 3.0;
      starPos.y /= streak;
      
      float dist = length(starPos);
      
      // Procedural brightness and twinkle
      float size = mix(0.015, 0.045, fract(n * 123.45));
      float star = smoothstep(size, 0.0, dist);
      float flare = max(0.0, 1.0 - dist * 12.0) * 0.4;
      
      // Cosmic tint variation (electric indigo, cyan, warm gold)
      vec3 tint = mix(
        vec3(0.38, 0.45, 1.0),
        vec3(0.05, 0.85, 0.95),
        fract(n * 45.67)
      );
      if (fract(n * 89.1) > 0.7) {
        tint = vec3(1.0, 0.75, 0.35); // Gold accent
      }
      
      col += (star + flare) * tint * mix(0.6, 1.0, fract(n * 78.9 + t * 2.0));
    }
  }
  return col;
}

void main() {
  vec2 uv = (gl_FragCoord.xy - 0.5 * u_resolution.xy) / min(u_resolution.x, u_resolution.y);
  
  // Gravitational lensing towards interactive pointer
  vec2 pointerUV = (u_pointer - 0.5 * u_resolution.xy) / min(u_resolution.x, u_resolution.y);
  vec2 toPointer = pointerUV - uv;
  float pDist = length(toPointer);
  uv += normalize(toPointer + 0.001) * (0.04 / (pDist * 8.0 + 1.0)) * u_hover;
  
  // Warp speed time parameter
  float baseSpeed = 0.25 + u_warp * 1.8 + u_hover * 0.8;
  float t = u_time * baseSpeed;
  
  // Gentle swirl rotation
  uv *= rotate2d(sin(t * 0.15) * 0.15 + length(uv) * 0.4);
  
  vec3 color = vec3(0.0);
  
  // Deep space background gradient
  vec3 spaceDark = vec3(0.035, 0.05, 0.09);
  vec3 spaceNebula = vec3(0.08, 0.12, 0.28);
  vec3 bg = mix(spaceDark, spaceNebula, length(uv) * 1.2);
  color += bg;
  
  // Render multi-depth starfield layers
  for (float i = 0.0; i < NUM_LAYERS; i++) {
    float depth = fract(i / NUM_LAYERS + t * 0.12);
    float scale = mix(12.0, 0.8, depth);
    float fade = depth * smoothstep(1.0, 0.85, depth);
    
    vec2 layerUV = uv * scale + vec2(0.0, -t * 2.5 * (1.0 + i * 0.3));
    color += starLayer(layerUV, t, i) * fade * 1.4;
  }
  
  // Center radiant portal core
  float coreDist = length(uv);
  float coreGlow = 0.06 / (coreDist * 4.0 + 0.12);
  vec3 coreColor = mix(vec3(0.39, 0.4, 0.95), vec3(0.02, 0.8, 0.98), sin(t * 1.5) * 0.5 + 0.5);
  color += coreGlow * coreColor * (0.8 + u_warp * 1.2 + u_hover * 0.5);
  
  // Edge vignette
  float vignette = smoothstep(1.2, 0.2, length(v_uv - 0.5) * 1.4);
  color *= vignette;
  
  // Light / dark mode adjustment
  if (u_mode > 0.5) {
    color = mix(color, color * 1.15 + vec3(0.02, 0.03, 0.05), 0.1);
  }
  
  gl_FragColor = vec4(color, 1.0);
}
`

function createShader(gl: WebGLRenderingContext, type: number, source: string): WebGLShader | null {
  const shader = gl.createShader(type)
  if (!shader) return null
  gl.shaderSource(shader, source)
  gl.compileShader(shader)
  if (!gl.getShaderParameter(shader, gl.COMPILE_STATUS)) {
    console.warn('[StarPortal] Shader compile failed:', gl.getShaderInfoLog(shader))
    gl.deleteShader(shader)
    return null
  }
  return shader
}

export function initStarPortalRenderer(
  canvas: HTMLCanvasElement,
  options?: { mode?: 'dark' | 'light' }
): RendererHandle | null {
  const gl = canvas.getContext('webgl', {
    alpha: false,
    antialias: true,
    powerPreference: 'high-performance',
    preserveDrawingBuffer: false,
  })

  if (!gl) {
    return null
  }

  const vertShader = createShader(gl, gl.VERTEX_SHADER, VERT_SRC)
  const fragShader = createShader(gl, gl.FRAGMENT_SHADER, FRAG_SRC)
  if (!vertShader || !fragShader) return null

  const program = gl.createProgram()
  if (!program) return null
  gl.attachShader(program, vertShader)
  gl.attachShader(program, fragShader)
  gl.linkProgram(program)

  if (!gl.getProgramParameter(program, gl.LINK_STATUS)) {
    console.warn('[StarPortal] Program link failed:', gl.getProgramInfoLog(program))
    return null
  }

  gl.useProgram(program)

  const posBuffer = gl.createBuffer()
  gl.bindBuffer(gl.ARRAY_BUFFER, posBuffer)
  gl.bufferData(
    gl.ARRAY_BUFFER,
    new Float32Array([-1, -1, 1, -1, -1, 1, -1, 1, 1, -1, 1, 1]),
    gl.STATIC_DRAW
  )

  const aPosition = gl.getAttribLocation(program, 'a_position')
  gl.enableVertexAttribArray(aPosition)
  gl.vertexAttribPointer(aPosition, 2, gl.FLOAT, false, 0, 0)

  const uResolution = gl.getUniformLocation(program, 'u_resolution')
  const uTime = gl.getUniformLocation(program, 'u_time')
  const uPointer = gl.getUniformLocation(program, 'u_pointer')
  const uHover = gl.getUniformLocation(program, 'u_hover')
  const uWarp = gl.getUniformLocation(program, 'u_warp')
  const uMode = gl.getUniformLocation(program, 'u_mode')

  let animFrameId: number | null = null
  let startTime = performance.now()
  let pointerX = 0
  let pointerY = 0
  let isHovered = false
  let currentHover = 0
  let warpFactor = 0
  let currentWarp = 0

  const resize = () => {
    const dpr = Math.min(window.devicePixelRatio || 1, 2)
    const rect = canvas.getBoundingClientRect()
    const width = Math.max(Math.floor(rect.width * dpr), 32)
    const height = Math.max(Math.floor(rect.height * dpr), 32)

    if (canvas.width !== width || canvas.height !== height) {
      canvas.width = width
      canvas.height = height
      gl.viewport(0, 0, width, height)
    }
  }

  resize()

  const render = (timeNow: number) => {
    const elapsed = (timeNow - startTime) * 0.001

    // Smooth hover & warp transitions
    currentHover += ((isHovered ? 1 : 0) - currentHover) * 0.1
    currentWarp += (warpFactor - currentWarp) * 0.08

    gl.useProgram(program)
    gl.uniform2f(uResolution, canvas.width, canvas.height)
    gl.uniform1f(uTime, elapsed)
    gl.uniform2f(uPointer, pointerX * (window.devicePixelRatio || 1), (canvas.height - pointerY * (window.devicePixelRatio || 1)))
    gl.uniform1f(uHover, currentHover)
    gl.uniform1f(uWarp, currentWarp)
    gl.uniform1f(uMode, options?.mode === 'light' ? 1.0 : 0.0)

    gl.drawArrays(gl.TRIANGLES, 0, 6)

    animFrameId = requestAnimationFrame(render)
  }

  animFrameId = requestAnimationFrame(render)

  return {
    destroy: () => {
      if (animFrameId !== null) cancelAnimationFrame(animFrameId)
      if (posBuffer) gl.deleteBuffer(posBuffer)
      if (vertShader) gl.deleteShader(vertShader)
      if (fragShader) gl.deleteShader(fragShader)
      if (program) gl.deleteProgram(program)
    },
    setPointer: (x: number, y: number, hover: boolean) => {
      pointerX = x
      pointerY = y
      isHovered = hover
    },
    setWarp: (warp: number) => {
      warpFactor = warp
    },
    resize,
  }
}
