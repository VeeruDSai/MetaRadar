'use client'

import React, { useState } from 'react'
import type { CacheClearResponse } from '@/types/api'
import { clearCache } from '@/lib/api'
import { formatError, FormattedError } from '@/lib/errors'
import { ErrorState } from '../common/ErrorState'
import { useTheme } from '../theme/ThemeProvider'
import { Moon, Sun, Key, ShieldCheck, Database, Server, Cpu } from 'lucide-react'

export function SettingsWorkspace() {
  const { theme, setTheme, isDark } = useTheme()
  const [clearing, setClearing] = useState(false)
  const [cacheResult, setCacheResult] = useState<CacheClearResponse | null>(null)
  const [error, setError] = useState<FormattedError | null>(null)

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

  const apiProviders = [
    {
      name: 'NCBI PubMed (E-Utilities)',
      type: 'Public Biomedical Endpoint',
      status: 'CONFIGURED',
      notes: 'Standard public API; no API key required for low-cadence queries.',
      url: 'https://www.ncbi.nlm.nih.gov/home/about/',
    },
    {
      name: 'ClinicalTrials.gov (API v2)',
      type: 'Public Clinical Registry',
      status: 'CONFIGURED',
      notes: 'Open public REST API v2; no API key required.',
      url: 'https://clinicaltrials.gov/data-api/about-api',
    },
    {
      name: 'OpenFDA Drug Adverse & Labeling',
      type: 'Public Regulatory Endpoint',
      status: 'CONFIGURED',
      notes: 'Open public FDA data; no API key required for base queries.',
      url: 'https://open.fda.gov/apis/',
    },
    {
      name: 'EMA Decision Feeds (RSS)',
      type: 'Public Syndication',
      status: 'CONFIGURED',
      notes: 'Public XML syndication; no authentication required.',
      url: 'https://www.ema.europa.eu/',
    },
    {
      name: 'NewsAPI (Biomedical News)',
      type: 'Commercial News Feed',
      status: 'OPTIONAL',
      notes: 'Requires NEWSAPI_KEY in .env. When unconfigured, public biomedical sources remain fully functional.',
      url: 'https://newsapi.org/register',
    },
    {
      name: 'xAI Grok (Secondary Fallback)',
      type: 'Hosted LLM Fallback',
      status: 'OPTIONAL',
      notes: 'Requires XAI_API_KEY and ENABLE_GROK_FALLBACK=true in .env. Local Gemma is default.',
      url: 'https://x.ai/api',
    },
  ]

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      <div>
        <h1 className="text-xl font-bold text-slate-900 dark:text-slate-100">System Governance & Platform Settings</h1>
        <p className="text-xs text-slate-600 dark:text-slate-400 mt-1">
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
      <div className="rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900/60 p-6 space-y-4 shadow-sm">
        <div className="flex items-start justify-between gap-4">
          <div className="space-y-1">
            <h2 className="text-sm font-semibold text-slate-900 dark:text-slate-200">Interface Appearance</h2>
            <p className="text-xs text-slate-600 dark:text-slate-400 leading-relaxed">
              Select your preferred color theme. Preferences persist across navigation, tabs, and system reloads.
            </p>
          </div>

          <div className="flex gap-2 shrink-0">
            <button
              onClick={() => setTheme('light')}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium border flex items-center gap-1.5 transition ${
                theme === 'light'
                  ? 'bg-blue-600 border-blue-600 text-white shadow-xs'
                  : 'bg-white dark:bg-slate-800 border-slate-200 dark:border-slate-700 text-slate-700 dark:text-slate-300 hover:bg-slate-50'
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
                  : 'bg-white dark:bg-slate-800 border-slate-200 dark:border-slate-700 text-slate-700 dark:text-slate-300 hover:bg-slate-50'
              }`}
            >
              <Moon size={14} />
              <span>Dark Mode</span>
            </button>
          </div>
        </div>
      </div>

      {/* Cache Flush Management */}
      <div className="rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900/60 p-6 space-y-4 shadow-sm">
        <div className="flex items-start justify-between gap-4">
          <div className="space-y-1">
            <h2 className="text-sm font-semibold text-slate-900 dark:text-slate-200">Redis Query Cache Management</h2>
            <p className="text-xs text-slate-600 dark:text-slate-400 leading-relaxed max-w-xl">
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
          <div className="p-3 rounded-lg bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 text-xs font-mono text-emerald-600 dark:text-emerald-400 flex items-center justify-between">
            <span>✓ Cache flushed successfully: {cacheResult.keys_cleared} keys invalidated</span>
            <span className="text-slate-500 text-[11px]">{new Date(cacheResult.flushed_at).toLocaleTimeString()}</span>
          </div>
        )}
      </div>

      {/* Connector Credentials & API Key Governance */}
      <div className="rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900/60 p-6 space-y-4 shadow-sm">
        <div className="flex items-center gap-2">
          <Key size={16} className="text-blue-600 dark:text-blue-400" />
          <h2 className="text-sm font-semibold text-slate-900 dark:text-slate-200">
            Source Connectors & API Key Configuration
          </h2>
        </div>

        <p className="text-xs text-slate-600 dark:text-slate-400 leading-relaxed">
          MetaRadar accesses open biomedical endpoints without requiring credentials. Commercial and optional providers can be configured via environment variables.
        </p>

        <div className="space-y-2.5">
          {apiProviders.map((p, idx) => (
            <div
              key={idx}
              className="p-3.5 rounded-lg bg-slate-50 dark:bg-slate-950/60 border border-slate-200 dark:border-slate-800 flex items-start justify-between gap-3 text-xs"
            >
              <div className="space-y-1">
                <div className="flex items-center gap-2 flex-wrap">
                  <span className="font-semibold text-slate-900 dark:text-slate-200">{p.name}</span>
                  <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-200 dark:bg-slate-800 text-slate-700 dark:text-slate-300">
                    {p.type}
                  </span>
                  <span
                    className={`text-[10px] font-semibold px-2 py-0.5 rounded border ${
                      p.status === 'CONFIGURED'
                        ? 'bg-emerald-50 text-emerald-700 border-emerald-200 dark:bg-emerald-950/80 dark:text-emerald-300 dark:border-emerald-800'
                        : 'bg-amber-50 text-amber-700 border-amber-200 dark:bg-amber-950/80 dark:text-amber-300 dark:border-amber-800'
                    }`}
                  >
                    {p.status}
                  </span>
                </div>
                <p className="text-slate-600 dark:text-slate-400 text-[11px] leading-relaxed">{p.notes}</p>
              </div>

              <a
                href={p.url}
                target="_blank"
                rel="noreferrer"
                className="text-blue-600 dark:text-blue-400 hover:underline font-medium text-[11px] shrink-0 inline-flex items-center gap-1"
              >
                <span>Docs / Keys</span>
                <span>↗</span>
              </a>
            </div>
          ))}
        </div>
      </div>

      {/* Environment Diagnostics */}
      <div className="rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900/60 p-6 space-y-4 shadow-sm">
        <h2 className="text-sm font-semibold text-slate-900 dark:text-slate-200">Architecture Configuration</h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs font-mono">
          <div className="p-3 rounded-lg bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 space-y-1">
            <div className="text-slate-500 uppercase text-[10px] font-semibold flex items-center gap-1.5">
              <Database size={12} /> Database Stack
            </div>
            <div className="text-slate-900 dark:text-slate-200 font-semibold">PostgreSQL 16 + pgvector (384-dim)</div>
          </div>
          <div className="p-3 rounded-lg bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 space-y-1">
            <div className="text-slate-500 uppercase text-[10px] font-semibold flex items-center gap-1.5">
              <Server size={12} /> Frontend Framework
            </div>
            <div className="text-slate-900 dark:text-slate-200 font-semibold">Next.js 16 (App Router) + React 19</div>
          </div>
          <div className="p-3 rounded-lg bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 space-y-1">
            <div className="text-slate-500 uppercase text-[10px] font-semibold flex items-center gap-1.5">
              <Server size={12} /> Backend Framework
            </div>
            <div className="text-slate-900 dark:text-slate-200 font-semibold">FastAPI 0.110+ (Async / Structlog)</div>
          </div>
          <div className="p-3 rounded-lg bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 space-y-1">
            <div className="text-slate-500 uppercase text-[10px] font-semibold flex items-center gap-1.5">
              <Cpu size={12} /> Local LLM & Embeddings
            </div>
            <div className="text-slate-900 dark:text-slate-200 font-semibold">Gemma 3 4B + all-MiniLM-L6-v2</div>
          </div>
        </div>
      </div>
    </div>
  )
}
