'use client'

import React, { useState, useEffect } from 'react'
import type { CacheClearResponse, SourceRegistryItem } from '@/types/api'
import { clearCache, fetchSourcesHealth } from '@/lib/api'
import { formatError, FormattedError } from '@/lib/errors'
import { SectionTitle, Card, Badge } from '@/components/metaradar'
import { ErrorState } from '../common/ErrorState'
import { useTheme } from '../theme/ThemeProvider'
import { useAuth } from '@/context/AuthContext'
import ProfileCard from '@/components/auth/ProfileCard'
import { 
  Moon, 
  Sun, 
  Key, 
  Database, 
  Server, 
  Cpu, 
  CheckCircle2, 
  Trash2, 
  ShieldCheck, 
  Users, 
  Lock, 
  Layers,
  ArrowRight,
  Radio
} from 'lucide-react'

export interface PersonaConfig {
  id: string
  name: string
  title: string
  handle: string
  email: string
  badgeTone: 'low' | 'medium' | 'high' | 'critical'
  dotColor: string
}

const SETTINGS_ROLE_PERSONAS: Record<string, PersonaConfig> = {
  DEVELOPER: { 
    id: 'DEVELOPER',
    name: 'test-developer', 
    title: 'Platform Engineer / Developer', 
    handle: 'test.developer',
    email: 'test-developer@metaradar.demo',
    badgeTone: 'low',
    dotColor: '#06b6d4'
  },
  LEADERSHIP: { 
    id: 'LEADERSHIP',
    name: 'test-leader', 
    title: 'Executive Leadership', 
    handle: 'test.leader',
    email: 'test-leader@metaradar.demo',
    badgeTone: 'high',
    dotColor: '#6366f1'
  },
  MEDICAL_AFFAIRS: { 
    id: 'MEDICAL_AFFAIRS',
    name: 'test-medical', 
    title: 'Medical Affairs Lead', 
    handle: 'test.medical',
    email: 'test-medical@metaradar.demo',
    badgeTone: 'low',
    dotColor: '#10b981'
  },
  REGULATORY: { 
    id: 'REGULATORY',
    name: 'test-regulatory', 
    title: 'Regulatory Affairs Director', 
    handle: 'test.regulatory',
    email: 'test-regulatory@metaradar.demo',
    badgeTone: 'medium',
    dotColor: '#3b82f6'
  },
  SAFETY: { 
    id: 'SAFETY',
    name: 'test-safety', 
    title: 'Pharmacovigilance & Safety Lead', 
    handle: 'test.safety',
    email: 'test-safety@metaradar.demo',
    badgeTone: 'critical',
    dotColor: '#ef4444'
  },
  MARKET_ACCESS: { 
    id: 'MARKET_ACCESS',
    name: 'test-access', 
    title: 'Market Access & HEOR Lead', 
    handle: 'test.access',
    email: 'test-access@metaradar.demo',
    badgeTone: 'medium',
    dotColor: '#f59e0b'
  },
  COMMUNICATIONS: { 
    id: 'COMMUNICATIONS',
    name: 'test-comms', 
    title: 'Medical Communications Lead', 
    handle: 'test.comms',
    email: 'test-comms@metaradar.demo',
    badgeTone: 'low',
    dotColor: '#a855f7'
  },
  ADMIN: { 
    id: 'ADMIN',
    name: 'test-admin', 
    title: 'System Administrator', 
    handle: 'test.admin',
    email: 'admin@metaradar.internal',
    badgeTone: 'low',
    dotColor: '#94a3b8'
  },
}

export function SettingsWorkspace() {
  const { theme, setTheme } = useTheme()
  const { user, role, logout, demoLogin } = useAuth()
  const [clearing, setClearing] = useState(false)
  const [switchingRole, setSwitchingRole] = useState<string | null>(null)
  const [cacheResult, setCacheResult] = useState<CacheClearResponse | null>(null)
  const [error, setError] = useState<FormattedError | null>(null)
  const [sources, setSources] = useState<SourceRegistryItem[]>([])

  const currentPersona = SETTINGS_ROLE_PERSONAS[role] || SETTINGS_ROLE_PERSONAS['DEVELOPER']

  useEffect(() => {
    fetchSourcesHealth()
      .then((data) => setSources(data))
      .catch(() => {})
  }, [])

  const handleClearCache = async () => {
    setClearing(true)
    setError(null)
    setCacheResult(null)
    try {
      const res = await clearCache()
      setCacheResult(res)
    } catch (err) {
      setError(formatError(err, 'Failed to clear system Redis cache.'))
    } finally {
      setClearing(false)
    }
  }

  const handleSwitchPersona = async (targetRole: string) => {
    if (targetRole === role) return
    setSwitchingRole(targetRole)
    try {
      await demoLogin(targetRole)
    } catch (err) {
      setError(formatError(err, `Failed to switch to persona ${targetRole}`))
    } finally {
      setSwitchingRole(null)
    }
  }

  const newsApiSource = sources.find((s) => s.source_id === 'newsapi')
  const newsApiConfigErr = newsApiSource?.configuration_error_message

  return (
    <>
      <SectionTitle
        eyebrow="Workspace Configuration"
        title="Settings"
        detail="Operational controls, stakeholder persona governance, color themes, cache invalidation, and all data source connector credentials."
      />

      {error && (
        <ErrorState
          title={error.title}
          message={error.message}
          requestId={error.requestId}
          endpoint={error.endpoint}
          statusCode={error.statusCode}
          onRetry={handleClearCache}
        />
      )}

      <div className="grid gap-5 max-w-5xl">
        {/* 1. Active Stakeholder Persona & 3D Interactive Profile Card */}
        <Card className="overflow-hidden">
          <div className="flex flex-col lg:flex-row items-center lg:items-start justify-between gap-6">
            <div className="flex-1 space-y-3 w-full">
              <div className="flex items-center gap-2">
                <ShieldCheck size={18} style={{ color: 'var(--signal)' }} />
                <h3 className="text-sm font-bold text-[var(--foreground)] m-0">
                  Active Stakeholder Identity & Credential
                </h3>
              </div>
              <p className="text-xs text-[var(--muted-foreground)] leading-relaxed m-0">
                Your authenticated persona credentials dictate role-based permissions, governance approval thresholds, and automated Bayesian calibration weights.
              </p>
              
              <div className="space-y-2 pt-2">
                <div className="p-3 rounded-lg border border-[var(--border)] bg-[var(--surface-secondary)] space-y-2 text-xs font-mono">
                  <div className="flex justify-between items-center">
                    <span className="text-[var(--muted-foreground)]">Stakeholder Name:</span>
                    <strong className="text-[var(--foreground)]">{user?.display_name || currentPersona.name}</strong>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-[var(--muted-foreground)]">Assigned Role:</span>
                    <strong className="text-[var(--signal)]">{currentPersona.title}</strong>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-[var(--muted-foreground)]">Account Email:</span>
                    <span className="text-[var(--foreground)] font-semibold">{user?.email || currentPersona.email}</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-[var(--muted-foreground)]">Stakeholder Handle:</span>
                    <strong className="text-[var(--foreground)]">@{currentPersona.handle}</strong>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-[var(--muted-foreground)]">User ID:</span>
                    <span className="text-[var(--muted-foreground)]">{user?.user_id || 'mr_usr_verified'}</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-[var(--muted-foreground)]">Session Security:</span>
                    <span className="text-emerald-500 font-semibold flex items-center gap-1">
                      <Lock size={11} /> Active · Nonce-Signed JWT
                    </span>
                  </div>
                </div>

                <div className="pt-2 flex items-center gap-3">
                  <button
                    type="button"
                    onClick={() => logout()}
                    className="px-4 py-2 rounded-lg text-xs font-bold text-white bg-rose-600 hover:bg-rose-500 transition shadow-sm cursor-pointer inline-flex items-center gap-1.5"
                  >
                    <span>Sign Out</span>
                  </button>
                </div>
              </div>
            </div>

            {/* 3D Holographic Card Display */}
            <div className="shrink-0 flex flex-col items-center">
              <ProfileCard
                name={user?.display_name || currentPersona.name}
                title={currentPersona.title}
                handle={currentPersona.handle}
                email={user?.email || currentPersona.email || `${currentPersona.handle}@metaradar.demo`}
                roleId={role}
                status="Online & Verified"
                contactText="Sign Out"
                onContactClick={() => logout()}
              />
              <span className="text-[11px] text-[var(--muted-foreground)] font-mono mt-3 text-center">
                Interactive 3D Holographic Card
              </span>
            </div>
          </div>
        </Card>

        {/* 2. All Configured Stakeholder Personas & Quick Role Switcher */}
        <Card>
          <div className="flex items-center gap-2 mb-2">
            <Users size={16} style={{ color: 'var(--signal)' }} />
            <h3 className="text-sm font-semibold text-[var(--foreground)] m-0">
              Configured Stakeholder Personas & Role Switcher
            </h3>
          </div>
          <p className="text-xs text-[var(--muted-foreground)] leading-relaxed m-0 mb-4">
            Switch between authenticated demo stakeholder personas instantly to evaluate distinct RBAC permissions, review workflows, and approval thresholds.
          </p>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
            {Object.values(SETTINGS_ROLE_PERSONAS).map((p) => {
              const isActive = p.id === role
              const isSwitching = switchingRole === p.id
              return (
                <div
                  key={p.id}
                  className={`p-3 rounded-lg border transition-all flex flex-col justify-between ${
                    isActive
                      ? 'border-[var(--signal)] bg-[var(--surface-hover)] shadow-xs ring-1 ring-[var(--signal)]'
                      : 'border-[var(--border)] bg-[var(--surface-secondary)] hover:border-[var(--foreground)]/30'
                  }`}
                >
                  <div className="space-y-1.5">
                    <div className="flex items-center justify-between gap-1">
                      <span className="text-xs font-bold text-[var(--foreground)] truncate">{p.name}</span>
                      {isActive ? (
                        <Badge tone="low">ACTIVE</Badge>
                      ) : (
                        <span className="text-[10px] font-mono text-[var(--muted-foreground)]">{p.id}</span>
                      )}
                    </div>
                    <p className="text-[11px] font-medium text-[var(--muted-foreground)] line-clamp-1 m-0">
                      {p.title}
                    </p>
                    <div className="text-[10px] font-mono text-[var(--muted-foreground)] truncate">
                      {p.email}
                    </div>
                  </div>

                  <div className="pt-3">
                    {isActive ? (
                      <div className="text-[11px] font-semibold text-emerald-500 flex items-center gap-1">
                        <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
                        <span>Current Session</span>
                      </div>
                    ) : (
                      <button
                        type="button"
                        onClick={() => handleSwitchPersona(p.id)}
                        disabled={isSwitching}
                        className="w-full px-2.5 py-1.5 rounded text-[11px] font-semibold border border-[var(--border)] bg-[var(--surface)] text-[var(--foreground)] hover:bg-[var(--surface-hover)] hover:border-[var(--signal)] transition flex items-center justify-center gap-1 cursor-pointer disabled:opacity-50"
                      >
                        <span>{isSwitching ? 'Switching...' : 'Switch Persona'}</span>
                        <ArrowRight size={11} />
                      </button>
                    )}
                  </div>
                </div>
              )
            })}
          </div>
        </Card>

        {/* 3. Theme Appearance Management */}
        <Card>
          <div className="flex items-start justify-between gap-4">
            <div>
              <h3 className="text-sm font-semibold text-[var(--foreground)] m-0 mb-1">Interface Appearance</h3>
              <p className="text-xs text-[var(--muted-foreground)] leading-relaxed m-0">
                Select your preferred color theme. Preferences persist across navigation, tabs, and system reloads.
              </p>
            </div>

            <div className="flex gap-2 shrink-0">
              <button
                onClick={() => setTheme('light')}
                className={`px-3 py-1.5 rounded text-xs font-semibold flex items-center gap-1.5 transition border ${
                  theme === 'light'
                    ? 'bg-[var(--foreground)] text-[var(--background)] border-[var(--foreground)]'
                    : 'bg-[var(--surface)] border-[var(--border)] text-[var(--muted-foreground)] hover:text-[var(--foreground)]'
                }`}
              >
                <Sun size={14} />
                <span>Light</span>
              </button>
              <button
                onClick={() => setTheme('dark')}
                className={`px-3 py-1.5 rounded text-xs font-semibold flex items-center gap-1.5 transition border ${
                  theme === 'dark'
                    ? 'bg-[var(--foreground)] text-[var(--background)] border-[var(--foreground)]'
                    : 'bg-[var(--surface)] border-[var(--border)] text-[var(--muted-foreground)] hover:text-[var(--foreground)]'
                }`}
              >
                <Moon size={14} />
                <span>Dark</span>
              </button>
            </div>
          </div>
        </Card>

        {/* 4. Cache Flush Management */}
        <Card>
          <div className="flex items-start justify-between gap-4">
            <div>
              <h3 className="text-sm font-semibold text-[var(--foreground)] m-0 mb-1">Redis Query Cache Management</h3>
              <p className="text-xs text-[var(--muted-foreground)] leading-relaxed m-0 max-w-xl">
                Flushes in-memory and Redis query caches across signal search, vector retrieval, and overview aggregations.
              </p>
            </div>

            <button
              onClick={handleClearCache}
              disabled={clearing}
              className="px-4 py-2 rounded text-xs font-semibold text-white transition disabled:opacity-50 shrink-0 inline-flex items-center gap-1.5 cursor-pointer"
              style={{ background: 'var(--danger)' }}
            >
              <Trash2 size={13} />
              <span>{clearing ? 'Flushing Cache...' : 'Flush Cache'}</span>
            </button>
          </div>

          {cacheResult && (
            <div
              className="p-3 rounded border text-xs font-mono flex items-center justify-between mt-3"
              style={{
                background: 'color-mix(in srgb, var(--success) 8%, var(--surface))',
                borderColor: 'color-mix(in srgb, var(--success) 30%, var(--border))',
                color: 'var(--success)',
              }}
            >
              <span className="flex items-center gap-1.5">
                <CheckCircle2 size={14} /> Cache flushed successfully: {cacheResult.keys_cleared} keys invalidated
              </span>
              <span className="text-[var(--muted-foreground)] text-[11px]">{new Date(cacheResult.flushed_at).toLocaleTimeString()}</span>
            </div>
          )}
        </Card>

        {/* 5. All 8 Registered Source Connectors & API Key Configuration */}
        <Card>
          <div className="flex items-center gap-2 mb-2">
            <Key size={16} style={{ color: 'var(--signal)' }} />
            <h3 className="text-sm font-semibold text-[var(--foreground)] m-0">
              Source Connectors & Feed Configuration (All 8 Ingestion Adapters)
            </h3>
          </div>

          <p className="text-xs text-[var(--muted-foreground)] leading-relaxed m-0 mb-3">
            MetaRadar accesses open biomedical endpoints and regulatory syndication without requiring credentials. Commercial and optional providers can be configured via environment variables.
          </p>

          <div className="grid gap-2.5">
            {/* 1. PubMed */}
            <div
              className="p-3 rounded-lg border border-[var(--border)] flex items-start justify-between gap-3 text-xs bg-[var(--surface-secondary)]"
            >
              <div>
                <div className="flex items-center gap-2 mb-1 flex-wrap">
                  <strong className="text-[var(--foreground)]">NCBI PubMed (E-Utilities)</strong>
                  <span className="text-[10px] font-mono text-[var(--muted-foreground)]">Public Biomedical Literature Endpoint</span>
                  <Badge tone="low">CONFIGURED</Badge>
                </div>
                <p className="text-[var(--muted-foreground)] text-[11px] m-0">
                  Standard public E-Utilities API; no API key required for low-cadence queries.
                </p>
              </div>
              <a
                href="https://www.ncbi.nlm.nih.gov/home/about/"
                target="_blank"
                rel="noreferrer noopener"
                className="text-link text-[11px] shrink-0"
              >
                Docs ↗
              </a>
            </div>

            {/* 2. ClinicalTrials */}
            <div
              className="p-3 rounded-lg border border-[var(--border)] flex items-start justify-between gap-3 text-xs bg-[var(--surface-secondary)]"
            >
              <div>
                <div className="flex items-center gap-2 mb-1 flex-wrap">
                  <strong className="text-[var(--foreground)]">ClinicalTrials.gov (API v2)</strong>
                  <span className="text-[10px] font-mono text-[var(--muted-foreground)]">Public Clinical Studies Registry</span>
                  <Badge tone="low">CONFIGURED</Badge>
                </div>
                <p className="text-[var(--muted-foreground)] text-[11px] m-0">
                  Open public REST API v2; no API key required.
                </p>
              </div>
              <a
                href="https://clinicaltrials.gov/data-api/about-api"
                target="_blank"
                rel="noreferrer noopener"
                className="text-link text-[11px] shrink-0"
              >
                Docs ↗
              </a>
            </div>

            {/* 3. OpenFDA */}
            <div
              className="p-3 rounded-lg border border-[var(--border)] flex items-start justify-between gap-3 text-xs bg-[var(--surface-secondary)]"
            >
              <div>
                <div className="flex items-center gap-2 mb-1 flex-wrap">
                  <strong className="text-[var(--foreground)]">OpenFDA Drug Adverse & Labeling</strong>
                  <span className="text-[10px] font-mono text-[var(--muted-foreground)]">Public Regulatory Endpoint</span>
                  <Badge tone="low">CONFIGURED</Badge>
                </div>
                <p className="text-[var(--muted-foreground)] text-[11px] m-0">
                  Open public FDA direct JSON data; no API key required.
                </p>
              </div>
              <a
                href="https://open.fda.gov/apis/"
                target="_blank"
                rel="noreferrer noopener"
                className="text-link text-[11px] shrink-0"
              >
                Docs ↗
              </a>
            </div>

            {/* 4. EMA RSS */}
            <div
              className="p-3 rounded-lg border border-[var(--border)] flex items-start justify-between gap-3 text-xs bg-[var(--surface-secondary)]"
            >
              <div>
                <div className="flex items-center gap-2 mb-1 flex-wrap">
                  <strong className="text-[var(--foreground)]">EMA Decision Feeds (RSS)</strong>
                  <span className="text-[10px] font-mono text-[var(--muted-foreground)]">European Medicines Agency Syndication</span>
                  <Badge tone="low">CONFIGURED</Badge>
                </div>
                <p className="text-[var(--muted-foreground)] text-[11px] m-0">
                  Public XML syndication; no authentication required.
                </p>
              </div>
              <a
                href="https://www.ema.europa.eu/"
                target="_blank"
                rel="noreferrer noopener"
                className="text-link text-[11px] shrink-0"
              >
                Docs ↗
              </a>
            </div>

            {/* 5. NewsAPI */}
            <div
              className="p-3 rounded-lg border border-[var(--border)] flex items-start justify-between gap-3 text-xs bg-[var(--surface-secondary)]"
            >
              <div>
                <div className="flex items-center gap-2 mb-1 flex-wrap">
                  <strong className="text-[var(--foreground)]">NewsAPI (Biomedical Commercial News)</strong>
                  <span className="text-[10px] font-mono text-[var(--muted-foreground)]">Commercial News Feed</span>
                  {newsApiConfigErr ? (
                    <Badge tone="critical">CONFIGURATION_ERROR</Badge>
                  ) : (
                    <Badge tone="low">CONFIGURED</Badge>
                  )}
                </div>
                <p className="text-[var(--muted-foreground)] text-[11px] m-0">
                  {newsApiConfigErr || 'NEWSAPI_KEY configured in environment. Live commercial news ingestion enabled.'}
                </p>
              </div>
              <a
                href="https://newsapi.org/register"
                target="_blank"
                rel="noreferrer noopener"
                className="text-link text-[11px] shrink-0"
              >
                Get Key ↗
              </a>
            </div>

            {/* 6. BioPharma Dive */}
            <div
              className="p-3 rounded-lg border border-[var(--border)] flex items-start justify-between gap-3 text-xs bg-[var(--surface-secondary)]"
            >
              <div>
                <div className="flex items-center gap-2 mb-1 flex-wrap">
                  <strong className="text-[var(--foreground)]">BioPharma Dive (RSS Intelligence Feed)</strong>
                  <span className="text-[10px] font-mono text-[var(--muted-foreground)]">Commercial & Pipeline News Feed</span>
                  <Badge tone="low">CONFIGURED</Badge>
                </div>
                <p className="text-[var(--muted-foreground)] text-[11px] m-0">
                  Real-time pipeline, commercial M&A, and clinical development RSS feed; no authentication required.
                </p>
              </div>
              <a
                href="https://www.biopharmadive.com/"
                target="_blank"
                rel="noreferrer noopener"
                className="text-link text-[11px] shrink-0"
              >
                Feed ↗
              </a>
            </div>

            {/* 7. Fierce Pharma */}
            <div
              className="p-3 rounded-lg border border-[var(--border)] flex items-start justify-between gap-3 text-xs bg-[var(--surface-secondary)]"
            >
              <div>
                <div className="flex items-center gap-2 mb-1 flex-wrap">
                  <strong className="text-[var(--foreground)]">Fierce Pharma (RSS Global Biopharma Feed)</strong>
                  <span className="text-[10px] font-mono text-[var(--muted-foreground)]">Global Pharma & Regulatory News</span>
                  <Badge tone="low">CONFIGURED</Badge>
                </div>
                <p className="text-[var(--muted-foreground)] text-[11px] m-0">
                  Industry regulatory filings, market dynamics, and competitive updates RSS syndication; open feed.
                </p>
              </div>
              <a
                href="https://www.fiercepharma.com/"
                target="_blank"
                rel="noreferrer noopener"
                className="text-link text-[11px] shrink-0"
              >
                Feed ↗
              </a>
            </div>

            {/* 8. ETHealthworld / ET Pharma */}
            <div
              className="p-3 rounded-lg border border-[var(--border)] flex items-start justify-between gap-3 text-xs bg-[var(--surface-secondary)]"
            >
              <div>
                <div className="flex items-center gap-2 mb-1 flex-wrap">
                  <strong className="text-[var(--foreground)]">ETHealthworld / ET Pharma (RSS Healthcare Feed)</strong>
                  <span className="text-[10px] font-mono text-[var(--muted-foreground)]">APAC & Global Regulatory Feed</span>
                  <Badge tone="low">CONFIGURED</Badge>
                </div>
                <p className="text-[var(--muted-foreground)] text-[11px] m-0">
                  Global and emerging market regulatory and clinical updates RSS syndication; open feed.
                </p>
              </div>
              <a
                href="https://health.economictimes.indiatimes.com/"
                target="_blank"
                rel="noreferrer noopener"
                className="text-link text-[11px] shrink-0"
              >
                Feed ↗
              </a>
            </div>
          </div>
        </Card>

        {/* 6. Environment & Architecture Configuration */}
        <Card>
          <div className="flex items-center gap-2 mb-3">
            <Layers size={16} style={{ color: 'var(--signal)' }} />
            <h3 className="text-sm font-semibold text-[var(--foreground)] m-0">
              Architecture & Reasoning Pipeline Configuration
            </h3>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3 text-xs font-mono">
            <div className="p-3 rounded-lg border border-[var(--border)] space-y-1 bg-[var(--surface-secondary)]">
              <div className="text-[var(--muted-foreground)] uppercase text-[10px] font-semibold flex items-center gap-1.5">
                <Database size={12} /> Database Stack
              </div>
              <div className="text-[var(--foreground)] font-semibold">PostgreSQL 16 + pgvector (384-dim)</div>
            </div>

            <div className="p-3 rounded-lg border border-[var(--border)] space-y-1 bg-[var(--surface-secondary)]">
              <div className="text-[var(--muted-foreground)] uppercase text-[10px] font-semibold flex items-center gap-1.5">
                <Server size={12} /> Frontend Framework
              </div>
              <div className="text-[var(--foreground)] font-semibold">Next.js 16 (App Router) + React 19</div>
            </div>

            <div className="p-3 rounded-lg border border-[var(--border)] space-y-1 bg-[var(--surface-secondary)]">
              <div className="text-[var(--muted-foreground)] uppercase text-[10px] font-semibold flex items-center gap-1.5">
                <Server size={12} /> Backend Framework
              </div>
              <div className="text-[var(--foreground)] font-semibold">FastAPI 0.110+ (Async / Structlog)</div>
            </div>

            <div className="p-3 rounded-lg border border-[var(--border)] space-y-1 bg-[var(--surface-secondary)]">
              <div className="text-[var(--muted-foreground)] uppercase text-[10px] font-semibold flex items-center gap-1.5">
                <Cpu size={12} /> Primary LLM Engine
              </div>
              <div className="text-[var(--foreground)] font-semibold">Gemma 3 4B (Ollama / Local)</div>
            </div>

            <div className="p-3 rounded-lg border border-[var(--border)] space-y-1 bg-[var(--surface-secondary)]">
              <div className="text-[var(--muted-foreground)] uppercase text-[10px] font-semibold flex items-center gap-1.5">
                <Cpu size={12} /> Vector Embeddings
              </div>
              <div className="text-[var(--foreground)] font-semibold">all-MiniLM-L6-v2 (384-dim)</div>
            </div>

            <div className="p-3 rounded-lg border border-[var(--border)] space-y-1 bg-[var(--surface-secondary)]">
              <div className="text-[var(--muted-foreground)] uppercase text-[10px] font-semibold flex items-center gap-1.5">
                <ShieldCheck size={12} /> Privacy Scrubber Gate
              </div>
              <div className="text-emerald-500 font-semibold">PII/PHI Sanitization Active</div>
            </div>

            <div className="p-3 rounded-lg border border-[var(--border)] space-y-1 bg-[var(--surface-secondary)]">
              <div className="text-[var(--muted-foreground)] uppercase text-[10px] font-semibold flex items-center gap-1.5">
                <Radio size={12} /> Caching Layer
              </div>
              <div className="text-[var(--foreground)] font-semibold">Redis 7.2 Semantic Cache</div>
            </div>

            <div className="p-3 rounded-lg border border-[var(--border)] space-y-1 bg-[var(--surface-secondary)]">
              <div className="text-[var(--muted-foreground)] uppercase text-[10px] font-semibold flex items-center gap-1.5">
                <Radio size={12} /> Cloud Fallback Gate
              </div>
              <div className="text-[var(--foreground)] font-semibold">xAI Grok-2 (Configurable)</div>
            </div>

            <div className="p-3 rounded-lg border border-[var(--border)] space-y-1 bg-[var(--surface-secondary)]">
              <div className="text-[var(--muted-foreground)] uppercase text-[10px] font-semibold flex items-center gap-1.5">
                <Lock size={12} /> RBAC & Governance
              </div>
              <div className="text-emerald-500 font-semibold">8 Persona Matrix Active</div>
            </div>
          </div>
        </Card>
      </div>
    </>
  )
}
