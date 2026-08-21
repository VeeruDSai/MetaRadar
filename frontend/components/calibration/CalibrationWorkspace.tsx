'use client'

import React, { useState, useEffect, useCallback } from 'react'
import type {
  CalibrationWeightsResponse,
  RecalibrateResponse,
} from '@/types/api'
import {
  fetchCalibrationWeights,
  triggerRecalibration,
  confirmWatchItem,
} from '@/lib/api'
import { formatError, FormattedError } from '@/lib/errors'
import { SectionTitle, Card, Badge } from '@/components/metaradar'
import { ErrorState } from '../common/ErrorState'
import { CheckCircle2, Gauge, RefreshCw, Sliders } from 'lucide-react'

export function CalibrationWorkspace() {
  const [weightsData, setWeightsData] = useState<CalibrationWeightsResponse | null>(null)
  const [recalibrationResult, setRecalibrationResult] = useState<RecalibrateResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [calibrating, setCalibrating] = useState(false)
  const [error, setError] = useState<FormattedError | null>(null)
  const [selectedRole, setSelectedRole] = useState<string>('')
  const [confirmedWatchId, setConfirmedWatchId] = useState<string | null>(null)

  const loadWeights = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await fetchCalibrationWeights()
      setWeightsData(data)
    } catch (err) {
      setError(formatError(err, 'Failed to fetch calibration weights.'))
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    loadWeights()
  }, [loadWeights])

  const handleRecalibrate = async () => {
    setCalibrating(true)
    setError(null)
    try {
      const result = await triggerRecalibration(selectedRole || undefined)
      setRecalibrationResult(result)
      await loadWeights()
    } catch (err) {
      setError(formatError(err, 'Batch recalibration execution failed.'))
    } finally {
      setCalibrating(false)
    }
  }

  const handleConfirmWatch = async (suggestion: any) => {
    try {
      const res = await confirmWatchItem({
        development_id: suggestion.development_id,
        trigger_event: suggestion.trigger_event,
        expected_event: suggestion.expected_event,
        monitoring_window_days: suggestion.monitoring_window_days || 90,
        responsible_function: suggestion.responsible_function,
      })
      setConfirmedWatchId(res.watch_id || suggestion.development_id)
    } catch (err) {
      console.error(err)
    }
  }

  return (
    <>
      <SectionTitle
        eyebrow="Stakeholder Calibration & Weight Governance"
        title="Scoring Calibration"
        detail="Bounded batch weight optimization based on domain expert feedback with immutable audit runs."
      />

      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 mb-4">
        <div className="filter-bar">
          <button
            className={selectedRole === '' ? 'filter-active' : ''}
            onClick={() => setSelectedRole('')}
          >
            All Roles
          </button>
          <button
            className={selectedRole === 'REGULATORY' ? 'filter-active' : ''}
            onClick={() => setSelectedRole('REGULATORY')}
          >
            Regulatory
          </button>
          <button
            className={selectedRole === 'MEDICAL_AFFAIRS' ? 'filter-active' : ''}
            onClick={() => setSelectedRole('MEDICAL_AFFAIRS')}
          >
            Medical Affairs
          </button>
          <button
            className={selectedRole === 'SAFETY' ? 'filter-active' : ''}
            onClick={() => setSelectedRole('SAFETY')}
          >
            Safety
          </button>
          <button
            className={selectedRole === 'MARKET_ACCESS' ? 'filter-active' : ''}
            onClick={() => setSelectedRole('MARKET_ACCESS')}
          >
            Market Access
          </button>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={loadWeights}
            className="inline-flex items-center gap-1 px-3 py-1.5 rounded text-xs border border-[var(--border)] bg-[var(--surface)] text-[var(--foreground)] hover:border-[var(--signal)]"
          >
            <RefreshCw size={13} className={loading ? 'animate-spin' : ''} />
            <span>Refresh</span>
          </button>
          <button
            onClick={handleRecalibrate}
            disabled={calibrating}
            className="inline-flex items-center gap-1.5 px-4 py-1.5 rounded text-xs font-semibold text-white"
            style={{ background: 'var(--primary)', opacity: calibrating ? 0.7 : 1 }}
          >
            <Sliders size={13} />
            <span>{calibrating ? 'Executing Batch...' : 'Run Calibration'}</span>
          </button>
        </div>
      </div>

      {error && (
        <ErrorState
          title={error.title}
          message={error.message}
          requestId={error.requestId}
          endpoint={error.endpoint}
          statusCode={error.statusCode}
          onRetry={loadWeights}
        />
      )}

      {/* Recalibration Result Banner */}
      {recalibrationResult && (
        <Card className="mb-4" style={{ borderColor: 'var(--border-selected)', background: 'color-mix(in srgb, var(--signal) 8%, var(--surface))' }}>
          <div className="flex items-center justify-between mb-2">
            <span className="font-semibold text-xs text-[var(--foreground)] flex items-center gap-1.5">
              <CheckCircle2 size={15} style={{ color: 'var(--success)' }} /> Batch Recalibration Run Complete
            </span>
            <Badge tone="high">{recalibrationResult.calibration_version}</Badge>
          </div>
          <p className="text-xs text-[var(--muted-foreground)] m-0 mb-3">
            {recalibrationResult.applied_feedback_count} feedback items applied across stakeholder roles.
          </p>

          {recalibrationResult.comparisons && recalibrationResult.comparisons.length > 0 && (
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-2 border-t border-[var(--border)] text-xs">
              <div className="p-3 rounded border border-[var(--border)]" style={{ background: 'var(--surface-secondary)' }}>
                <strong className="block text-[10px] uppercase text-[var(--muted-foreground)] mb-1">Baseline Average Relevance</strong>
                <div>Score: <strong className="font-mono">{recalibrationResult.comparisons[0].baseline_relevance_score}</strong></div>
              </div>
              <div className="p-3 rounded border" style={{ background: 'color-mix(in srgb, var(--success) 8%, var(--surface))', borderColor: 'color-mix(in srgb, var(--success) 30%, var(--border))' }}>
                <strong className="block text-[10px] uppercase mb-1" style={{ color: 'var(--success)' }}>Calibrated Relevance</strong>
                <div>Score: <strong className="font-mono">{recalibrationResult.comparisons[0].calibrated_relevance_score}</strong></div>
              </div>
            </div>
          )}
        </Card>
      )}

      {/* Active Weights Grid */}
      {weightsData && (
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4">
          {weightsData.weights
            .filter((w) => !selectedRole || w.stakeholder_function === selectedRole)
            .map((w) => (
              <Card key={w.stakeholder_function} className="flex flex-col justify-between">
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <h3 className="text-xs font-bold uppercase tracking-wider text-[var(--foreground)] m-0">
                      {w.stakeholder_function.replace(/_/g, ' ')}
                    </h3>
                    <Badge tone="neutral">
                      {w.updated_at ? new Date(w.updated_at).toLocaleDateString() : 'Active'}
                    </Badge>
                  </div>
                </div>

                <div className="grid grid-cols-3 gap-1.5 text-center text-xs pt-2 border-t border-[var(--border)] mt-3">
                  <div className="p-2 rounded border border-[var(--border)]" style={{ background: 'var(--surface-secondary)' }}>
                    <div className="text-[9px] text-[var(--muted-foreground)] uppercase">Impact</div>
                    <div className="font-mono font-semibold text-[var(--foreground)] mt-0.5">{w.impact_weight.toFixed(2)}</div>
                  </div>
                  <div className="p-2 rounded border border-[var(--border)]" style={{ background: 'var(--surface-secondary)' }}>
                    <div className="text-[9px] text-[var(--muted-foreground)] uppercase">Urgency</div>
                    <div className="font-mono font-semibold text-[var(--foreground)] mt-0.5">{w.urgency_weight.toFixed(2)}</div>
                  </div>
                  <div className="p-2 rounded border border-[var(--border)]" style={{ background: 'var(--surface-secondary)' }}>
                    <div className="text-[9px] text-[var(--muted-foreground)] uppercase">Novelty</div>
                    <div className="font-mono font-semibold text-[var(--foreground)] mt-0.5">{w.novelty_weight.toFixed(2)}</div>
                  </div>
                </div>
              </Card>
            ))}
        </div>
      )}
    </>
  )
}
