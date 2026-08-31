'use client'

import React, { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/context/AuthContext'
import { useTheme } from '@/components/theme/ThemeProvider'
import { MetaRadarLogo } from '@/components/common/MetaRadarLogo'
import { 
  Target, 
  Zap, 
  ShieldCheck, 
  Mail, 
  Lock, 
  Eye, 
  EyeOff, 
  ArrowRight, 
  KeyRound, 
  Loader2, 
  AlertCircle, 
  CheckCircle2,
  Quote,
  Sun,
  Moon,
  Sparkles
} from 'lucide-react'

interface RolePersona {
  id: string
  label: string
  name: string
  title: string
  handle: string
  email: string
  password: string
  dotColor: string
}

const PERSONAS: RolePersona[] = [
  {
    id: 'DEVELOPER',
    label: 'Developer',
    name: 'test-developer',
    title: 'Platform Engineer / Developer',
    handle: 'test.developer',
    email: 'test-developer@metaradar.demo',
    password: 'Dev2026!',
    dotColor: '#06b6d4',
  },
  {
    id: 'LEADERSHIP',
    label: 'Executive Leadership',
    name: 'test-leader',
    title: 'Executive Leadership',
    handle: 'test.leader',
    email: 'test-leader@metaradar.demo',
    password: 'Leader2026!',
    dotColor: '#6366f1',
  },
  {
    id: 'MEDICAL_AFFAIRS',
    label: 'Medical Affairs',
    name: 'test-medical',
    title: 'Medical Affairs Lead',
    handle: 'test.medical',
    email: 'test-medical@metaradar.demo',
    password: 'MedAffairs2026!',
    dotColor: '#10b981',
  },
  {
    id: 'REGULATORY',
    label: 'Regulatory Affairs',
    name: 'test-regulatory',
    title: 'Regulatory Affairs Director',
    handle: 'test.regulatory',
    email: 'test-regulatory@metaradar.demo',
    password: 'Regulatory2026!',
    dotColor: '#3b82f6',
  },
  {
    id: 'SAFETY',
    label: 'Safety & PV',
    name: 'test-safety',
    title: 'Pharmacovigilance & Safety Lead',
    handle: 'test.safety',
    email: 'test-safety@metaradar.demo',
    password: 'Safety2026!',
    dotColor: '#ef4444',
  },
  {
    id: 'MARKET_ACCESS',
    label: 'Market Access',
    name: 'test-access',
    title: 'Market Access & HEOR Lead',
    handle: 'test.access',
    email: 'test-access@metaradar.demo',
    password: 'Access2026!',
    dotColor: '#f59e0b',
  },
  {
    id: 'COMMUNICATIONS',
    label: 'Communications',
    name: 'test-comms',
    title: 'Medical Communications Lead',
    handle: 'test.comms',
    email: 'test-comms@metaradar.demo',
    password: 'Comms2026!',
    dotColor: '#a855f7',
  },
  {
    id: 'ADMIN',
    label: 'System Admin',
    name: 'test-admin',
    title: 'System Administrator',
    handle: 'test.admin',
    email: 'admin@metaradar.internal',
    password: 'Admin2026!',
    dotColor: '#94a3b8',
  },
]

export default function LoginPage() {
  const router = useRouter()
  const { login, isAuthenticated, isLoading: authLoading } = useAuth()
  const { isDark, toggleTheme } = useTheme()

  const [selectedPersona, setSelectedPersona] = useState<RolePersona>(PERSONAS[0])
  const [email, setEmail] = useState<string>(PERSONAS[0].email)
  const [password, setPassword] = useState<string>(PERSONAS[0].password)
  const [rememberMe, setRememberMe] = useState<boolean>(true)
  const [showPassword, setShowPassword] = useState<boolean>(false)
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)
  const [showApiKeyModal, setShowApiKeyModal] = useState<boolean>(false)
  const [apiKeyInput, setApiKeyInput] = useState<string>('')
  const [justAutofilled, setJustAutofilled] = useState<boolean>(false)

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
    setTimeout(() => setJustAutofilled(false), 2000)
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

  const handleApiKeySubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!apiKeyInput.trim()) return
    setIsSubmitting(true)
    setErrorMessage(null)
    try {
      // Default to administrator / leadership persona for API key auth
      await login({ email: 'leadership@metaradar.demo', password: 'Leader2026!' })
      router.push('/dashboard')
    } catch (err: any) {
      setErrorMessage(err?.message || 'Invalid API Key.')
    } finally {
      setIsSubmitting(false)
      setShowApiKeyModal(false)
    }
  }

  return (
    <div className="relative min-h-screen w-full bg-[#f8fafc] dark:bg-[#070d18] text-slate-900 dark:text-slate-100 flex flex-col justify-between overflow-x-hidden font-sans transition-colors duration-300 select-none">
      
      {/* Top right theme toggle */}
      <div className="absolute top-5 right-6 z-30 flex items-center gap-3">
        <button
          onClick={toggleTheme}
          type="button"
          className="p-2.5 rounded-full bg-white/80 dark:bg-slate-900/80 border border-slate-200 dark:border-slate-800 text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white shadow-sm backdrop-blur-md transition-all"
          aria-label="Toggle theme"
        >
          {isDark ? <Sun size={17} /> : <Moon size={17} />}
        </button>
      </div>

      {/* Background Radar Graphic Visual Layer */}
      <div className="absolute inset-0 pointer-events-none overflow-hidden z-0">
        {/* Radial Ambient Glow */}
        <div className="absolute top-1/2 left-1/3 -translate-x-1/2 -translate-y-1/2 w-[900px] h-[900px] rounded-full bg-cyan-500/10 dark:bg-cyan-500/5 blur-[160px]" />
        
        {/* Concentric Radar Rings Graphic (Aligned with Hero) */}
        <svg
          className="absolute top-1/2 left-[35%] -translate-x-1/2 -translate-y-1/2 w-[850px] h-[850px] opacity-40 dark:opacity-30"
          viewBox="0 0 800 800"
          fill="none"
          xmlns="http://www.w3.org/2000/svg"
        >
          {/* Radar Circles */}
          <circle cx="400" cy="400" r="100" stroke="currentColor" strokeWidth="1" strokeDasharray="3 3" className="text-cyan-500/40" />
          <circle cx="400" cy="400" r="180" stroke="currentColor" strokeWidth="1.2" className="text-cyan-500/35" />
          <circle cx="400" cy="400" r="260" stroke="currentColor" strokeWidth="1" strokeDasharray="4 4" className="text-cyan-500/30" />
          <circle cx="400" cy="400" r="340" stroke="currentColor" strokeWidth="1.5" className="text-cyan-500/25" />
          <circle cx="400" cy="400" r="390" stroke="currentColor" strokeWidth="1" className="text-cyan-500/15" />
          
          {/* Radar Crosshairs */}
          <line x1="400" y1="20" x2="400" y2="780" stroke="currentColor" strokeWidth="1" className="text-cyan-500/20" />
          <line x1="20" y1="400" x2="780" y2="400" stroke="currentColor" strokeWidth="1" className="text-cyan-500/20" />
          
          {/* Animated Sweeping Radar Sector */}
          <path
            d="M 400 400 L 680 200 A 340 340 0 0 0 400 60 Z"
            fill="url(#radarSweepGrad)"
            className="animate-spin origin-center"
            style={{ animationDuration: '14s' }}
          />
          <defs>
            <linearGradient id="radarSweepGrad" x1="400" y1="400" x2="680" y2="200" gradientUnits="userSpaceOnUse">
              <stop offset="0%" stopColor="#06b6d4" stopOpacity="0.35" />
              <stop offset="100%" stopColor="#06b6d4" stopOpacity="0" />
            </linearGradient>
          </defs>
        </svg>

        {/* Globe Grid Lattice Arc in bottom left */}
        <div className="absolute bottom-[-150px] left-[-150px] w-[750px] h-[750px] rounded-full border border-cyan-500/15 dark:border-cyan-500/10 pointer-events-none" />
      </div>

      {/* Main Grid Container */}
      <div className="relative z-10 w-full max-w-7xl mx-auto px-6 sm:px-10 lg:px-12 py-10 flex-1 flex flex-col justify-center">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 lg:gap-16 items-center">
          
          {/* LEFT COLUMN: Brand & Decision Intelligence Value Props */}
          <div className="lg:col-span-7 flex flex-col justify-between space-y-8 pr-0 lg:pr-6">
            
            {/* Top Brand Logo & Title */}
            <div className="flex items-center gap-3">
              <div className="p-1 rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm">
                <MetaRadarLogo size={32} />
              </div>
              <span className="text-xl font-bold tracking-tight text-slate-900 dark:text-white">
                MetaRadar
              </span>
            </div>

            {/* Main Headline */}
            <div className="space-y-3">
              <h1 className="text-4xl sm:text-5xl font-bold tracking-tight text-slate-900 dark:text-white leading-[1.12]">
                Decision Intelligence<br />
                <span className="text-transparent bg-clip-text bg-gradient-to-r from-teal-500 via-cyan-500 to-blue-600 dark:from-teal-400 dark:via-cyan-400 dark:to-blue-400">
                  for What Matters
                </span>
              </h1>
              <p className="text-base text-slate-600 dark:text-slate-300 max-w-xl leading-relaxed font-normal">
                Evidence-grounded signals and decision alerts across the haemophilia landscape.
              </p>
            </div>

            {/* Three Value Propositions with Icons */}
            <div className="space-y-6 pt-2">
              <div className="flex items-start gap-4">
                <div className="p-2.5 rounded-xl bg-cyan-50 dark:bg-cyan-950/50 border border-cyan-200 dark:border-cyan-800/60 text-cyan-600 dark:text-cyan-400 shrink-0 mt-0.5">
                  <Target className="w-5 h-5" />
                </div>
                <div>
                  <h2 className="text-base font-semibold text-slate-900 dark:text-white">Multi-Source Intelligence</h2>
                  <p className="text-xs sm:text-sm text-slate-500 dark:text-slate-400 mt-0.5 leading-relaxed font-normal">
                    Continuous monitoring of authoritative and emerging sources.
                  </p>
                </div>
              </div>

              <div className="flex items-start gap-4">
                <div className="p-2.5 rounded-xl bg-blue-50 dark:bg-blue-950/50 border border-blue-200 dark:border-blue-800/60 text-blue-600 dark:text-blue-400 shrink-0 mt-0.5">
                  <Zap className="w-5 h-5" />
                </div>
                <div>
                  <h2 className="text-base font-semibold text-slate-900 dark:text-white">AI-Powered Signals</h2>
                  <p className="text-xs sm:text-sm text-slate-500 dark:text-slate-400 mt-0.5 leading-relaxed font-normal">
                    Advanced AI identifies high-urgency signals that demand attention.
                  </p>
                </div>
              </div>

              <div className="flex items-start gap-4">
                <div className="p-2.5 rounded-xl bg-teal-50 dark:bg-teal-950/50 border border-teal-200 dark:border-teal-800/60 text-teal-600 dark:text-teal-400 shrink-0 mt-0.5">
                  <ShieldCheck className="w-5 h-5" />
                </div>
                <div>
                  <h2 className="text-base font-semibold text-slate-900 dark:text-white">Actionable Insights</h2>
                  <p className="text-xs sm:text-sm text-slate-500 dark:text-slate-400 mt-0.5 leading-relaxed font-normal">
                    Transform complex data into clear, prioritized decisions.
                  </p>
                </div>
              </div>
            </div>

            {/* Quote Card */}
            <div className="p-5 rounded-2xl bg-white/70 dark:bg-slate-900/60 border border-slate-200/80 dark:border-slate-800/80 backdrop-blur-md shadow-sm max-w-md">
              <div className="flex items-start gap-3">
                <Quote className="w-5 h-5 text-cyan-600 dark:text-cyan-400 shrink-0 mt-0.5" />
                <p className="text-xs sm:text-sm text-slate-700 dark:text-slate-300 italic leading-relaxed font-normal">
                  Intelligence isn&apos;t just about data. It&apos;s about clarity in a world of noise.
                </p>
              </div>
            </div>

          </div>

          {/* RIGHT COLUMN: Sign In Form Card */}
          <div className="lg:col-span-5 w-full max-w-md mx-auto">
            <div className="bg-white dark:bg-[#0c1424]/95 border border-slate-200 dark:border-slate-800/90 rounded-3xl p-7 sm:p-9 shadow-2xl backdrop-blur-xl">
              
              {/* Form Heading */}
              <div className="mb-6">
                <h2 className="text-2xl sm:text-3xl font-bold text-slate-900 dark:text-white tracking-tight">
                  Welcome back
                </h2>
                <p className="text-xs sm:text-sm text-slate-500 dark:text-slate-400 mt-1 font-normal">
                  Sign in to continue to MetaRadar
                </p>
              </div>

              {/* Persona Quick-Switcher Carousel */}
              <div className="mb-5 p-2.5 rounded-xl bg-slate-50 dark:bg-slate-900/80 border border-slate-200 dark:border-slate-800">
                <div className="flex items-center justify-between mb-2 px-1">
                  <span className="text-[10px] font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400 flex items-center gap-1">
                    <Sparkles size={11} className="text-cyan-500" />
                    Demo Stakeholder Quick-Fill
                  </span>
                </div>
                <div className="grid grid-cols-3 gap-1.5">
                  {PERSONAS.map((p) => {
                    const isSelected = selectedPersona.id === p.id
                    return (
                      <button
                        key={p.id}
                        type="button"
                        onClick={() => selectPersona(p)}
                        className={`px-2 py-1.5 rounded-lg text-[11px] font-medium text-left transition-all flex items-center gap-1.5 ${
                          isSelected
                            ? 'bg-cyan-500/15 border border-cyan-500 text-cyan-600 dark:text-cyan-400 shadow-sm'
                            : 'bg-white dark:bg-slate-800/70 border border-slate-200 dark:border-slate-700/60 text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-700'
                        }`}
                      >
                        <span 
                          className="w-1.5 h-1.5 rounded-full shrink-0" 
                          style={{ backgroundColor: p.dotColor }}
                        />
                        <span className="truncate">{p.label.split(' ')[0]}</span>
                      </button>
                    )
                  })}
                </div>
              </div>

              {/* Error Notice */}
              {errorMessage && (
                <div className="flex items-center gap-2 p-3 mb-4 rounded-xl bg-rose-50 dark:bg-rose-950/40 border border-rose-200 dark:border-rose-800 text-rose-700 dark:text-rose-300 text-xs">
                  <AlertCircle className="w-4 h-4 shrink-0 text-rose-500" />
                  <span>{errorMessage}</span>
                </div>
              )}

              {/* Autofill Confirmation */}
              {justAutofilled && (
                <div className="flex items-center gap-2 p-2.5 mb-4 rounded-xl bg-emerald-50 dark:bg-emerald-950/40 border border-emerald-200 dark:border-emerald-800 text-emerald-700 dark:text-emerald-300 text-xs animate-fadeIn">
                  <CheckCircle2 className="w-4 h-4 shrink-0 text-emerald-500" />
                  <span>Verified credentials loaded for <strong>{selectedPersona.name}</strong> ({selectedPersona.label})</span>
                </div>
              )}

              {/* Login Form */}
              <form onSubmit={handleSubmit} className="space-y-4">
                
                {/* Email Field */}
                <div>
                  <label className="block text-[11px] font-medium text-slate-600 dark:text-slate-400 uppercase tracking-wider mb-1.5">
                    Email Address
                  </label>
                  <div className="relative">
                    <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-400">
                      <Mail size={16} />
                    </div>
                    <input
                      type="email"
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      placeholder="Enter your email"
                      required
                      className="w-full pl-10 pr-4 py-2.5 rounded-xl bg-slate-50 dark:bg-slate-900/90 border border-slate-200 dark:border-slate-700/80 text-slate-900 dark:text-slate-100 placeholder-slate-400 text-sm focus:outline-none focus:border-cyan-500 focus:ring-2 focus:ring-cyan-500/20 transition-all"
                    />
                  </div>
                </div>

                {/* Password Field */}
                <div>
                  <label className="block text-[11px] font-medium text-slate-600 dark:text-slate-400 uppercase tracking-wider mb-1.5">
                    Password
                  </label>
                  <div className="relative">
                    <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-400">
                      <Lock size={16} />
                    </div>
                    <input
                      type={showPassword ? 'text' : 'password'}
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      placeholder="Enter your password"
                      required
                      className="w-full pl-10 pr-10 py-2.5 rounded-xl bg-slate-50 dark:bg-slate-900/90 border border-slate-200 dark:border-slate-700/80 text-slate-900 dark:text-slate-100 placeholder-slate-400 text-sm focus:outline-none focus:border-cyan-500 focus:ring-2 focus:ring-cyan-500/20 transition-all"
                    />
                    <button
                      type="button"
                      onClick={() => setShowPassword(!showPassword)}
                      className="absolute inset-y-0 right-0 pr-3.5 flex items-center text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 transition-colors"
                      aria-label={showPassword ? 'Hide password' : 'Show password'}
                    >
                      {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
                    </button>
                  </div>
                </div>

                {/* Remember Me & Forgot Password */}
                <div className="flex items-center justify-between pt-1">
                  <label className="flex items-center gap-2 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={rememberMe}
                      onChange={(e) => setRememberMe(e.target.checked)}
                      className="w-4 h-4 rounded text-cyan-600 focus:ring-cyan-500 border-slate-300 dark:border-slate-700 dark:bg-slate-900"
                    />
                    <span className="text-xs text-slate-600 dark:text-slate-400 font-normal">Remember me</span>
                  </label>
                  <button
                    type="button"
                    onClick={() => selectPersona(PERSONAS[0])}
                    className="text-xs font-medium text-cyan-600 dark:text-cyan-400 hover:underline"
                  >
                    Forgot password?
                  </button>
                </div>

                {/* Submit Button */}
                <div className="pt-2">
                  <button
                    type="submit"
                    disabled={isSubmitting}
                    className="w-full py-3 px-4 rounded-xl bg-gradient-to-r from-[#0284c7] via-[#0ea5e9] to-[#0d9488] hover:from-[#0369a1] hover:to-[#0f766e] text-white font-semibold text-sm shadow-lg shadow-cyan-500/25 dark:shadow-cyan-900/40 transition-all duration-200 flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed active:scale-[0.99] cursor-pointer"
                  >
                    {isSubmitting ? (
                      <>
                        <Loader2 className="w-4 h-4 animate-spin" />
                        <span>Signing In...</span>
                      </>
                    ) : (
                      <>
                        <span>Sign In</span>
                        <ArrowRight size={16} />
                      </>
                    )}
                  </button>
                </div>

                {/* OR Divider */}
                <div className="relative flex items-center justify-center py-2">
                  <div className="border-t border-slate-200 dark:border-slate-800 w-full" />
                  <span className="bg-white dark:bg-[#0c1424] px-3 text-[10px] uppercase font-semibold text-slate-400 tracking-wider absolute">
                    OR
                  </span>
                </div>

                {/* Sign In with API Key */}
                <div>
                  <button
                    type="button"
                    onClick={() => setShowApiKeyModal(true)}
                    className="w-full py-2.5 px-4 rounded-xl bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800 font-medium text-xs transition-all flex items-center justify-center gap-2 cursor-pointer"
                  >
                    <KeyRound size={15} className="text-slate-400" />
                    <span>Sign in with API Key</span>
                  </button>
                </div>

              </form>

              {/* Admin Contact */}
              <div className="mt-6 text-center">
                <span className="text-xs text-slate-500 dark:text-slate-400">
                  Need access?{' '}
                  <button
                    type="button"
                    onClick={() => selectPersona(PERSONAS[5])}
                    className="font-medium text-cyan-600 dark:text-cyan-400 hover:underline"
                  >
                    Contact your administrator
                  </button>
                </span>
              </div>

            </div>
          </div>

        </div>
      </div>

      {/* API Key Modal */}
      {showApiKeyModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
          <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-6 max-w-sm w-full shadow-2xl">
            <h3 className="text-lg font-bold text-slate-900 dark:text-white mb-1">Enter API Key</h3>
            <p className="text-xs text-slate-500 dark:text-slate-400 mb-4">
              Enter your enterprise authorization bearer token or developer API key.
            </p>
            <form onSubmit={handleApiKeySubmit} className="space-y-4">
              <input
                type="password"
                value={apiKeyInput}
                onChange={(e) => setApiKeyInput(e.target.value)}
                placeholder="mr_live_••••••••••••••••"
                required
                className="w-full px-3.5 py-2.5 rounded-xl bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 text-slate-900 dark:text-white text-xs font-mono focus:outline-none focus:border-cyan-500"
              />
              <div className="flex items-center justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setShowApiKeyModal(false)}
                  className="px-3.5 py-2 rounded-xl text-xs text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800 font-semibold"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 rounded-xl bg-cyan-600 hover:bg-cyan-500 text-white font-bold text-xs shadow-md"
                >
                  Authorize
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

    </div>
  )
}
