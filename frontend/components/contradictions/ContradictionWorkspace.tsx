'use client'

import React, { useState, useEffect, useCallback } from 'react'
import type { ContradictionItem } from '@/types/api'
import { fetchRedTeamContradictions } from '@/lib/api'
import { formatError, FormattedError } from '@/lib/errors'
import { SectionTitle, Card, Badge } from '@/components/metaradar'
import { ErrorState } from '../common/ErrorState'
import { RefreshCw, ShieldAlert, ShieldCheck } from 'lucide-react'

export function ContradictionWorkspace() {
  const [contradictions, setContradictions] = useState<ContradictionItem[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<FormattedError | null>(null)
  const [severityFilter, setSeverityFilter] = useState<string>('')

  const loadContradictions = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await fetchRedTeamContradictions(severityFilter || undefined, 50)
      setContradictions(data)
    } catch (err) {
      setError(formatError(err, 'Failed to fetch Red-Team contradiction alerts.'))
    } finally {
      setLoading(false)
    }
  }, [severityFilter])

  useEffect(() => {
    loadContradictions()
  }, [loadContradictions])

  const getBadgeTone = (sev: string): 'critical' | 'high' | 'medium' | 'low' | 'neutral' => {
    switch (sev?.toUpperCase()) {
      case 'CRITICAL':
        return 'critical'
      case 'HIGH':
        return 'high'
      case 'MEDIUM':
        return 'medium'
      case 'LOW':
        return 'low'
      default:
        return 'neutral'
    }
  }

  return (
    <>
      <SectionTitle
        eyebrow="Pairwise Adversarial Consistency Audit"
        title="Red-Team Contradictions"
        detail="Cross-evidence verification across 19 clinical, regulatory, and safety contradiction rules."
      />

      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 mb-4">
        <div className="filter-bar">
          <button
            className={severityFilter === '' ? 'filter-active' : ''}
            onClick={() => setSeverityFilter('')}
          >
            All Severities
          </button>
          <button
            className={severityFilter === 'CRITICAL' ? 'filter-active' : ''}
            onClick={() => setSeverityFilter('CRITICAL')}
          >
            Critical
          </button>
          <button
            className={severityFilter === 'HIGH' ? 'filter-active' : ''}
            onClick={() => setSeverityFilter('HIGH')}
          >
            High
          </button>
          <button
            className={severityFilter === 'MEDIUM' ? 'filter-active' : ''}
            onClick={() => setSeverityFilter('MEDIUM')}
          >
            Medium
          </button>
        </div>

        <button
          onClick={loadContradictions}
          className="inline-flex items-center gap-1 px-3 py-1.5 rounded text-xs border border-[var(--border)] bg-[var(--surface)] text-[var(--foreground)] hover:border-[var(--signal)]"
        >
          <RefreshCw size={13} className={loading ? 'animate-spin' : ''} />
          <span>Refresh Alerts</span>
        </button>
      </div>

      {error && (
        <ErrorState
          title={error.title}
          message={error.message}
          requestId={error.requestId}
          endpoint={error.endpoint}
          statusCode={error.statusCode}
          onRetry={loadContradictions}
        />
      )}

      {loading && (
        <div className="grid gap-4">
          {[1, 2, 3].map((i) => (
            <Card key={i} className="animate-pulse h-40" />
          ))}
        </div>
      )}

      {!loading && !error && contradictions.length === 0 && (
        <Card className="empty-state">
          <ShieldCheck size={28} />
          <p>No active claim contradictions detected</p>
          <span>All pairwise cross-source statements satisfy consistency rules A through S.</span>
        </Card>
      )}

      {!loading && !error && contradictions.length > 0 && (
        <div className="grid gap-4">
          {contradictions.map((c) => (
            <Card key={c.contradiction_id}>
              <div className="flex items-start justify-between gap-4 mb-2">
                <div>
                  <div className="flex items-center gap-2 mb-1">
                    <ShieldAlert size={16} style={{ color: 'var(--danger)' }} />
                    <Badge tone={getBadgeTone(c.severity)}>
                      {c.severity} Severity
                    </Badge>
                    <span className="text-xs font-mono text-[var(--muted-foreground)]">
                      Rule: {c.rule_name || c.rule_id}
                    </span>
                  </div>
                  <h3 className="text-sm font-semibold text-[var(--foreground)] m-0">
                    {c.description}
                  </h3>
                </div>

                <div className="text-right shrink-0">
                  <span className="text-xs font-mono text-[var(--muted-foreground)]">
                    NLI Confidence: <strong className="text-[var(--foreground)]">{Math.round(c.confidence * 100)}%</strong>
                  </span>
                </div>
              </div>

              {/* Side-by-Side Verbatim Evidence Excerpts */}
              <div className="contradiction-pair grid grid-cols-1 md:grid-cols-2 gap-3 pt-2 border-t border-[var(--border)] mt-2">
                <div
                  className="claim-box p-3 rounded border border-[var(--border)]"
                  style={{ background: 'var(--surface-secondary)' }}
                >
                  <div className="flex items-center justify-between text-[10px] font-semibold text-[var(--muted-foreground)] uppercase mb-1">
                    <span>Claim A (Primary Ingestion)</span>
                    <span className="font-mono">ID: {c.claim_a_id}</span>
                  </div>
                  <p className="text-xs text-[var(--foreground)] leading-relaxed m-0 font-mono select-text">
                    {c.claim_a_excerpt || 'Evidence excerpt recorded in bronze stream.'}
                  </p>
                </div>

                <div
                  className="claim-box p-3 rounded border"
                  style={{
                    background: 'color-mix(in srgb, var(--danger) 6%, var(--surface))',
                    borderColor: 'color-mix(in srgb, var(--danger) 25%, var(--border))',
                  }}
                >
                  <div
                    className="flex items-center justify-between text-[10px] font-semibold uppercase mb-1"
                    style={{ color: 'var(--danger)' }}
                  >
                    <span>Claim B (Contradicting Stream)</span>
                    <span className="font-mono text-[var(--muted-foreground)]">ID: {c.claim_b_id}</span>
                  </div>
                  <p className="text-xs text-[var(--foreground)] leading-relaxed m-0 font-mono select-text">
                    {c.claim_b_excerpt || 'Contradicting evidence excerpt recorded in bronze stream.'}
                  </p>
                </div>
              </div>
            </Card>
          ))}
        </div>
      )}
    </>
  )
}
