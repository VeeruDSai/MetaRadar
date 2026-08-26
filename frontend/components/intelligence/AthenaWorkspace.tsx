'use client'

import React, { useEffect, useRef, useState } from 'react'
import Link from 'next/link'
import type { AthenaStreamMeta } from '@/lib/api'
import { getAthenaSuggestedQuestions, streamAthena } from '@/lib/api'
import { formatError, FormattedError } from '@/lib/errors'
import { SectionTitle, Card, Badge } from '@/components/metaradar'
import { ErrorState } from '../common/ErrorState'
import { BrainCircuit, ChevronRight, Sparkles, ExternalLink } from 'lucide-react'
import { GlowingThinkingButton } from '@/components/ui/GlowingThinkingButton'
import { useTheme } from '@/components/theme/ThemeProvider'

type AthenaPhase = 'idle' | 'thinking' | 'streaming' | 'done'

function modeLabel(meta: AthenaStreamMeta | null, degraded: boolean): string {
  if (!meta) return 'Gemma 3 Reasoning'
  switch (meta.response_type) {
    case 'assistant_intro':
      return 'Assistant Intro'
    case 'insufficient_evidence':
      return 'No Grounding Evidence'
    default:
      return degraded ? 'Degraded Factual' : 'Gemma 3 Reasoning'
  }
}

export function AthenaWorkspace() {
  const [prompt, setPrompt] = useState('')
  const [phase, setPhase] = useState<AthenaPhase>('idle')
  const [answer, setAnswer] = useState('')
  const [meta, setMeta] = useState<AthenaStreamMeta | null>(null)
  const [degraded, setDegraded] = useState(false)
  const [streamNotice, setStreamNotice] = useState<string | null>(null)
  const [error, setError] = useState<FormattedError | null>(null)
  const [suggestedQueries, setSuggestedQueries] = useState<string[]>([
    'What are the 5-year durability outcomes and bleed reductions for AAV5 gene therapy in Haemophilia A?',
    'How do the Phase 3 FRONTIER-2 Mim8 zero-bleed readouts compare with prophylactic factor infusions?',
    'What regulatory action milestones and PDUFA timelines are expected for anti-TFPI prophylaxis?',
    'What are the EMA CHMP 5-year safety conclusions regarding vector shedding and liver transaminitis?',
  ])
  const [signalsCount, setSignalsCount] = useState(4)
  const abortRef = useRef<AbortController | null>(null)
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

  // Abort any in-flight stream on unmount
  useEffect(() => {
    return () => {
      abortRef.current?.abort()
    }
  }, [])

  const busy = phase === 'thinking' || phase === 'streaming'

  const handleQuery = async (queryText?: string) => {
    const q = (queryText ?? prompt).trim()
    if (!q || busy) return

    abortRef.current?.abort()
    const controller = new AbortController()
    abortRef.current = controller

    setPhase('thinking')
    setError(null)
    setAnswer('')
    setMeta(null)
    setDegraded(false)
    setStreamNotice(null)

    try {
      await streamAthena(
        q,
        {
          onMeta: (m) => setMeta(m),
          onToken: (delta) =>
            setAnswer((prev) => {
              if (prev.length === 0) setPhase('streaming')
              return prev + delta
            }),
          onDegraded: () => setDegraded(true),
          onError: (message) => setStreamNotice(message),
        },
        controller.signal
      )
      if (!controller.signal.aborted) setPhase('done')
    } catch (err) {
      if (err instanceof Error && err.name === 'AbortError') return
      setError(formatError(err, 'Athena synthesis query failed.'))
      setPhase('done')
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
                disabled={busy}
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
              loadingLabel={phase === 'streaming' ? 'Streaming...' : 'Thinking...'}
              loading={busy}
              disabled={!prompt.trim() || busy}
              onClick={() => handleQuery()}
              width={140}
              height={42}
            />
          </div>
        </Card>

        <Card className="answer-card flex flex-col justify-between">
          {phase === 'thinking' ? (
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
          ) : answer ? (
            <div className="flex flex-col h-full justify-between">
              <div>
                <div className="flex justify-between items-center mb-4">
                  <div className="flex items-center gap-2">
                    <BrainCircuit size={16} className="text-[var(--signal)]" />
                    <span className="text-xs font-bold uppercase tracking-wider">
                      Athena Grounded Synthesis
                    </span>
                  </div>
                  <Badge tone={degraded ? 'neutral' : 'low'}>{modeLabel(meta, degraded)}</Badge>
                </div>

                <div className="prose text-xs text-[var(--foreground)] leading-relaxed whitespace-pre-wrap">
                  {answer}
                  {phase === 'streaming' && (
                    <span className="inline-block w-1.5 h-3.5 ml-0.5 align-middle bg-[var(--signal)] animate-pulse" aria-hidden />
                  )}
                </div>

                {streamNotice && (
                  <p className="mt-3 text-[11px] text-[var(--warning, #b45309)] m-0">{streamNotice}</p>
                )}
              </div>

              {meta && meta.evidence.length > 0 && (
                <div className="mt-6 pt-4 border-t border-[var(--border)]">
                  <span className="text-[10px] font-bold uppercase tracking-wider text-[var(--muted-foreground)] block mb-2">
                    Grounded Evidence Citations ({meta.evidence_count})
                  </span>
                  <p className="text-[10px] text-[var(--muted-foreground)] m-0 mb-2">
                    Click any citation to open its source signal page and verify the evidence.
                  </p>
                  <div className="flex flex-col gap-2">
                    {meta.evidence.map((ev, idx) => {
                      const detailHref = `/signals/${encodeURIComponent(ev.signal_id)}`
                      return (
                        <div
                          key={`${ev.signal_id}-${idx}`}
                          className="p-2.5 rounded-md bg-[var(--surface-secondary)] border border-[var(--border)] text-xs hover:border-[var(--signal)] transition-colors"
                        >
                          <div className="flex items-center justify-between mb-1 gap-2">
                            <Link
                              href={detailHref}
                              className="min-w-0 flex-1 group"
                              title="Open source signal page"
                            >
                              <strong className="text-[var(--foreground)] truncate max-w-[280px] block group-hover:text-[var(--signal)] transition-colors">
                                {ev.title}
                              </strong>
                            </Link>
                            <span className="flex items-center gap-1.5 shrink-0">
                              <Link
                                href={detailHref}
                                className="flex items-center gap-0.5 text-[10px] font-mono text-[var(--signal)] uppercase hover:underline"
                                title="Open source signal page"
                              >
                                {ev.source_id}
                                <ExternalLink size={10} />
                              </Link>
                              {ev.canonical_url && (
                                <a
                                  href={ev.canonical_url}
                                  target="_blank"
                                  rel="noopener noreferrer"
                                  className="text-[var(--muted-foreground)] hover:text-[var(--signal)] transition-colors"
                                  title="Open original external source"
                                >
                                  <ExternalLink size={11} />
                                </a>
                              )}
                            </span>
                          </div>
                          <Link href={detailHref} title="Open source signal page">
                            <p className="text-[11px] text-[var(--muted-foreground)] line-clamp-2 m-0 hover:text-[var(--foreground)] transition-colors">
                              {ev.excerpt}
                            </p>
                          </Link>
                        </div>
                      )
                    })}
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
