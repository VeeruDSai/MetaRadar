'use client'

import React, { useState } from 'react'
import type { AthenaResponse } from '@/types/api'
import { askAthena } from '@/lib/api'
import { formatError, FormattedError } from '@/lib/errors'
import { SectionTitle, Card, Badge } from '@/components/metaradar'
import { ErrorState } from '../common/ErrorState'
import { BrainCircuit, ChevronRight, Sparkles } from 'lucide-react'
import { ThinkingShaderButton, Scene } from '@/components/ui/ThinkingShaderButton'

export function AthenaWorkspace() {
  const [prompt, setPrompt] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<FormattedError | null>(null)
  const [response, setResponse] = useState<AthenaResponse | null>(null)

  const handleQuery = async (queryText?: string) => {
    const q = (queryText ?? prompt).trim()
    if (!q || loading) return

    setLoading(true)
    setError(null)
    setResponse(null)

    try {
      const res = await askAthena(q)
      setResponse(res)
    } catch (err) {
      setError(formatError(err, 'Athena synthesis query failed.'))
    } finally {
      setLoading(false)
    }
  }

  const suggestedQueries = [
    'What are the latest clinical readout updates for Factor VIII gene therapies?',
    'Are there any contradiction alerts on concizumab safety?',
    'What regulatory target dates are expected in Q3 2026 for Haemophilia B?',
  ]

  return (
    <>
      <SectionTitle
        eyebrow="Grounded Synthesis & Semantic Q&A"
        title="Ask Athena"
        detail="Biomedical question answering with PII/PHI scrubbing and factual evidence grounding."
      />

      <div className="intelligence-grid">
        <Card className="athena-card">
          <div className="athena-orbit">
            <BrainCircuit size={28} />
          </div>
          <h2>Ask anything about the clinical landscape.</h2>
          <p className="muted">
            Athena searches the 384-dimensional vector space, applies PII/PHI scrubbing, and synthesizes answers using local Gemma 3 or privacy-gated fallback.
          </p>

          <div className="prompt-list">
            {suggestedQueries.map((q) => (
              <button
                key={q}
                onClick={() => {
                  setPrompt(q)
                  handleQuery(q)
                }}
              >
                <span>{q}</span>
                <ChevronRight size={14} />
              </button>
            ))}
          </div>

          <div className="ask-row">
            <input
              type="text"
              placeholder="Ask a question about haemophilia competitive signals..."
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter') handleQuery()
              }}
            />
            <ThinkingShaderButton
              onClick={() => handleQuery()}
              disabled={!prompt.trim()}
              loading={loading}
              label="Ask Athena"
              loadingLabel="Thinking..."
            />
          </div>
        </Card>

        <Card className="answer-card flex flex-col justify-between">
          {loading ? (
            <div className="flex flex-col items-center justify-center py-16 gap-4">
              <Scene />
              <span className="text-xs text-[var(--muted-foreground)] animate-pulse">
                Synthesizing grounded answer across indexed vector embeddings...
              </span>
            </div>
          ) : error ? (
            <ErrorState
              title={error.title}
              message={error.message}
              requestId={error.requestId}
              endpoint={error.endpoint}
              statusCode={error.statusCode}
              onRetry={() => handleQuery()}
            />
          ) : response ? (
            <div>
              <div className="flex items-center justify-between gap-3 mb-3 pb-2 border-b border-[var(--border)]">
                <div className="flex items-center gap-2">
                  <Sparkles size={16} style={{ color: 'var(--signal)' }} />
                  <strong className="text-xs uppercase tracking-wider text-[var(--foreground)]">Athena Synthesis</strong>
                </div>
                <Badge tone={response.mode === 'insufficient_evidence' ? 'high' : 'low'}>
                  {response.mode === 'insufficient_evidence' ? 'Insufficient Evidence' : 'Grounded Synthesis'}
                </Badge>
              </div>

              <p className="text-sm leading-relaxed text-[var(--foreground)] whitespace-pre-line m-0 mb-4">
                {response.answer}
              </p>

              {response.evidence && response.evidence.length > 0 && (
                <div className="pt-3 border-t border-[var(--border)] mt-3">
                  <div className="text-[10px] uppercase tracking-wider font-semibold text-[var(--muted-foreground)] mb-2">
                    Retrieved Vector Evidence Citations ({response.evidence.length})
                  </div>
                  <div className="grid gap-2 max-h-60 overflow-y-auto pr-1">
                    {response.evidence.map((cit, idx) => (
                      <div
                        key={idx}
                        className="p-2.5 rounded border border-[var(--border)] text-xs"
                        style={{ background: 'var(--surface-secondary)' }}
                      >
                        <div className="flex items-center justify-between text-[11px] font-semibold text-[var(--primary)] mb-1">
                          <span className="truncate">{cit.title}</span>
                          <span className="font-mono text-[var(--muted-foreground)] text-[10px] shrink-0 ml-2">
                            Dist: {cit.distance}
                          </span>
                        </div>
                        <p className="text-xs text-[var(--muted-foreground)] m-0 leading-relaxed font-sans">
                          {cit.excerpt}
                        </p>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              <div className="confidence">
                <span>Evidence Grounding Confidence:</span>
                <strong>{Math.round(response.confidence)}%</strong>
              </div>
            </div>
          ) : (
            <div className="empty-state">
              <BrainCircuit size={28} />
              <p>Athena is ready</p>
              <span>Select a suggested prompt from the left or enter a custom clinical query to start synthesis.</span>
            </div>
          )}
        </Card>
      </div>
    </>
  )
}
