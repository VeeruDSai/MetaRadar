'use client'

import React, { useEffect, useState } from 'react'
import type { AthenaResponse } from '@/types/api'
import { askAthena, getAthenaSuggestedQuestions } from '@/lib/api'
import { formatError, FormattedError } from '@/lib/errors'
import { SectionTitle, Card, Badge } from '@/components/metaradar'
import { ErrorState } from '../common/ErrorState'
import { BrainCircuit, ChevronRight, Sparkles, RefreshCw } from 'lucide-react'
import { GlowingThinkingButton } from '@/components/ui/GlowingThinkingButton'
import { useTheme } from '@/components/theme/ThemeProvider'

export function AthenaWorkspace() {
  const [prompt, setPrompt] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<FormattedError | null>(null)
  const [response, setResponse] = useState<AthenaResponse | null>(null)
  const [suggestedQueries, setSuggestedQueries] = useState<string[]>([
    'What are the 5-year durability outcomes and bleed reductions for AAV5 gene therapy in Haemophilia A?',
    'How do the Phase 3 FRONTIER-2 Mim8 zero-bleed readouts compare with prophylactic factor infusions?',
    'What regulatory action milestones and PDUFA timelines are expected for anti-TFPI prophylaxis?',
    'What are the EMA CHMP 5-year safety conclusions regarding vector shedding and liver transaminitis?',
  ])
  const [signalsCount, setSignalsCount] = useState(4)
  const { isDark } = useTheme()

  useEffect(() => {
    let active = true
    getAthenaSuggestedQuestions().then((res) => {
      if (active && res.questions && res.questions.length > 0) {
        setSuggestedQueries(res.questions)
        if (res.signals_count) setSignalsCount(res.signals_count)
      }
    })
    return () => {
      active = false
    }
  }, [])

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
            <div className="flex items-center gap-1.5 text-[10px] font-bold uppercase tracking-wider text-[var(--signal)] mb-1">
              <Sparkles size={12} />
              <span>Synthesized from {signalsCount} Active Signals (Gemma 3)</span>
            </div>
            {suggestedQueries.map((q) => (
              <button
                key={q}
                onClick={() => {
                  setPrompt(q)
                  handleQuery(q)
                }}
              >
                <span className="line-clamp-2 text-left">{q}</span>
                <ChevronRight size={14} className="shrink-0 ml-1" />
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
            <GlowingThinkingButton
              label="Ask Athena"
              loadingLabel="Thinking..."
              loading={loading}
              disabled={!prompt.trim() || loading}
              onClick={() => handleQuery()}
              width={140}
              height={42}
            />
          </div>
        </Card>

        <Card className="answer-card flex flex-col justify-between">
          {loading ? (
            <div className="flex flex-col items-center justify-center min-h-[380px] gap-3 text-center">
              <div className="flex items-center gap-2 text-[15px] font-semibold text-[var(--foreground)]">
                <BrainCircuit size={18} className="text-[var(--signal)] animate-pulse" />
                <span>Athena thinking</span>
                <span className="inline-flex gap-1 items-center ml-0.5">
                  <i className="w-1.5 h-1.5 rounded-full bg-[var(--signal)] animate-bounce [animation-delay:-0.3s]" />
                  <i className="w-1.5 h-1.5 rounded-full bg-[var(--signal)] animate-bounce [animation-delay:-0.15s]" />
                  <i className="w-1.5 h-1.5 rounded-full bg-[var(--signal)] animate-bounce" />
                </span>
              </div>
              <p className="text-xs text-[var(--muted-foreground)] m-0">
                Searching vector index and evaluating source grounded evidence...
              </p>
            </div>
          ) : error ? (
            <ErrorState message={error.message} onRetry={() => handleQuery()} />
          ) : response ? (
            <div className="flex flex-col h-full justify-between">
              <div>
                <div className="flex justify-between items-center mb-4">
                  <div className="flex items-center gap-2">
                    <BrainCircuit size={16} className="text-[var(--signal)]" />
                    <span className="text-xs font-bold uppercase tracking-wider">
                      Athena Grounded Synthesis
                    </span>
                  </div>
                  <Badge tone={response.mode === 'reasoning' ? 'low' : 'neutral'}>
                    {response.mode === 'reasoning' ? 'Gemma 3 Reasoning' : 'Degraded Factual'}
                  </Badge>
                </div>

                <div className="prose text-xs text-[var(--foreground)] leading-relaxed whitespace-pre-wrap">
                  {response.answer}
                </div>
              </div>

              {response.evidence && response.evidence.length > 0 && (
                <div className="mt-6 pt-4 border-t border-[var(--border)]">
                  <span className="text-[10px] font-bold uppercase tracking-wider text-[var(--muted-foreground)] block mb-2">
                    Grounded Evidence Citations ({response.evidence.length})
                  </span>
                  <div className="flex flex-col gap-2">
                    {response.evidence.map((ev, idx) => (
                      <div
                        key={idx}
                        className="p-2.5 rounded-md bg-[var(--surface-secondary)] border border-[var(--border)] text-xs"
                      >
                        <div className="flex items-center justify-between mb-1">
                          <strong className="text-[var(--foreground)] truncate max-w-[280px]">
                            {ev.title}
                          </strong>
                          <span className="text-[10px] font-mono text-[var(--signal)] uppercase">
                            {ev.source_id}
                          </span>
                        </div>
                        <p className="text-[11px] text-[var(--muted-foreground)] line-clamp-2 m-0">
                          {ev.excerpt}
                        </p>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div className="empty-state">
              <BrainCircuit size={32} />
              <p>Athena is ready</p>
              <span>
                Select a suggested prompt from the left or enter a custom clinical query to start synthesis.
              </span>
            </div>
          )}
        </Card>
      </div>
    </>
  )
}
