'use client'

import React, { useState } from 'react'
import type { AthenaResponse } from '@/types/api'
import { askAthena } from '@/lib/api'
import { formatError, FormattedError } from '@/lib/errors'
import { ErrorState } from '../common/ErrorState'

export function AthenaWorkspace() {
  const [prompt, setPrompt] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<FormattedError | null>(null)
  const [response, setResponse] = useState<AthenaResponse | null>(null)

  const handleQuery = async (e?: React.FormEvent) => {
    e?.preventDefault?.()
    if (!prompt.trim() || loading) return

    setLoading(true)
    setError(null)
    setResponse(null)

    try {
      const res = await askAthena(prompt.trim())
      setResponse(res)
    } catch (err) {
      setError(formatError(err, 'Athena synthesis query failed.'))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      <div>
        <div className="text-[11px] font-semibold tracking-wider uppercase text-[var(--muted-foreground)] mb-0.5">
          Grounded Synthesis & Semantic Q&A
        </div>
        <h2 className="text-xl font-bold text-[var(--foreground)]">Athena Intelligence Synthesis</h2>
        <p className="text-xs text-[var(--muted-foreground)] mt-1">
          Grounded biomedical reasoning over indexed vector evidence with zero-fabrication guarantees and PII privacy gates.
        </p>
      </div>

      {/* Query Input Card */}
      <form onSubmit={handleQuery} className="rounded-xl border border-[var(--border)] bg-[var(--card)] p-5 space-y-4 shadow-xs">
        <div className="space-y-2">
          <label htmlFor="athena-query" className="block text-xs font-semibold uppercase tracking-wider text-[var(--muted-foreground)]">
            Biomedical Query or Hypothesis
          </label>
          <textarea
            id="athena-query"
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            placeholder="Ask a question (e.g., 'What are the latest clinical readout updates for Factor VIII gene therapies in severe Haemophilia A?')"
            rows={3}
            className="w-full rounded-lg bg-[var(--surface-subtle)] border border-[var(--border)] p-3 text-sm text-[var(--foreground)] focus:outline-none focus:border-blue-500 font-sans"
          />
        </div>

        <div className="flex items-center justify-between gap-3">
          <div className="flex items-center gap-2 text-[11px] text-[var(--muted-foreground)]">
            <span className="w-1.5 h-1.5 rounded-full bg-blue-500" />
            <span>PII/PHI auto-scrubbed • pgvector HNSW retrieval • Gemma / Local fallback</span>
          </div>

          <button
            type="submit"
            disabled={loading || !prompt.trim()}
            className="px-5 py-2 rounded-lg bg-blue-600 hover:bg-blue-500 text-xs font-semibold text-white transition disabled:opacity-50 flex items-center gap-2 shadow-xs"
          >
            {loading ? (
              <>
                <span className="w-3 h-3 border-2 border-white/20 border-t-white rounded-full animate-spin" />
                Synthesizing...
              </>
            ) : (
              'Query Athena'
            )}
          </button>
        </div>
      </form>

      {/* Error state */}
      {error && (
        <ErrorState
          title={error.title}
          message={error.message}
          requestId={error.requestId}
          endpoint={error.endpoint}
          statusCode={error.statusCode}
          onRetry={handleQuery}
        />
      )}

      {/* Response Card */}
      {response && (
        <div className="rounded-xl border border-[var(--border)] bg-[var(--card)] p-6 space-y-6 shadow-md">
          <div className="flex items-center justify-between gap-4 pb-4 border-b border-[var(--border)]">
            <div className="flex items-center gap-2">
              <span className={`px-2.5 py-0.5 rounded-full text-xs font-semibold uppercase tracking-wider ${response.mode === 'insufficient_evidence' ? 'bg-amber-50 text-amber-700 border border-amber-200 dark:bg-amber-950/80 dark:text-amber-300 dark:border-amber-800/60' : 'bg-emerald-50 text-emerald-700 border border-emerald-200 dark:bg-emerald-950/80 dark:text-emerald-300 dark:border-emerald-800/60'}`}>
                {response.mode === 'insufficient_evidence' ? 'Insufficient Evidence' : 'Grounded Synthesis'}
              </span>
              <span className="text-xs text-[var(--muted-foreground)] font-mono">
                Citations: {response.evidence_count} retrieved
              </span>
            </div>

            <div className="text-right">
              <span className="text-xs font-mono text-[var(--foreground)]">
                Confidence: <strong className="text-emerald-600 dark:text-emerald-400">{response.confidence}%</strong>
              </span>
              {response.model_metadata?.provider && (
                <div className="text-[10px] text-[var(--muted-foreground)] font-mono">
                  Provider: {response.model_metadata.provider} ({response.model_metadata.mode})
                </div>
              )}
            </div>
          </div>

          {/* Synthesized Answer */}
          <div className="space-y-2">
            <h3 className="text-xs font-semibold uppercase tracking-wider text-[var(--muted-foreground)]">
              Synthesis Output
            </h3>
            <div className="text-sm text-[var(--foreground)] leading-relaxed whitespace-pre-line bg-[var(--surface-subtle)] p-4 rounded-xl border border-[var(--border)]">
              {response.answer}
            </div>
          </div>

          {/* Evidence Citations */}
          {response.evidence && response.evidence.length > 0 && (
            <div className="space-y-3 pt-2">
              <h3 className="text-xs font-semibold uppercase tracking-wider text-[var(--muted-foreground)]">
                Retrieved Vector Evidence Citations
              </h3>
              <div className="space-y-2">
                {response.evidence.map((cit, idx) => (
                  <div
                    key={idx}
                    className="p-3.5 rounded-lg bg-[var(--surface-subtle)] border border-[var(--border)] text-xs space-y-1.5"
                  >
                    <div className="flex items-center justify-between text-[11px] font-semibold text-blue-600 dark:text-blue-400">
                      <span className="truncate max-w-md">{cit.title}</span>
                      <span className="font-mono text-[var(--muted-foreground)] shrink-0 ml-2">
                        Distance: {cit.distance}
                      </span>
                    </div>
                    <p className="text-[var(--foreground)] leading-relaxed font-sans">{cit.excerpt}</p>
                    <div className="flex items-center justify-between text-[10px] text-[var(--muted-foreground)] pt-1 font-mono">
                      <span>Source: {cit.source_id.toUpperCase()}</span>
                      {cit.canonical_url && (
                        <a
                          href={cit.canonical_url}
                          target="_blank"
                          rel="noreferrer"
                          className="text-blue-600 dark:text-blue-400 hover:underline font-medium"
                        >
                          View Source ↗
                        </a>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
