'use client'

import React, { useState, useEffect } from 'react'
import type { CacheClearResponse, SourceRegistryItem } from '@/types/api'
import { clearCache, fetchSourcesHealth } from '@/lib/api'
import { formatError, FormattedError } from '@/lib/errors'
import { SectionTitle, Card, Badge } from '@/components/metaradar'
import { ErrorState } from '../common/ErrorState'
import { useTheme } from '../theme/ThemeProvider'
import { Moon, Sun, Key, Database, Server, Cpu, CheckCircle2, Trash2 } from 'lucide-react'

export function SettingsWorkspace() {
  const { theme, setTheme } = useTheme()
  const [clearing, setClearing] = useState(false)
  const [cacheResult, setCacheResult] = useState<CacheClearResponse | null>(null)
  const [error, setError] = useState<FormattedError | null>(null)
  const [sources, setSources] = useState<SourceRegistryItem[]>([])

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

  const newsApiSource = sources.find((s) => s.source_id === 'newsapi')
  const newsApiConfigErr = newsApiSource?.configuration_error_message

  return (
    <>
      <SectionTitle
        eyebrow="Workspace Configuration"
        title="Settings"
        detail="Operational controls, color theme management, cache invalidation, and external connector credentials."
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

      <div className="grid gap-4 max-w-4xl">
        {/* Theme Appearance Management */}
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

        {/* Cache Flush Management */}
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
              className="px-4 py-2 rounded text-xs font-semibold text-white transition disabled:opacity-50 shrink-0 inline-flex items-center gap-1.5"
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

        {/* Connector Credentials & API Key Governance */}
        <Card>
          <div className="flex items-center gap-2 mb-2">
            <Key size={16} style={{ color: 'var(--signal)' }} />
            <h3 className="text-sm font-semibold text-[var(--foreground)] m-0">
              Source Connectors & API Key Configuration
            </h3>
          </div>

          <p className="text-xs text-[var(--muted-foreground)] leading-relaxed m-0 mb-3">
            MetaRadar accesses open biomedical endpoints without requiring credentials. Commercial and optional providers can be configured via environment variables.
          </p>

          <div className="grid gap-2.5">
            {/* PubMed */}
            <div
              className="p-3 rounded border border-[var(--border)] flex items-start justify-between gap-3 text-xs"
              style={{ background: 'var(--surface-secondary)' }}
            >
              <div>
                <div className="flex items-center gap-2 mb-1 flex-wrap">
                  <strong className="text-[var(--foreground)]">NCBI PubMed (E-Utilities)</strong>
                  <span className="text-[10px] font-mono text-[var(--muted-foreground)]">Public Biomedical Endpoint</span>
                  <Badge tone="low">CONFIGURED</Badge>
                </div>
                <p className="text-[var(--muted-foreground)] text-[11px] m-0">
                  Standard public API; no API key required for low-cadence queries.
                </p>
              </div>
              <a
                href="https://www.ncbi.nlm.nih.gov/home/about/"
                target="_blank"
                rel="noreferrer noopener"
                className="text-link text-[11px]"
              >
                Docs ↗
              </a>
            </div>

            {/* ClinicalTrials */}
            <div
              className="p-3 rounded border border-[var(--border)] flex items-start justify-between gap-3 text-xs"
              style={{ background: 'var(--surface-secondary)' }}
            >
              <div>
                <div className="flex items-center gap-2 mb-1 flex-wrap">
                  <strong className="text-[var(--foreground)]">ClinicalTrials.gov (API v2)</strong>
                  <span className="text-[10px] font-mono text-[var(--muted-foreground)]">Public Clinical Registry</span>
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
                className="text-link text-[11px]"
              >
                Docs ↗
              </a>
            </div>

            {/* OpenFDA */}
            <div
              className="p-3 rounded border border-[var(--border)] flex items-start justify-between gap-3 text-xs"
              style={{ background: 'var(--surface-secondary)' }}
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
                className="text-link text-[11px]"
              >
                Docs ↗
              </a>
            </div>

            {/* EMA RSS */}
            <div
              className="p-3 rounded border border-[var(--border)] flex items-start justify-between gap-3 text-xs"
              style={{ background: 'var(--surface-secondary)' }}
            >
              <div>
                <div className="flex items-center gap-2 mb-1 flex-wrap">
                  <strong className="text-[var(--foreground)]">EMA Decision Feeds (RSS)</strong>
                  <span className="text-[10px] font-mono text-[var(--muted-foreground)]">Public Syndication</span>
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
                className="text-link text-[11px]"
              >
                Docs ↗
              </a>
            </div>

            {/* NewsAPI */}
            <div
              className="p-3 rounded border border-[var(--border)] flex items-start justify-between gap-3 text-xs"
              style={{ background: 'var(--surface-secondary)' }}
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
                  {newsApiConfigErr || 'NEWSAPI_KEY configured in .env. Live news ingestion enabled.'}
                </p>
              </div>
              <a
                href="https://newsapi.org/register"
                target="_blank"
                rel="noreferrer noopener"
                className="text-link text-[11px]"
              >
                Get Key ↗
              </a>
            </div>
          </div>
        </Card>

        {/* Environment Diagnostics */}
        <Card>
          <h3 className="text-sm font-semibold text-[var(--foreground)] m-0 mb-3">Architecture Configuration</h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs font-mono">
            <div
              className="p-3 rounded border border-[var(--border)] space-y-1"
              style={{ background: 'var(--surface-secondary)' }}
            >
              <div className="text-[var(--muted-foreground)] uppercase text-[10px] font-semibold flex items-center gap-1.5">
                <Database size={12} /> Database Stack
              </div>
              <div className="text-[var(--foreground)] font-semibold">PostgreSQL 16 + pgvector (384-dim)</div>
            </div>
            <div
              className="p-3 rounded border border-[var(--border)] space-y-1"
              style={{ background: 'var(--surface-secondary)' }}
            >
              <div className="text-[var(--muted-foreground)] uppercase text-[10px] font-semibold flex items-center gap-1.5">
                <Server size={12} /> Frontend Framework
              </div>
              <div className="text-[var(--foreground)] font-semibold">Next.js 16 (App Router) + React 19</div>
            </div>
            <div
              className="p-3 rounded border border-[var(--border)] space-y-1"
              style={{ background: 'var(--surface-secondary)' }}
            >
              <div className="text-[var(--muted-foreground)] uppercase text-[10px] font-semibold flex items-center gap-1.5">
                <Server size={12} /> Backend Framework
              </div>
              <div className="text-[var(--foreground)] font-semibold">FastAPI 0.110+ (Async / Structlog)</div>
            </div>
            <div
              className="p-3 rounded border border-[var(--border)] space-y-1"
              style={{ background: 'var(--surface-secondary)' }}
            >
              <div className="text-[var(--muted-foreground)] uppercase text-[10px] font-semibold flex items-center gap-1.5">
                <Cpu size={12} /> Local LLM & Embeddings
              </div>
              <div className="text-[var(--foreground)] font-semibold">Gemma 3 4B + all-MiniLM-L6-v2</div>
            </div>
          </div>
        </Card>
      </div>
    </>
  )
}
