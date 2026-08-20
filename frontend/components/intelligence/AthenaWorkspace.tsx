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
        <h1 className="text-xl font-bold text-slate-100">Athena Intelligence Synthesis</h1>
        <p className="text-xs text-slate-400 mt-1">
          Grounded biomedical reasoning over indexed vector evidence with zero-fabrication guarantees and PII privacy gates.
        </p>
      </div>

      {/* Query Input Card */}
      <form onSubmit={handleQuery} className="rounded-xl border border-slate-800 bg-slate-900/60 p-5 space-y-4 shadow-sm">
        <div className="space-y-2">
          <label htmlFor="athena-query" className="block text-xs font-semibold uppercase tracking-wider text-slate-400">
            Biomedical Query or Hypothesis
          </label>
          <textarea
            id="athena-query"
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            placeholder="Ask a question (e.g., 'What are the latest clinical readout updates for Factor VIII gene therapies in severe Haemophilia A?')"
            rows={3}
            className="w-full rounded-lg bg-slate-950 border border-slate-800 p-3 text-sm text-slate-200 focus:outline-none focus:border-blue-500 font-sans"
          />
        </div>

        <div className="flex items-center justify-between gap-3">
          <div className="flex items-center gap-2 text-[11px] text-slate-500">
            <span className="w-1.5 h-1.5 rounded-full bg-blue-400" />
            <span>PII/PHI auto-scrubbed • pgvector HNSW retrieval • Gemma / Local fallback</span>
          </div>

          <button
            type="submit"
            disabled={loading || !prompt.trim()}
            className="px-5 py-2 rounded-lg bg-blue-600 hover:bg-blue-500 text-xs font-semibold text-white transition disabled:opacity-50 flex items-center gap-2"
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
        <div className="rounded-xl border border-slate-800 bg-slate-900/70 p-6 space-y-6 shadow-md">
          <div className="flex items-center justify-between gap-4 pb-4 border-b border-slate-800">
            <div className="flex items-center gap-2">
              <span className={`px-2.5 py-0.5 rounded-full text-xs font-semibold uppercase tracking-wider ${response.mode === 'insufficient_evidence' ? 'bg-amber-950/80 text-amber-300 border border-amber-800/60' : 'bg-emerald-950/80 text-emerald-300 border border-emerald-800/60'}`}>
                {response.mode === 'insufficient_evidence' ? 'Insufficient Evidence' : 'Grounded Synthesis'}
              </span>
              <span className="text-xs text-slate-400 font-mono">
                Citations: {response.evidence_count} retrieved
              </span>
            </div>

            <div className="text-right">
              <span className="text-xs font-mono text-slate-300">
                Confidence: <strong className="text-emerald-400">{response.confidence}%</strong>
              </span>
              {response.model_metadata?.provider && (
                <div className="text-[10px] text-slate-500 font-mono">
                  Provider: {response.model_metadata.provider} ({response.model_metadata.mode})
                </div>
              )}
            </div>
          </div>

          {/* Synthesized Answer */}
          <div className="space-y-2">
            <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-400">
              Synthesis Output
            </h3>
            <div className="text-sm text-slate-200 leading-relaxed whitespace-pre-line bg-slate-950/60 p-4 rounded-xl border border-slate-800">
              {response.answer}
            </div>
          </div>

          {/* Evidence Citations */}
          {response.evidence && response.evidence.length > 0 && (
            <div className="space-y-3 pt-2">
              <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-400">
                Retrieved Vector Evidence Citations
              </h3>
              <div className="space-y-2">
                {response.evidence.map((cit, idx) => (
                  <div
                    key={idx}
                    className="p-3.5 rounded-lg bg-slate-950/80 border border-slate-800 text-xs space-y-1.5"
                  >
                    <div className="flex items-center justify-between text-[11px] font-semibold text-blue-400">
                      <span className="truncate max-w-md">{cit.title}</span>
                      <span className="font-mono text-slate-500 shrink-0 ml-2">
                        Distance: {cit.distance}
                      </span>
                    </div>
                    <p className="text-slate-300 leading-relaxed font-sans">{cit.excerpt}</p>
                    <div className="flex items-center justify-between text-[10px] text-slate-500 pt-1 font-mono">
                      <span>Source: {cit.source_id.toUpperCase()}</span>
                      {cit.canonical_url && (
                        <a
                          href={cit.canonical_url}
                          target="_blank"
                          rel="noreferrer"
                          className="text-blue-400 hover:underline"
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
