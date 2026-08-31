'use client'

import React, { useEffect, useRef, useCallback, useMemo } from 'react';
import { Mail, LogOut, ShieldCheck } from 'lucide-react';

const DEFAULT_INNER_GRADIENT = 'linear-gradient(145deg,#0e2238cc 0%,#159a9c44 50%,#2563eb33 100%)';

const ANIMATION_CONFIG = {
  INITIAL_DURATION: 1200,
  INITIAL_X_OFFSET: 70,
  INITIAL_Y_OFFSET: 60,
  DEVICE_BETA_OFFSET: 20,
  ENTER_TRANSITION_MS: 180
} as const;

const clamp = (v: number, min = 0, max = 100): number => Math.min(Math.max(v, min), max);
const round = (v: number, precision = 3): number => parseFloat(v.toFixed(precision));
const adjust = (v: number, fMin: number, fMax: number, tMin: number, tMax: number): number =>
  round(tMin + ((tMax - tMin) * (v - fMin)) / (fMax - fMin));

// Inject keyframes once
const KEYFRAMES_ID = 'pc-keyframes';
if (typeof document !== 'undefined' && !document.getElementById(KEYFRAMES_ID)) {
  const style = document.createElement('style');
  style.id = KEYFRAMES_ID;
  style.textContent = `
    @keyframes pc-holo-bg {
      0% { background-position: 0 var(--background-y), 0 0, center; }
      100% { background-position: 0 var(--background-y), 90% 90%, center; }
    }
  `;
  document.head.appendChild(style);
}

export interface ProfileCardProps {
  avatarUrl?: string;
  iconUrl?: string;
  grainUrl?: string;
  innerGradient?: string;
  behindGlowEnabled?: boolean;
  behindGlowColor?: string;
  behindGlowSize?: string;
  className?: string;
  enableTilt?: boolean;
  enableMobileTilt?: boolean;
  mobileTiltSensitivity?: number;
  miniAvatarUrl?: string;
  name?: string;
  title?: string;
  handle?: string;
  email?: string;
  status?: string;
  contactText?: string;
  showUserInfo?: boolean;
  roleId?: string;
  onContactClick?: () => void;
}

interface TiltEngine {
  setImmediate: (x: number, y: number) => void;
  setTarget: (x: number, y: number) => void;
  toCenter: () => void;
  beginInitial: (durationMs: number) => void;
  getCurrent: () => { x: number; y: number; tx: number; ty: number };
  cancel: () => void;
}

const ProfileCardComponent: React.FC<ProfileCardProps> = ({
  avatarUrl,
  iconUrl,
  grainUrl,
  innerGradient,
  behindGlowEnabled = true,
  behindGlowColor,
  behindGlowSize,
  className = '',
  enableTilt = true,
  enableMobileTilt = false,
  mobileTiltSensitivity = 5,
  miniAvatarUrl,
  name = 'test-developer',
  title = 'Platform Engineer / Developer',
  handle = 'test.developer',
  email,
  status = 'Online & Verified',
  contactText = 'Sign Out',
  showUserInfo = true,
  roleId,
  onContactClick
}) => {
  const wrapRef = useRef<HTMLDivElement>(null);
  const shellRef = useRef<HTMLDivElement>(null);

  const enterTimerRef = useRef<number | null>(null);
  const leaveRafRef = useRef<number | null>(null);

  const tiltEngine = useMemo<TiltEngine | null>(() => {
    if (!enableTilt) return null;

    let rafId: number | null = null;
    let running = false;
    let lastTs = 0;

    let currentX = 0;
    let currentY = 0;
    let targetX = 0;
    let targetY = 0;

    const DEFAULT_TAU = 0.14;
    const INITIAL_TAU = 0.6;
    let initialUntil = 0;

    const setVarsFromXY = (x: number, y: number): void => {
      const shell = shellRef.current;
      const wrap = wrapRef.current;
      if (!shell || !wrap) return;

      const width = shell.clientWidth || 1;
      const height = shell.clientHeight || 1;

      const percentX = clamp((100 / width) * x);
      const percentY = clamp((100 / height) * y);

      const centerX = percentX - 50;
      const centerY = percentY - 50;

      const properties: Record<string, string> = {
        '--pointer-x': `${percentX}%`,
        '--pointer-y': `${percentY}%`,
        '--background-x': `${adjust(percentX, 0, 100, 35, 65)}%`,
        '--background-y': `${adjust(percentY, 0, 100, 35, 65)}%`,
        '--pointer-from-center': `${clamp(Math.hypot(percentY - 50, percentX - 50) / 50, 0, 1)}`,
        '--pointer-from-top': `${percentY / 100}`,
        '--pointer-from-left': `${percentX / 100}`,
        '--rotate-x': `${round(-(centerX / 5))}deg`,
        '--rotate-y': `${round(centerY / 4)}deg`
      };

      for (const [k, v] of Object.entries(properties)) wrap.style.setProperty(k, v);
    };

    const step = (ts: number): void => {
      if (!running) return;
      if (lastTs === 0) lastTs = ts;
      const dt = (ts - lastTs) / 1000;
      lastTs = ts;

      const tau = ts < initialUntil ? INITIAL_TAU : DEFAULT_TAU;
      const k = 1 - Math.exp(-dt / tau);

      currentX += (targetX - currentX) * k;
      currentY += (targetY - currentY) * k;

      setVarsFromXY(currentX, currentY);

      const stillFar = Math.abs(targetX - currentX) > 0.05 || Math.abs(targetY - currentY) > 0.05;

      if (stillFar || (typeof document !== 'undefined' && document.hasFocus())) {
        rafId = requestAnimationFrame(step);
      } else {
        running = false;
        lastTs = 0;
        if (rafId) {
          cancelAnimationFrame(rafId);
          rafId = null;
        }
      }
    };

    const start = (): void => {
      if (running) return;
      running = true;
      lastTs = 0;
      rafId = requestAnimationFrame(step);
    };

    return {
      setImmediate(x: number, y: number): void {
        currentX = x;
        currentY = y;
        setVarsFromXY(currentX, currentY);
      },
      setTarget(x: number, y: number): void {
        targetX = x;
        targetY = y;
        start();
      },
      toCenter(): void {
        const shell = shellRef.current;
        if (!shell) return;
        this.setTarget(shell.clientWidth / 2, shell.clientHeight / 2);
      },
      beginInitial(durationMs: number): void {
        initialUntil = performance.now() + durationMs;
        start();
      },
      getCurrent(): { x: number; y: number; tx: number; ty: number } {
        return { x: currentX, y: currentY, tx: targetX, ty: targetY };
      },
      cancel(): void {
        if (rafId) cancelAnimationFrame(rafId);
        rafId = null;
        running = false;
        lastTs = 0;
      }
    };
  }, [enableTilt]);

  const getOffsets = (evt: PointerEvent, el: HTMLElement): { x: number; y: number } => {
    const rect = el.getBoundingClientRect();
    return { x: evt.clientX - rect.left, y: evt.clientY - rect.top };
  };

  const handlePointerMove = useCallback(
    (event: PointerEvent): void => {
      const shell = shellRef.current;
      if (!shell || !tiltEngine) return;
      const { x, y } = getOffsets(event, shell);
      tiltEngine.setTarget(x, y);
    },
    [tiltEngine]
  );

  const handlePointerEnter = useCallback(
    (event: PointerEvent): void => {
      const shell = shellRef.current;
      if (!shell || !tiltEngine) return;

      shell.classList.add('active');
      shell.classList.add('entering');
      if (enterTimerRef.current) window.clearTimeout(enterTimerRef.current);
      enterTimerRef.current = window.setTimeout(() => {
        shell.classList.remove('entering');
      }, ANIMATION_CONFIG.ENTER_TRANSITION_MS);

      const { x, y } = getOffsets(event, shell);
      tiltEngine.setTarget(x, y);
    },
    [tiltEngine]
  );

  const handlePointerLeave = useCallback((): void => {
    const shell = shellRef.current;
    if (!shell || !tiltEngine) return;

    tiltEngine.toCenter();

    const checkSettle = (): void => {
      const { x, y, tx, ty } = tiltEngine.getCurrent();
      const settled = Math.hypot(tx - x, ty - y) < 0.6;
      if (settled) {
        shell.classList.remove('active');
        leaveRafRef.current = null;
      } else {
        leaveRafRef.current = requestAnimationFrame(checkSettle);
      }
    };
    if (leaveRafRef.current) cancelAnimationFrame(leaveRafRef.current);
    leaveRafRef.current = requestAnimationFrame(checkSettle);
  }, [tiltEngine]);

  const handleDeviceOrientation = useCallback(
    (event: DeviceOrientationEvent): void => {
      const shell = shellRef.current;
      if (!shell || !tiltEngine) return;

      const { beta, gamma } = event;
      if (beta === null || gamma === null) return;

      const clampedBeta = clamp(beta, -ANIMATION_CONFIG.DEVICE_BETA_OFFSET, ANIMATION_CONFIG.DEVICE_BETA_OFFSET);
      const clampedGamma = clamp(gamma, -ANIMATION_CONFIG.DEVICE_BETA_OFFSET, ANIMATION_CONFIG.DEVICE_BETA_OFFSET);

      const x = adjust(
        clampedGamma,
        -ANIMATION_CONFIG.DEVICE_BETA_OFFSET,
        ANIMATION_CONFIG.DEVICE_BETA_OFFSET,
        0,
        shell.clientWidth || 0
      );
      const y = adjust(
        clampedBeta,
        -ANIMATION_CONFIG.DEVICE_BETA_OFFSET,
        ANIMATION_CONFIG.DEVICE_BETA_OFFSET,
        0,
        shell.clientHeight || 0
      );

      tiltEngine.setTarget(x * mobileTiltSensitivity, y * mobileTiltSensitivity);
    },
    [tiltEngine, mobileTiltSensitivity]
  );

  useEffect(() => {
    const shell = shellRef.current;
    if (!shell || !tiltEngine) return;

    const pointerEnterHandler = (e: Event) => handlePointerEnter(e as PointerEvent);
    const pointerMoveHandler = (e: Event) => handlePointerMove(e as PointerEvent);
    const pointerLeaveHandler = () => handlePointerLeave();
    const deviceOrientationHandler = (e: Event) => handleDeviceOrientation(e as DeviceOrientationEvent);

    shell.addEventListener('pointerenter', pointerEnterHandler);
    shell.addEventListener('pointermove', pointerMoveHandler);
    shell.addEventListener('pointerleave', pointerLeaveHandler);

    const handleClick = (): void => {
      if (!enableMobileTilt || location.protocol !== 'https:') return;
      const anyMotion = typeof DeviceMotionEvent !== 'undefined' ? (DeviceMotionEvent as any) : null;
      if (anyMotion && typeof anyMotion.requestPermission === 'function') {
        anyMotion
          .requestPermission()
          .then((state: string) => {
            if (state === 'granted') {
              window.addEventListener('deviceorientation', deviceOrientationHandler);
            }
          })
          .catch(console.error);
      } else {
        window.addEventListener('deviceorientation', deviceOrientationHandler);
      }
    };
    shell.addEventListener('click', handleClick);

    const initialX = (shell.clientWidth || 0) - ANIMATION_CONFIG.INITIAL_X_OFFSET;
    const initialY = ANIMATION_CONFIG.INITIAL_Y_OFFSET;
    tiltEngine.setImmediate(initialX, initialY);
    tiltEngine.toCenter();
    tiltEngine.beginInitial(ANIMATION_CONFIG.INITIAL_DURATION);

    return () => {
      shell.removeEventListener('pointerenter', pointerEnterHandler);
      shell.removeEventListener('pointermove', pointerMoveHandler);
      shell.removeEventListener('pointerleave', pointerLeaveHandler);
      shell.removeEventListener('click', handleClick);
      window.removeEventListener('deviceorientation', deviceOrientationHandler);
      if (enterTimerRef.current) window.clearTimeout(enterTimerRef.current);
      if (leaveRafRef.current) cancelAnimationFrame(leaveRafRef.current);
      tiltEngine.cancel();
      shell.classList.remove('entering');
    };
  }, [
    enableTilt,
    enableMobileTilt,
    tiltEngine,
    handlePointerMove,
    handlePointerEnter,
    handlePointerLeave,
    handleDeviceOrientation
  ]);

  const cardRadius = '24px';

  const cardStyle = useMemo(
    () => ({
      '--icon': iconUrl ? `url(${iconUrl})` : 'none',
      '--grain': grainUrl ? `url(${grainUrl})` : 'none',
      '--inner-gradient': innerGradient ?? DEFAULT_INNER_GRADIENT,
      '--behind-glow-color': behindGlowColor ?? 'rgba(21, 154, 156, 0.45)',
      '--behind-glow-size': behindGlowSize ?? '55%',
      '--pointer-x': '50%',
      '--pointer-y': '50%',
      '--pointer-from-center': '0',
      '--pointer-from-top': '0.5',
      '--pointer-from-left': '0.5',
      '--card-opacity': '1',
      '--rotate-x': '0deg',
      '--rotate-y': '0deg',
      '--background-x': '50%',
      '--background-y': '50%',
      '--card-radius': cardRadius,
      '--sunpillar-1': 'hsl(176, 100%, 76%)',
      '--sunpillar-2': 'hsl(204, 100%, 69%)',
      '--sunpillar-3': 'hsl(228, 100%, 74%)',
      '--sunpillar-4': 'hsl(176, 100%, 76%)',
      '--sunpillar-5': 'hsl(53, 100%, 69%)',
      '--sunpillar-6': 'hsl(283, 100%, 73%)',
      '--sunpillar-clr-1': 'var(--sunpillar-1)',
      '--sunpillar-clr-2': 'var(--sunpillar-2)',
      '--sunpillar-clr-3': 'var(--sunpillar-3)',
      '--sunpillar-clr-4': 'var(--sunpillar-4)',
      '--sunpillar-clr-5': 'var(--sunpillar-5)',
      '--sunpillar-clr-6': 'var(--sunpillar-6)'
    }),
    [iconUrl, grainUrl, innerGradient, behindGlowColor, behindGlowSize, cardRadius]
  );

  const handleContactClick = useCallback((e: React.MouseEvent): void => {
    e.stopPropagation();
    onContactClick?.();
  }, [onContactClick]);

  const effectiveEmail = email || (handle ? `${handle.replace('@', '')}@metaradar.demo` : 'user@metaradar.demo');

  // Shine layer style
  const shineStyle = {
    maskImage: 'var(--icon)',
    maskMode: 'luminance',
    maskRepeat: 'repeat',
    maskSize: '150%',
    maskPosition: 'top calc(200% - (var(--background-y) * 5)) left calc(100% - var(--background-x))',
    filter: 'brightness(0.66) contrast(1.33) saturate(0.33) opacity(0.4)',
    animation: 'pc-holo-bg 18s linear infinite',
    animationPlayState: 'running' as const,
    mixBlendMode: 'color-dodge' as const,
    transform: 'translate3d(0, 0, 1px)',
    overflow: 'hidden' as const,
    zIndex: 1,
    background: 'transparent',
    backgroundSize: 'cover',
    backgroundPosition: 'center',
    backgroundImage: `
      repeating-linear-gradient(
        0deg,
        var(--sunpillar-clr-1) 5%,
        var(--sunpillar-clr-2) 10%,
        var(--sunpillar-clr-3) 15%,
        var(--sunpillar-clr-4) 20%,
        var(--sunpillar-clr-5) 25%,
        var(--sunpillar-clr-6) 30%,
        var(--sunpillar-clr-1) 35%
      ),
      repeating-linear-gradient(
        -45deg,
        #0b1220 0%,
        hsl(180, 10%, 60%) 3.8%,
        hsl(180, 29%, 66%) 4.5%,
        hsl(180, 10%, 60%) 5.2%,
        #0b1220 10%,
        #0b1220 12%
      ),
      radial-gradient(
        farthest-corner circle at var(--pointer-x) var(--pointer-y),
        hsla(0, 0%, 0%, 0.1) 12%,
        hsla(0, 0%, 0%, 0.15) 20%,
        hsla(0, 0%, 0%, 0.25) 120%
      )
    `.replace(/\s+/g, ' '),
    gridArea: '1 / -1',
    borderRadius: cardRadius,
    pointerEvents: 'none' as const
  };

  const glareStyle: React.CSSProperties = {
    transform: 'translate3d(0, 0, 1.1px)',
    overflow: 'hidden',
    backgroundImage: `radial-gradient(
      farthest-corner circle at var(--pointer-x) var(--pointer-y),
      hsl(248, 25%, 80%) 12%,
      hsla(207, 40%, 30%, 0.6) 90%
    )`,
    mixBlendMode: 'overlay',
    filter: 'brightness(0.8) contrast(1.2)',
    zIndex: 2,
    gridArea: '1 / -1',
    borderRadius: cardRadius,
    pointerEvents: 'none'
  };

  return (
    <div
      ref={wrapRef}
      className={`relative touch-none ${className}`.trim()}
      style={{ perspective: '600px', transform: 'translate3d(0, 0, 0.1px)', ...cardStyle } as React.CSSProperties}
    >
      {behindGlowEnabled && (
        <div
          className="absolute inset-0 z-0 pointer-events-none transition-opacity duration-200 ease-out"
          style={{
            background: `radial-gradient(circle at var(--pointer-x) var(--pointer-y), var(--behind-glow-color) 0%, transparent var(--behind-glow-size))`,
            filter: 'blur(50px) saturate(1.2)',
            opacity: 'calc(0.85 * var(--card-opacity))'
          }}
        />
      )}
      <div ref={shellRef} className="relative z-[1] group">
        <section
          className="grid relative overflow-hidden shadow-2xl border border-white/20"
          style={{
            height: '500px',
            maxHeight: '520px',
            width: '325px',
            borderRadius: cardRadius,
            backgroundBlendMode: 'color-dodge, normal, normal, normal',
            boxShadow:
              'rgba(0, 0, 0, 0.85) calc((var(--pointer-from-left) * 10px) - 3px) calc((var(--pointer-from-top) * 20px) - 6px) 28px -4px',
            transition: 'transform 1s ease',
            transform: 'translateZ(0) rotateX(0deg) rotateY(0deg)',
            background: '#070c18',
            backfaceVisibility: 'hidden'
          }}
          onMouseEnter={e => {
            e.currentTarget.style.transition = 'none';
            e.currentTarget.style.transform = 'translateZ(0) rotateX(var(--rotate-y)) rotateY(var(--rotate-x))';
          }}
          onMouseLeave={e => {
            const shell = shellRef.current;
            if (shell?.classList.contains('entering')) {
              e.currentTarget.style.transition = 'transform 180ms ease-out';
            } else {
              e.currentTarget.style.transition = 'transform 1s ease';
            }
            e.currentTarget.style.transform = 'translateZ(0) rotateX(0deg) rotateY(0deg)';
          }}
        >
          <div
            className="absolute inset-0"
            style={{
              backgroundImage: 'var(--inner-gradient)',
              backgroundColor: '#070c18',
              borderRadius: cardRadius,
              display: 'grid',
              gridArea: '1 / -1'
            }}
          >
            {/* Shine layer */}
            <div style={shineStyle} />

            {/* Glare layer */}
            <div style={glareStyle} />

            {/* Main Interactive Foreground Container (Z-10, Pointer-Events-Auto) */}
            <div
              className="relative z-10 flex flex-col justify-between p-5 h-full pointer-events-auto"
              style={{
                transform:
                  'translate3d(calc(var(--pointer-from-left) * -6px + 3px), calc(var(--pointer-from-top) * -6px + 3px), 2px)',
                gridArea: '1 / -1',
                borderRadius: cardRadius
              }}
            >
              {/* TOP: Identity Header */}
              <div className="flex flex-col items-center text-center space-y-1.5 pt-1">
                <div className="flex items-center gap-1 px-2.5 py-0.5 rounded-full bg-cyan-950/70 border border-cyan-500/30 text-[10px] font-mono font-semibold text-cyan-300 tracking-wider uppercase mb-0.5">
                  <ShieldCheck size={11} className="text-cyan-400" />
                  <span>MetaRadar Verified</span>
                </div>

                <h3
                  className="font-black text-xl text-white tracking-tight m-0 drop-shadow-[0_2px_8px_rgba(0,0,0,0.9)]"
                  style={{ color: '#ffffff' }}
                >
                  {name}
                </h3>

                <p
                  className="font-bold text-xs px-3 py-1 rounded-full text-[#52d0c2] bg-slate-950/80 border border-[#52d0c2]/30 shadow-md inline-block max-w-[270px] truncate"
                >
                  {title}
                </p>

                {/* Email Address Pill */}
                <div className="flex items-center justify-center gap-1.5 px-3 py-0.5 rounded-full bg-slate-900/80 border border-white/10 text-[11px] font-mono text-slate-300 mt-1 max-w-[260px] truncate shadow-inner">
                  <Mail size={11} className="text-cyan-400 shrink-0" />
                  <span className="truncate">{effectiveEmail}</span>
                </div>
              </div>

              {/* CENTER: Empty Black Silhouette Avatar Figure */}
              <div className="my-auto flex flex-col items-center justify-center py-2">
                {avatarUrl ? (
                  <div className="w-32 h-32 rounded-full overflow-hidden border-2 border-cyan-400/40 shadow-2xl bg-black">
                    {/* eslint-disable-next-line @next/next/no-img-element */}
                    <img
                      className="w-full h-full object-cover"
                      src={avatarUrl}
                      alt={`${name || 'User'} avatar`}
                      loading="lazy"
                      onError={e => {
                        const t = e.target as HTMLImageElement;
                        t.style.display = 'none';
                      }}
                    />
                  </div>
                ) : (
                  <div className="relative flex flex-col items-center justify-center group/avatar">
                    {/* Ambient Glow behind silhouette */}
                    <div className="absolute -inset-2 rounded-full bg-gradient-to-tr from-cyan-500/20 via-blue-500/10 to-transparent blur-xl pointer-events-none" />
                    
                    {/* Frame */}
                    <div className="relative w-36 h-36 rounded-full flex items-center justify-center border-2 border-white/20 bg-gradient-to-b from-slate-950 via-[#060913] to-black shadow-[0_10px_30px_rgba(0,0,0,0.9)] overflow-hidden">
                      {/* Empty Black Silhouette SVG Vector */}
                      <svg
                        viewBox="0 0 100 100"
                        className="w-28 h-28 drop-shadow-[0_4px_16px_rgba(0,0,0,1)] translate-y-1.5"
                      >
                        <defs>
                          <linearGradient id="silhouetteRim" x1="0%" y1="0%" x2="100%" y2="100%">
                            <stop offset="0%" stopColor="#1e293b" />
                            <stop offset="50%" stopColor="#0b1329" />
                            <stop offset="100%" stopColor="#020617" />
                          </linearGradient>
                        </defs>
                        {/* Head */}
                        <circle
                          cx="50"
                          cy="34"
                          r="17"
                          fill="url(#silhouetteRim)"
                          stroke="rgba(255, 255, 255, 0.25)"
                          strokeWidth="1.2"
                        />
                        {/* Torso / Shoulders */}
                        <path
                          d="M18 88 C18 64, 33 57, 50 57 C67 57, 82 64, 82 88 Z"
                          fill="url(#silhouetteRim)"
                          stroke="rgba(255, 255, 255, 0.25)"
                          strokeWidth="1.2"
                        />
                      </svg>

                      {/* Subtle Holographic Grid Line Accent */}
                      <div className="absolute inset-0 bg-gradient-to-b from-transparent via-cyan-400/5 to-transparent pointer-events-none" />
                    </div>
                  </div>
                )}
              </div>

              {/* BOTTOM: Handle, Live Status & Sign Out Button */}
              {showUserInfo && (
                <div
                  className="rounded-2xl p-2.5 flex items-center justify-between border border-white/20 shadow-xl backdrop-blur-xl"
                  style={{
                    background: 'rgba(7, 12, 24, 0.88)'
                  }}
                >
                  <div className="flex items-center gap-2">
                    <div className="w-8 h-8 rounded-full bg-slate-950 border border-white/20 flex items-center justify-center shrink-0">
                      {/* Mini Silhouette */}
                      <svg viewBox="0 0 100 100" className="w-5 h-5 text-white/70" fill="currentColor">
                        <circle cx="50" cy="35" r="16" fill="#0f172a" stroke="rgba(255,255,255,0.4)" strokeWidth="2" />
                        <path d="M22 86 C22 65, 35 58, 50 58 C65 58, 78 65, 78 86 Z" fill="#0f172a" stroke="rgba(255,255,255,0.4)" strokeWidth="2" />
                      </svg>
                    </div>

                    <div className="flex flex-col items-start leading-tight">
                      <span className="text-xs font-bold text-white tracking-tight">@{handle}</span>
                      <div className="text-[10px] font-semibold flex items-center gap-1 mt-0.5 text-emerald-400">
                        <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                        <span>{status}</span>
                      </div>
                    </div>
                  </div>

                  {/* Sign Out / Action Button */}
                  <button
                    type="button"
                    onClick={handleContactClick}
                    className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-bold text-rose-200 bg-rose-950/70 hover:bg-rose-900 border border-rose-500/40 hover:border-rose-400 hover:text-white transition-all shadow-md cursor-pointer shrink-0 active:scale-95"
                    aria-label={`${contactText} for ${name || 'user'}`}
                  >
                    <LogOut size={12} className="text-rose-400" />
                    <span>{contactText}</span>
                  </button>
                </div>
              )}
            </div>
          </div>
        </section>
      </div>
    </div>
  );
};

const ProfileCard = React.memo(ProfileCardComponent);
export default ProfileCard;
