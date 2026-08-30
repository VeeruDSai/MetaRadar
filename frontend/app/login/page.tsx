'use client'

import React, { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/context/AuthContext'
import ProfileCard from '@/components/auth/ProfileCard'
import { MetaRadarLogo } from '@/components/common/MetaRadarLogo'
import { Shield, ArrowRight, Eye, EyeOff, Loader2, AlertCircle, Sparkles, CheckCircle2 } from 'lucide-react'

interface RolePersona {
  id: string
  label: string
  name: string
  title: string
  handle: string
  email: string
  password: string
  tone: 'emerald' | 'blue' | 'rose' | 'amber' | 'purple' | 'indigo'
  dotColor: string
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
    tone: 'emerald',
    dotColor: 'var(--signal)',
  },
  {
    id: 'REGULATORY',
    label: 'Regulatory Affairs',
    name: 'Marcus Chen',
    title: 'Regulatory Affairs Director',
    handle: '@marcus.chen',
    email: 'regulatory@metaradar.demo',
    password: 'Regulatory2026!',
    tone: 'blue',
    dotColor: 'var(--primary)',
  },
  {
    id: 'SAFETY',
    label: 'Safety & PV',
    name: 'Dr. Sarah Jenkins',
    title: 'Pharmacovigilance Lead',
    handle: '@sarah.jenkins',
    email: 'safety@metaradar.demo',
    password: 'Safety2026!',
    tone: 'rose',
    dotColor: 'var(--critical)',
  },
  {
    id: 'MARKET_ACCESS',
    label: 'Market Access',
    name: 'Henrik Lindqvist',
    title: 'Value & Access Director',
    handle: '@henrik.l',
    email: 'market.access@metaradar.demo',
    password: 'Access2026!',
    tone: 'amber',
    dotColor: 'var(--warning)',
  },
  {
    id: 'COMMUNICATIONS',
    label: 'Communications',
    name: 'Claire Beaumont',
    title: 'Medical Communications Lead',
    handle: '@claire.beaumont',
    email: 'comms@metaradar.demo',
    password: 'Comms2026!',
    tone: 'purple',
    dotColor: '#a78bfa',
  },
  {
    id: 'LEADERSHIP',
    label: 'Executive Leadership',
    name: 'Dr. Alexander Wright',
    title: 'EVP Global Development',
    handle: '@alex.wright',
    email: 'leadership@metaradar.demo',
    password: 'Leader2026!',
    tone: 'indigo',
    dotColor: '#818cf8',
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
    setTimeout(() => setJustAutofilled(false), 1500)
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
    <div className="relative min-h-screen bg-[var(--background)] text-[var(--foreground)] flex flex-col items-center justify-center px-4 py-10 overflow-x-hidden font-sans select-none">
      {/* MetaRadar Ambient Radial Glows */}
      <div className="absolute top-1/4 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[750px] h-[550px] bg-[radial-gradient(circle,color-mix(in_srgb,var(--primary)_12%,transparent)_0%,transparent_70%)] blur-[140px] pointer-events-none" />
      <div className="absolute bottom-1/4 left-1/3 w-[550px] h-[450px] bg-[radial-gradient(circle,color-mix(in_srgb,var(--signal)_10%,transparent)_0%,transparent_70%)] blur-[120px] pointer-events-none" />

      {/* Brand Header */}
      <div className="relative z-10 text-center mb-8 max-w-2xl flex flex-col items-center">
        <div className="mb-3 flex items-center justify-center">
          <div className="p-2 rounded-2xl bg-[var(--surface-secondary)] border border-[var(--border)] shadow-xl shadow-[color-mix(in_srgb,var(--signal)_10%,transparent)]">
            <MetaRadarLogo size={42} />
          </div>
        </div>

        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-[var(--surface)] border border-[var(--border)] shadow-md mb-3 backdrop-blur-md">
          <span className="w-2 h-2 rounded-full bg-[var(--signal)] animate-pulse" />
          <span className="text-[11px] font-semibold tracking-wide text-[var(--muted-foreground)]">
            Novo Nordisk GBS Hackathon 2026
          </span>
          <span className="badge badge-critical text-[9px] py-0 px-1.5 font-mono font-bold">
            v5.1 Live
          </span>
        </div>

        <h1 className="text-3xl sm:text-4xl font-extrabold tracking-tight text-[var(--foreground)] mb-2">
          MetaRadar <span className="text-[var(--signal)]">Haemophilia</span>
        </h1>
        <p className="text-xs sm:text-sm text-[var(--muted-foreground)] max-w-lg leading-relaxed">
          Autonomous multi-source intelligence radar & cross-functional decision governance for haemophilia therapies
        </p>
      </div>

      {/* Role Quick-Select Grid */}
      <div className="relative z-10 w-full max-w-4xl mb-7">
        <div className="flex items-center justify-between px-1 mb-2.5">
          <div className="flex items-center gap-1.5 text-[10px] font-bold text-[var(--muted-foreground)] uppercase tracking-wider">
            <Sparkles className="w-3 h-3 text-[var(--signal)]" />
            <span>Select Stakeholder Role (Zero-Friction Auto-Fill)</span>
          </div>
          <span className="text-[10px] text-[var(--muted-foreground)] font-mono hidden sm:inline">
            Click pill to auto-fill credentials
          </span>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-2">
          {PERSONAS.map((p) => {
            const isSelected = selectedPersona.id === p.id
            return (
              <button
                key={p.id}
                type="button"
                onClick={() => selectPersona(p)}
                onMouseEnter={() => setSelectedPersona(p)}
                className={`flex flex-col items-start p-2.5 rounded-lg border text-left transition-all duration-200 ${
                  isSelected
                    ? 'bg-[color-mix(in_srgb,var(--signal)_14%,var(--surface-elevated))] border-[var(--border-selected)] shadow-md shadow-[color-mix(in_srgb,var(--signal)_15%,transparent)] scale-[1.02]'
                    : 'bg-[var(--surface)] border-[var(--border)] text-[var(--muted-foreground)] hover:text-[var(--foreground)] hover:bg-[color-mix(in_srgb,var(--signal)_6%,var(--surface))]'
                }`}
              >
                <div className="flex items-center justify-between w-full mb-1">
                  <span
                    className="w-2 h-2 rounded-full"
                    style={{
                      backgroundColor: p.dotColor,
                      boxShadow: isSelected ? `0 0 8px ${p.dotColor}` : 'none',
                    }}
                  />
                  {isSelected && <CheckCircle2 className="w-3 h-3 text-[var(--signal)]" />}
                </div>
                <span className="text-[11px] font-bold text-[var(--foreground)] line-clamp-1 leading-tight">{p.label}</span>
                <span className="text-[10px] text-[var(--muted-foreground)] line-clamp-1 mt-0.5">{p.name.split(' ')[0]}</span>
              </button>
            )
          })}
        </div>
      </div>

      {/* Main Login Deck: 3D Tilt Card + Credential Form */}
      <div className="relative z-10 w-full max-w-4xl grid grid-cols-1 lg:grid-cols-12 gap-7 items-center">
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
          <p className="mt-2.5 text-[10px] text-[var(--muted-foreground)] font-mono text-center">
            Move cursor over card for 3D holographic tilt
          </p>
        </div>

        {/* Right Column: Sign In Card */}
        <div className="lg:col-span-7">
          <div className="panel bg-[var(--surface)] border border-[var(--border)] rounded-[var(--radius-lg)] p-6 sm:p-7 shadow-2xl backdrop-blur-xl">
            <div className="flex items-center justify-between mb-5 pb-3 border-b border-[var(--border)]">
              <div>
                <h2 className="text-base font-bold text-[var(--foreground)] tracking-tight">Enterprise Sign In</h2>
                <p className="text-[11px] text-[var(--muted-foreground)]">Authenticated RBAC Session</p>
              </div>
              <div className="badge badge-neutral flex items-center gap-1 text-[10px] py-1 px-2">
                <Shield className="w-3 h-3 text-[var(--signal)]" />
                <span>RBAC v5.1</span>
              </div>
            </div>

            {errorMessage && (
              <div className="flex items-center gap-2 p-2.5 mb-4 rounded-lg bg-[color-mix(in_srgb,var(--critical)_12%,var(--surface))] border border-[var(--critical)] text-[var(--critical)] text-xs">
                <AlertCircle className="w-4 h-4 shrink-0 text-[var(--critical)]" />
                <span>{errorMessage}</span>
              </div>
            )}

            {justAutofilled && (
              <div className="flex items-center gap-2 p-2.5 mb-4 rounded-lg bg-[color-mix(in_srgb,var(--signal)_12%,var(--surface))] border border-[var(--border-selected)] text-[var(--foreground)] text-xs transition-opacity duration-500">
                <CheckCircle2 className="w-4 h-4 shrink-0 text-[var(--signal)]" />
                <span>Auto-filled verified credentials for <strong>{selectedPersona.name}</strong></span>
              </div>
            )}

            <form onSubmit={handleSubmit} className="space-y-3.5">
              <div>
                <label className="block text-[10px] font-bold text-[var(--muted-foreground)] uppercase tracking-wider mb-1">
                  Email Address
                </label>
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="name@metaradar.demo"
                  required
                  className="w-full px-3 py-2 rounded-lg bg-[var(--surface-secondary)] border border-[var(--border)] text-[var(--foreground)] placeholder-[var(--muted-foreground)] text-xs focus:outline-none focus:border-[var(--signal)] focus:ring-1 focus:ring-[var(--signal)] transition-all font-mono"
                />
              </div>

              <div>
                <div className="flex items-center justify-between mb-1">
                  <label className="block text-[10px] font-bold text-[var(--muted-foreground)] uppercase tracking-wider">
                    Password
                  </label>
                  <span className="text-[10px] text-[var(--muted-foreground)] font-mono">
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
                    className="w-full px-3 py-2 pr-9 rounded-lg bg-[var(--surface-secondary)] border border-[var(--border)] text-[var(--foreground)] placeholder-[var(--muted-foreground)] text-xs focus:outline-none focus:border-[var(--signal)] focus:ring-1 focus:ring-[var(--signal)] transition-all font-mono"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-2.5 top-1/2 -translate-y-1/2 text-[var(--muted-foreground)] hover:text-[var(--foreground)] transition-colors"
                  >
                    {showPassword ? <EyeOff className="w-3.5 h-3.5" /> : <Eye className="w-3.5 h-3.5" />}
                  </button>
                </div>
              </div>

              <div className="pt-2">
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="w-full flex items-center justify-center gap-2 px-4 py-2.5 rounded-lg bg-gradient-to-r from-[var(--primary)] to-[var(--signal)] hover:opacity-95 text-white font-bold text-xs shadow-md shadow-[color-mix(in_srgb,var(--signal)_25%,transparent)] transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed hover:scale-[1.01] active:scale-[0.99]"
                >
                  {isSubmitting ? (
                    <>
                      <Loader2 className="w-3.5 h-3.5 animate-spin" />
                      <span>Authenticating Persona...</span>
                    </>
                  ) : (
                    <>
                      <span>Sign In as {selectedPersona.label}</span>
                      <ArrowRight className="w-3.5 h-3.5" />
                    </>
                  )}
                </button>
              </div>
            </form>

            <div className="mt-5 pt-3.5 border-t border-[var(--border)] text-center">
              <p className="text-[10px] text-[var(--muted-foreground)]">
                Novo Nordisk Hackathon evaluation mode • Deterministic JWT session & append-only audit trail
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

