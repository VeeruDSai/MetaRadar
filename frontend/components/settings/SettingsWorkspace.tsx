'use client'

import React, { useState, useEffect } from 'react'
import type { CacheClearResponse, SourceRegistryItem } from '@/types/api'
import { clearCache, fetchSourcesHealth } from '@/lib/api'
import { formatError, FormattedError } from '@/lib/errors'
import { ErrorState } from '../common/ErrorState'
import { useTheme } from '../theme/ThemeProvider'
import { Moon, Sun, Key, Database, Server, Cpu } from 'lucide-react'

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
    <div className="space-y-6 max-w-4xl mx-auto">
      <div>
        <div className="text-[11px] font-semibold tracking-wider uppercase text-[var(--muted-foreground)] mb-0.5">
          Platform Configuration
        </div>
        <h2 className="text-xl font-bold text-[var(--foreground)]">System Governance & Platform Settings</h2>
        <p className="text-xs text-[var(--muted-foreground)] mt-1">
          Operational controls, color theme management, cache invalidation, and external connector credentials.
        </p>
      </div>

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

      {/* Theme Appearance Management */}
      <div className="rounded-xl border border-[var(--border)] bg-[var(--card)] p-6 space-y-4 shadow-xs">
        <div className="flex items-start justify-between gap-4">
          <div className="space-y-1">
            <h3 className="text-sm font-semibold text-[var(--foreground)]">Interface Appearance</h3>
            <p className="text-xs text-[var(--muted-foreground)] leading-relaxed">
              Select your preferred color theme. Preferences persist across navigation, tabs, and system reloads.
            </p>
          </div>

          <div className="flex gap-2 shrink-0">
            <button
              onClick={() => setTheme('light')}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium border flex items-center gap-1.5 transition ${
                theme === 'light'
                  ? 'bg-blue-600 border-blue-600 text-white shadow-xs'
                  : 'bg-[var(--card)] border-[var(--border)] text-[var(--foreground)] hover:bg-[var(--surface-subtle)]'
              }`}
            >
              <Sun size={14} />
              <span>Light Mode</span>
            </button>
            <button
              onClick={() => setTheme('dark')}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium border flex items-center gap-1.5 transition ${
                theme === 'dark'
                  ? 'bg-blue-600 border-blue-600 text-white shadow-xs'
                  : 'bg-[var(--card)] border-[var(--border)] text-[var(--foreground)] hover:bg-[var(--surface-subtle)]'
              }`}
            >
              <Moon size={14} />
              <span>Dark Mode</span>
            </button>
          </div>
        </div>
      </div>

      {/* Cache Flush Management */}
      <div className="rounded-xl border border-[var(--border)] bg-[var(--card)] p-6 space-y-4 shadow-xs">
        <div className="flex items-start justify-between gap-4">
          <div className="space-y-1">
            <h3 className="text-sm font-semibold text-[var(--foreground)]">Redis Query Cache Management</h3>
            <p className="text-xs text-[var(--muted-foreground)] leading-relaxed max-w-xl">
              Flushes in-memory and Redis query caches across signal search, vector retrieval, and overview aggregations.
            </p>
          </div>

          <button
            onClick={handleClearCache}
            disabled={clearing}
            className="px-4 py-2 rounded-lg bg-red-600 hover:bg-red-700 text-xs font-semibold text-white transition disabled:opacity-50 shrink-0 shadow-xs"
          >
            {clearing ? 'Flushing Cache...' : 'Flush Cache'}
          </button>
        </div>

        {cacheResult && (
          <div className="p-3 rounded-lg bg-[var(--surface-subtle)] border border-[var(--border)] text-xs font-mono text-emerald-600 dark:text-emerald-400 flex items-center justify-between">
            <span>✓ Cache flushed successfully: {cacheResult.keys_cleared} keys invalidated</span>
            <span className="text-[var(--muted-foreground)] text-[11px]">{new Date(cacheResult.flushed_at).toLocaleTimeString()}</span>
          </div>
        )}
      </div>

      {/* Connector Credentials & API Key Governance */}
      <div className="rounded-xl border border-[var(--border)] bg-[var(--card)] p-6 space-y-4 shadow-xs">
        <div className="flex items-center gap-2">
          <Key size={16} className="text-blue-600 dark:text-blue-400" />
          <h3 className="text-sm font-semibold text-[var(--foreground)]">
            Source Connectors & API Key Configuration
          </h3>
        </div>

        <p className="text-xs text-[var(--muted-foreground)] leading-relaxed">
          MetaRadar accesses open biomedical endpoints without requiring credentials. Commercial and optional providers can be configured via environment variables.
        </p>

        <div className="space-y-2.5">
          {/* PubMed */}
          <div className="p-3.5 rounded-lg bg-[var(--surface-subtle)] border border-[var(--border)] flex items-start justify-between gap-3 text-xs">
            <div className="space-y-1">
              <div className="flex items-center gap-2 flex-wrap">
                <span className="font-semibold text-[var(--foreground)]">NCBI PubMed (E-Utilities)</span>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-[var(--surface-muted)] text-[var(--foreground)]">
                  Public Biomedical Endpoint
                </span>
                <span className="text-[10px] font-semibold px-2 py-0.5 rounded border bg-emerald-50 text-emerald-700 border-emerald-200 dark:bg-emerald-950/80 dark:text-emerald-300 dark:border-emerald-800">
                  CONFIGURED
                </span>
              </div>
              <p className="text-[var(--muted-foreground)] text-[11px] leading-relaxed">
                Standard public API; no API key required for low-cadence queries.
              </p>
            </div>
            <a
              href="https://www.ncbi.nlm.nih.gov/home/about/"
              target="_blank"
              rel="noreferrer"
              className="text-blue-600 dark:text-blue-400 hover:underline font-medium text-[11px] shrink-0 inline-flex items-center gap-1"
            >
              <span>Docs</span>
              <span>↗</span>
            </a>
          </div>

          {/* ClinicalTrials */}
          <div className="p-3.5 rounded-lg bg-[var(--surface-subtle)] border border-[var(--border)] flex items-start justify-between gap-3 text-xs">
            <div className="space-y-1">
              <div className="flex items-center gap-2 flex-wrap">
                <span className="font-semibold text-[var(--foreground)]">ClinicalTrials.gov (API v2)</span>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-[var(--surface-muted)] text-[var(--foreground)]">
                  Public Clinical Registry
                </span>
                <span className="text-[10px] font-semibold px-2 py-0.5 rounded border bg-emerald-50 text-emerald-700 border-emerald-200 dark:bg-emerald-950/80 dark:text-emerald-300 dark:border-emerald-800">
                  CONFIGURED
                </span>
              </div>
              <p className="text-[var(--muted-foreground)] text-[11px] leading-relaxed">
                Open public REST API v2; no API key required.
              </p>
            </div>
            <a
              href="https://clinicaltrials.gov/data-api/about-api"
              target="_blank"
              rel="noreferrer"
              className="text-blue-600 dark:text-blue-400 hover:underline font-medium text-[11px] shrink-0 inline-flex items-center gap-1"
            >
              <span>Docs</span>
              <span>↗</span>
            </a>
          </div>

          {/* OpenFDA */}
          <div className="p-3.5 rounded-lg bg-[var(--surface-subtle)] border border-[var(--border)] flex items-start justify-between gap-3 text-xs">
            <div className="space-y-1">
              <div className="flex items-center gap-2 flex-wrap">
                <span className="font-semibold text-[var(--foreground)]">OpenFDA Drug Adverse & Labeling</span>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-[var(--surface-muted)] text-[var(--foreground)]">
                  Public Regulatory Endpoint
                </span>
                <span className="text-[10px] font-semibold px-2 py-0.5 rounded border bg-emerald-50 text-emerald-700 border-emerald-200 dark:bg-emerald-950/80 dark:text-emerald-300 dark:border-emerald-800">
                  CONFIGURED
                </span>
              </div>
              <p className="text-[var(--muted-foreground)] text-[11px] leading-relaxed">
                Open public FDA direct JSON data; no API key required.
              </p>
            </div>
            <a
              href="https://open.fda.gov/apis/"
              target="_blank"
              rel="noreferrer"
              className="text-blue-600 dark:text-blue-400 hover:underline font-medium text-[11px] shrink-0 inline-flex items-center gap-1"
            >
              <span>Docs</span>
              <span>↗</span>
            </a>
          </div>

          {/* EMA RSS */}
          <div className="p-3.5 rounded-lg bg-[var(--surface-subtle)] border border-[var(--border)] flex items-start justify-between gap-3 text-xs">
            <div className="space-y-1">
              <div className="flex items-center gap-2 flex-wrap">
                <span className="font-semibold text-[var(--foreground)]">EMA Decision Feeds (RSS)</span>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-[var(--surface-muted)] text-[var(--foreground)]">
                  Public Syndication
                </span>
                <span className="text-[10px] font-semibold px-2 py-0.5 rounded border bg-emerald-50 text-emerald-700 border-emerald-200 dark:bg-emerald-950/80 dark:text-emerald-300 dark:border-emerald-800">
                  CONFIGURED
                </span>
              </div>
              <p className="text-[var(--muted-foreground)] text-[11px] leading-relaxed">
                Public XML syndication; no authentication required.
              </p>
            </div>
            <a
              href="https://www.ema.europa.eu/"
              target="_blank"
              rel="noreferrer"
              className="text-blue-600 dark:text-blue-400 hover:underline font-medium text-[11px] shrink-0 inline-flex items-center gap-1"
            >
              <span>Docs</span>
              <span>↗</span>
            </a>
          </div>

          {/* NewsAPI */}
          <div className="p-3.5 rounded-lg bg-[var(--surface-subtle)] border border-[var(--border)] flex items-start justify-between gap-3 text-xs">
            <div className="space-y-1">
              <div className="flex items-center gap-2 flex-wrap">
                <span className="font-semibold text-[var(--foreground)]">NewsAPI (Biomedical Commercial News)</span>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-[var(--surface-muted)] text-[var(--foreground)]">
                  Commercial News Feed
                </span>
                {newsApiConfigErr ? (
                  <span className="text-[10px] font-semibold px-2 py-0.5 rounded border bg-rose-50 text-rose-700 border-rose-200 dark:bg-rose-950/80 dark:text-rose-300 dark:border-rose-800">
                    CONFIGURATION_ERROR (required)
                  </span>
                ) : (
                  <span className="text-[10px] font-semibold px-2 py-0.5 rounded border bg-emerald-50 text-emerald-700 border-emerald-200 dark:bg-emerald-950/80 dark:text-emerald-300 dark:border-emerald-800">
                    CONFIGURED
                  </span>
                )}
              </div>
              <p className="text-[var(--muted-foreground)] text-[11px] leading-relaxed">
                {newsApiConfigErr || 'NEWSAPI_KEY configured in .env. Live news ingestion enabled.'}
              </p>
            </div>
            <a
              href="https://newsapi.org/register"
              target="_blank"
              rel="noreferrer"
              className="text-blue-600 dark:text-blue-400 hover:underline font-medium text-[11px] shrink-0 inline-flex items-center gap-1"
            >
              <span>Get Key</span>
              <span>↗</span>
            </a>
          </div>
        </div>
      </div>

      {/* Environment Diagnostics */}
      <div className="rounded-xl border border-[var(--border)] bg-[var(--card)] p-6 space-y-4 shadow-xs">
        <h3 className="text-sm font-semibold text-[var(--foreground)]">Architecture Configuration</h3>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs font-mono">
          <div className="p-3 rounded-lg bg-[var(--surface-subtle)] border border-[var(--border)] space-y-1">
            <div className="text-[var(--muted-foreground)] uppercase text-[10px] font-semibold flex items-center gap-1.5">
              <Database size={12} /> Database Stack
            </div>
            <div className="text-[var(--foreground)] font-semibold">PostgreSQL 16 + pgvector (384-dim)</div>
          </div>
          <div className="p-3 rounded-lg bg-[var(--surface-subtle)] border border-[var(--border)] space-y-1">
            <div className="text-[var(--muted-foreground)] uppercase text-[10px] font-semibold flex items-center gap-1.5">
              <Server size={12} /> Frontend Framework
            </div>
            <div className="text-[var(--foreground)] font-semibold">Next.js 16 (App Router) + React 19</div>
          </div>
          <div className="p-3 rounded-lg bg-[var(--surface-subtle)] border border-[var(--border)] space-y-1">
            <div className="text-[var(--muted-foreground)] uppercase text-[10px] font-semibold flex items-center gap-1.5">
              <Server size={12} /> Backend Framework
            </div>
            <div className="text-[var(--foreground)] font-semibold">FastAPI 0.110+ (Async / Structlog)</div>
          </div>
          <div className="p-3 rounded-lg bg-[var(--surface-subtle)] border border-[var(--border)] space-y-1">
            <div className="text-[var(--muted-foreground)] uppercase text-[10px] font-semibold flex items-center gap-1.5">
              <Cpu size={12} /> Local LLM & Embeddings
            </div>
            <div className="text-[var(--foreground)] font-semibold">Gemma 3 4B + all-MiniLM-L6-v2</div>
          </div>
        </div>
      </div>
    </div>
  )
}
