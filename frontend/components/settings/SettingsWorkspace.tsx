'use client'

import React, { useState, useEffect, useCallback } from 'react'
import type { HealthReadyResponse, HealthModelsResponse, CacheClearResponse } from '@/types/api'
import { clearCache } from '@/lib/api'
import { formatError, FormattedError } from '@/lib/errors'
import { ErrorState } from '../common/ErrorState'

export function SettingsWorkspace() {
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

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      <div>
        <h1 className="text-xl font-bold text-slate-100">System Governance & Platform Settings</h1>
        <p className="text-xs text-slate-400 mt-1">
          Operational controls, system cache management, and platform environment diagnostics.
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

      {/* Cache Flush Management */}
      <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-6 space-y-4 shadow-sm">
        <div className="flex items-start justify-between gap-4">
          <div className="space-y-1">
            <h2 className="text-sm font-semibold text-slate-200">Redis Query Cache Management</h2>
            <p className="text-xs text-slate-400 leading-relaxed max-w-xl">
              Flushes in-memory and Redis query caches across signal search, vector retrieval, and overview aggregations.
            </p>
          </div>

          <button
            onClick={handleClearCache}
            disabled={clearing}
            className="px-4 py-2 rounded-lg bg-red-900/60 hover:bg-red-800 border border-red-700/60 text-xs font-semibold text-red-100 transition disabled:opacity-50 shrink-0"
          >
            {clearing ? 'Flushing Cache...' : 'Flush Cache'}
          </button>
        </div>

        {cacheResult && (
          <div className="p-3 rounded-lg bg-slate-950 border border-slate-800 text-xs font-mono text-emerald-400 flex items-center justify-between">
            <span>✓ Cache flushed successfully: {cacheResult.keys_cleared} keys invalidated</span>
            <span className="text-slate-500 text-[11px]">{new Date(cacheResult.flushed_at).toLocaleTimeString()}</span>
          </div>
        )}
      </div>

      {/* Environment Diagnostics */}
      <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-6 space-y-4 shadow-sm">
        <h2 className="text-sm font-semibold text-slate-200">Architecture Configuration</h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs font-mono">
          <div className="p-3 rounded-lg bg-slate-950 border border-slate-800 space-y-1">
            <div className="text-slate-500 uppercase text-[10px]">Database Stack</div>
            <div className="text-slate-200 font-semibold">PostgreSQL 16 + pgvector (384-dim)</div>
          </div>
          <div className="p-3 rounded-lg bg-slate-950 border border-slate-800 space-y-1">
            <div className="text-slate-500 uppercase text-[10px]">Frontend Framework</div>
            <div className="text-slate-200 font-semibold">Next.js 16 (App Router) + React 19</div>
          </div>
          <div className="p-3 rounded-lg bg-slate-950 border border-slate-800 space-y-1">
            <div className="text-slate-500 uppercase text-[10px]">Backend Framework</div>
            <div className="text-slate-200 font-semibold">FastAPI 0.110+ (Async / Structlog)</div>
          </div>
          <div className="p-3 rounded-lg bg-slate-950 border border-slate-800 space-y-1">
            <div className="text-slate-500 uppercase text-[10px]">Local LLM & Embeddings</div>
            <div className="text-slate-200 font-semibold">Gemma 2B + all-MiniLM-L6-v2 ONNX</div>
          </div>
        </div>
      </div>
    </div>
  )
}
