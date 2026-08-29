'use client'

import React, { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/context/AuthContext'
import ProfileCard from '@/components/auth/ProfileCard'
import { Shield, Radar, ArrowRight, Eye, EyeOff, Loader2, AlertCircle, Sparkles, CheckCircle2 } from 'lucide-react'

interface RolePersona {
  id: string
  label: string
  name: string
  title: string
  handle: string
  email: string
  password: string
  color: string
  bgClass: string
  borderClass: string
  textClass: string
  badgeClass: string
  glowClass: string
}

const PERSONAS: RolePersona[] = [
  {
    id: 'MEDICAL_AFFAIRS',
    label: 'Medical Affairs',
    name: 'Dr. Elena Vance',
    title: 'Medical Affairs Lead',
    handle: '@elena.vance',
    email: 'medical.affairs@metaradar.demo',
    password: 'MedAffairs2026!',
    color: 'emerald',
    bgClass: 'hover:bg-emerald-500/10',
    borderClass: 'border-emerald-500/40 text-emerald-400',
    textClass: 'text-emerald-400',
    badgeClass: 'bg-emerald-500/20 text-emerald-300 border-emerald-500/30',
    glowClass: 'rgba(52, 211, 153, 0.4)',
  },
  {
    id: 'REGULATORY',
    label: 'Regulatory Affairs',
    name: 'Marcus Chen',
    title: 'Regulatory Affairs Director',
    handle: '@marcus.chen',
    email: 'regulatory@metaradar.demo',
    password: 'Regulatory2026!',
    color: 'blue',
    bgClass: 'hover:bg-blue-500/10',
    borderClass: 'border-blue-500/40 text-blue-400',
    textClass: 'text-blue-400',
    badgeClass: 'bg-blue-500/20 text-blue-300 border-blue-500/30',
    glowClass: 'rgba(96, 165, 250, 0.4)',
  },
  {
    id: 'SAFETY',
    label: 'Safety & PV',
    name: 'Dr. Sarah Jenkins',
    title: 'Pharmacovigilance Lead',
    handle: '@sarah.jenkins',
    email: 'safety@metaradar.demo',
    password: 'Safety2026!',
    color: 'rose',
    bgClass: 'hover:bg-rose-500/10',
    borderClass: 'border-rose-500/40 text-rose-400',
    textClass: 'text-rose-400',
    badgeClass: 'bg-rose-500/20 text-rose-300 border-rose-500/30',
    glowClass: 'rgba(248, 113, 113, 0.4)',
  },
  {
    id: 'MARKET_ACCESS',
    label: 'Market Access',
    name: 'Henrik Lindqvist',
    title: 'Value & Access Director',
    handle: '@henrik.l',
    email: 'market.access@metaradar.demo',
    password: 'Access2026!',
    color: 'amber',
    bgClass: 'hover:bg-amber-500/10',
    borderClass: 'border-amber-500/40 text-amber-400',
    textClass: 'text-amber-400',
    badgeClass: 'bg-amber-500/20 text-amber-300 border-amber-500/30',
    glowClass: 'rgba(251, 191, 36, 0.4)',
  },
  {
    id: 'COMMUNICATIONS',
    label: 'Communications',
    name: 'Claire Beaumont',
    title: 'Medical Communications Lead',
    handle: '@claire.beaumont',
    email: 'comms@metaradar.demo',
    password: 'Comms2026!',
    color: 'purple',
    bgClass: 'hover:bg-purple-500/10',
    borderClass: 'border-purple-500/40 text-purple-400',
    textClass: 'text-purple-400',
    badgeClass: 'bg-purple-500/20 text-purple-300 border-purple-500/30',
    glowClass: 'rgba(167, 139, 250, 0.4)',
  },
  {
    id: 'LEADERSHIP',
    label: 'Executive Leadership',
    name: 'Dr. Alexander Wright',
    title: 'EVP Global Development',
    handle: '@alex.wright',
    email: 'leadership@metaradar.demo',
    password: 'Leader2026!',
    color: 'indigo',
    bgClass: 'hover:bg-indigo-500/10',
    borderClass: 'border-indigo-500/40 text-indigo-400',
    textClass: 'text-indigo-400',
    badgeClass: 'bg-indigo-500/20 text-indigo-300 border-indigo-500/30',
    glowClass: 'rgba(129, 140, 248, 0.5)',
  },
]

export default function LoginPage() {
  const router = useRouter()
  const { login, isAuthenticated, isLoading: authLoading } = useAuth()

  const [selectedPersona, setSelectedPersona] = useState<RolePersona>(PERSONAS[0])
  const [email, setEmail] = useState<string>(PERSONAS[0].email)
  const [password, setPassword] = useState<string>(PERSONAS[0].password)
  const [showPassword, setShowPassword] = useState<boolean>(false)
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)
  const [justAutofilled, setJustAutofilled] = useState<boolean>(true)

  useEffect(() => {
    if (isAuthenticated && !authLoading) {
      router.push('/dashboard')
    }
  }, [isAuthenticated, authLoading, router])

  const selectPersona = (p: RolePersona) => {
    setSelectedPersona(p)
    setEmail(p.email)
    setPassword(p.password)
    setErrorMessage(null)
    setJustAutofilled(true)
    setTimeout(() => setJustAutofilled(false), 1200)
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!email || !password) {
      setErrorMessage('Please enter both email and password.')
      return
    }

    setIsSubmitting(true)
    setErrorMessage(null)

    try {
      await login({ email, password })
      router.push('/dashboard')
    } catch (err: any) {
      setErrorMessage(
        err?.message || 'Invalid credentials. Please verify your email and password.'
      )
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <div className="relative min-h-screen flex flex-col items-center justify-center px-4 py-12 overflow-x-hidden">
      {/* Ambient background glows */}
      <div className="absolute top-1/4 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[700px] h-[500px] bg-blue-600/10 rounded-full blur-[140px] pointer-events-none" />
      <div className="absolute bottom-1/4 left-1/3 w-[500px] h-[400px] bg-teal-500/10 rounded-full blur-[120px] pointer-events-none" />

      {/* Brand Header */}
      <div className="relative z-10 text-center mb-8 max-w-2xl">
        <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-slate-900/80 border border-slate-700/60 shadow-lg mb-4 backdrop-blur-md">
          <Radar className="w-4 h-4 text-cyan-400 animate-spin" style={{ animationDuration: '6s' }} />
          <span className="text-xs font-semibold tracking-wide text-slate-200">
            Novo Nordisk GBS Hackathon 2026
          </span>
          <span className="text-[10px] uppercase font-mono px-1.5 py-0.5 rounded bg-cyan-500/20 text-cyan-300 font-bold">
            v5.1 Live
          </span>
        </div>

        <h1 className="text-3xl sm:text-4xl font-extrabold tracking-tight text-white mb-2">
          MetaRadar <span className="bg-clip-text text-transparent bg-gradient-to-r from-cyan-400 to-blue-500">Haemophilia</span>
        </h1>
        <p className="text-sm sm:text-base text-slate-400">
          Continuous AI Decision Intelligence Radar across Clinical, Regulatory, Safety & Market Signals
        </p>
      </div>

      {/* Role Quick-Select Carousel */}
      <div className="relative z-10 w-full max-w-4xl mb-8">
        <div className="flex items-center justify-between px-2 mb-3">
          <div className="flex items-center gap-2 text-xs font-semibold text-slate-400 uppercase tracking-wider">
            <Sparkles className="w-3.5 h-3.5 text-cyan-400" />
            <span>Select Stakeholder Role (Zero-Friction Auto-Fill)</span>
          </div>
          <span className="text-xs text-slate-400 font-mono hidden sm:inline">
            Click pill to auto-fill credentials
          </span>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-2.5">
          {PERSONAS.map((p) => {
            const isSelected = selectedPersona.id === p.id
            return (
              <button
                key={p.id}
                type="button"
                onClick={() => selectPersona(p)}
                onMouseEnter={() => setSelectedPersona(p)}
                className={`flex flex-col items-start p-3 rounded-xl border text-left transition-all duration-200 ${
                  isSelected
                    ? `bg-slate-900/90 ${p.borderClass} ring-1 ring-offset-0 shadow-lg scale-[1.02]`
                    : `bg-slate-900/40 border-slate-800 text-slate-400 hover:text-slate-200 ${p.bgClass}`
                }`}
                style={{
                  boxShadow: isSelected ? `0 0 20px ${p.glowClass}` : undefined,
                }}
              >
                <div className="flex items-center justify-between w-full mb-1">
                  <span
                    className="w-2 h-2 rounded-full"
                    style={{
                      backgroundColor: isSelected ? p.borderClass : '#64748b',
                      boxShadow: isSelected ? `0 0 8px ${p.glowClass}` : 'none',
                    }}
                  />
                  {isSelected && <CheckCircle2 className="w-3 h-3 text-cyan-400" />}
                </div>
                <span className="text-xs font-bold text-slate-200 line-clamp-1">{p.label}</span>
                <span className="text-[11px] text-slate-400 line-clamp-1">{p.name.split(' ')[0]}</span>
              </button>
            )
          })}
        </div>
      </div>

      {/* Main Login Deck: 3D Tilt Card + Credential Form */}
      <div className="relative z-10 w-full max-w-4xl grid grid-cols-1 lg:grid-cols-12 gap-8 items-center">
        {/* Left Column: Interactive 3D Tilt ProfileCard */}
        <div className="lg:col-span-5 flex flex-col items-center justify-center">
          <ProfileCard
            name={selectedPersona.name}
            title={selectedPersona.title}
            handle={selectedPersona.handle}
            roleId={selectedPersona.id}
            status="Online & Verified"
            contactText="Auto-Fill Credentials"
            onContactClick={() => selectPersona(selectedPersona)}
          />
          <p className="mt-3 text-[11px] text-slate-400 font-mono text-center">
            Move cursor over card for 3D holographic tilt
          </p>
        </div>

        {/* Right Column: Sign In Card */}
        <div className="lg:col-span-7">
          <div className="bg-slate-900/90 border border-slate-800/80 rounded-2xl p-6 sm:p-8 shadow-2xl backdrop-blur-xl">
            <div className="flex items-center justify-between mb-6 pb-4 border-b border-slate-800">
              <div>
                <h2 className="text-lg font-bold text-slate-100">Enterprise Sign In</h2>
                <p className="text-xs text-slate-400">Authenticated RBAC Session</p>
              </div>
              <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-slate-800/80 border border-slate-700 text-xs font-medium text-slate-300">
                <Shield className="w-3.5 h-3.5 text-cyan-400" />
                <span>RBAC v5.1</span>
              </div>
            </div>

            {errorMessage && (
              <div className="flex items-center gap-2 p-3 mb-5 rounded-lg bg-rose-950/50 border border-rose-800/80 text-rose-300 text-xs animate-shake">
                <AlertCircle className="w-4 h-4 shrink-0 text-rose-400" />
                <span>{errorMessage}</span>
              </div>
            )}

            {justAutofilled && (
              <div className="flex items-center gap-2 p-2.5 mb-5 rounded-lg bg-emerald-950/40 border border-emerald-800/60 text-emerald-300 text-xs transition-opacity duration-500">
                <CheckCircle2 className="w-4 h-4 shrink-0 text-emerald-400" />
                <span>Auto-filled verified credentials for <strong>{selectedPersona.name}</strong></span>
              </div>
            )}

            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1.5">
                  Email Address
                </label>
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="name@metaradar.demo"
                  required
                  className="w-full px-3.5 py-2.5 rounded-lg bg-slate-950/70 border border-slate-800 text-slate-100 placeholder-slate-600 text-sm focus:outline-none focus:ring-2 focus:ring-cyan-500/50 focus:border-cyan-500/80 transition-all font-mono"
                />
              </div>

              <div>
                <div className="flex items-center justify-between mb-1.5">
                  <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider">
                    Password
                  </label>
                  <span className="text-[11px] text-slate-400 font-mono">
                    Fixed Demo Secret
                  </span>
                </div>
                <div className="relative">
                  <input
                    type={showPassword ? 'text' : 'password'}
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="••••••••••••"
                    required
                    className="w-full px-3.5 py-2.5 pr-10 rounded-lg bg-slate-950/70 border border-slate-800 text-slate-100 placeholder-slate-600 text-sm focus:outline-none focus:ring-2 focus:ring-cyan-500/50 focus:border-cyan-500/80 transition-all font-mono"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-200 transition-colors"
                  >
                    {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                  </button>
                </div>
              </div>

              <div className="pt-2">
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="w-full flex items-center justify-center gap-2 px-4 py-3 rounded-xl bg-gradient-to-r from-blue-600 to-cyan-600 hover:from-blue-500 hover:to-cyan-500 text-white font-bold text-sm shadow-lg shadow-cyan-900/30 transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed hover:scale-[1.01] active:scale-[0.99]"
                >
                  {isSubmitting ? (
                    <>
                      <Loader2 className="w-4 h-4 animate-spin" />
                      <span>Authenticating Persona...</span>
                    </>
                  ) : (
                    <>
                      <span>Sign In as {selectedPersona.label}</span>
                      <ArrowRight className="w-4 h-4" />
                    </>
                  )}
                </button>
              </div>
            </form>

            <div className="mt-6 pt-4 border-t border-slate-800 text-center">
              <p className="text-[11px] text-slate-400">
                Novo Nordisk Hackathon evaluation mode • Deterministic JWT session & append-only audit trail
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
