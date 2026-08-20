'use client'

import React, { useState, useEffect, useCallback } from 'react'
import type {
  CalibrationWeightsResponse,
  RecalibrateResponse,
  RoleWeight,
} from '@/types/api'
import {
  fetchCalibrationWeights,
  triggerRecalibration,
  confirmWatchItem,
} from '@/lib/api'
import { formatError, FormattedError } from '@/lib/errors'
import { ErrorState } from '../common/ErrorState'
import { EmptyState } from '../common/EmptyState'

export function CalibrationWorkspace() {
  const [weightsData, setWeightsData] = useState<CalibrationWeightsResponse | null>(null)
  const [recalibrationResult, setRecalibrationResult] = useState<RecalibrateResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [calibrating, setCalibrating] = useState(false)
  const [error, setError] = useState<FormattedError | null>(null)
  const [selectedRole, setSelectedRole] = useState<string>('')

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
      await confirmWatchItem({
        development_id: suggestion.development_id,
        trigger_event: suggestion.trigger_event,
        expected_event: suggestion.expected_event,
        monitoring_window_days: suggestion.monitoring_window_days || 90,
        responsible_function: suggestion.responsible_function,
      })
      alert(`Watch rule created for ${suggestion.responsible_function}!`)
    } catch (err) {
      alert('Failed to confirm watch rule.')
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-slate-100">Stakeholder Calibration & Weight Governance</h1>
          <p className="text-xs text-slate-400 mt-1">
            Bounded batch weight optimization based on domain expert feedback with immutable audit runs.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <select
            value={selectedRole}
            onChange={(e) => setSelectedRole(e.target.value)}
            className="px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-800 text-xs text-slate-200"
          >
            <option value="">All 6 Canonical Roles</option>
            <option value="REGULATORY">Regulatory Affairs</option>
            <option value="MEDICAL_AFFAIRS">Medical Affairs</option>
            <option value="SAFETY">Safety</option>
            <option value="MARKET_ACCESS">Market Access</option>
            <option value="COMMUNICATIONS">Communications</option>
            <option value="LEADERSHIP">Leadership</option>
          </select>

          <button
            onClick={handleRecalibrate}
            disabled={calibrating}
            className="px-4 py-1.5 rounded-lg bg-blue-600 hover:bg-blue-500 text-xs font-semibold text-white transition disabled:opacity-50 flex items-center gap-1.5"
          >
            {calibrating ? 'Executing Batch...' : 'Run Calibration'}
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

      {/* Active Weights Grid */}
      {weightsData && (
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-semibold uppercase tracking-wider text-slate-400">
              Active Calibrated Scoring Weights ({weightsData.version})
            </h2>
            <span className="text-xs font-mono text-slate-400">
              Pending Feedback: {weightsData.pending_feedback_count ?? 0} items
            </span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4">
            {weightsData.weights.map((w) => (
              <div
                key={w.stakeholder_function}
                className="rounded-xl border border-slate-800 bg-slate-900/60 p-4 space-y-3 shadow-sm"
              >
                <div className="flex items-center justify-between">
                  <h3 className="text-xs font-semibold text-slate-200">
                    {w.stakeholder_function.replace(/_/g, ' ')}
                  </h3>
                  <span className="text-[10px] text-slate-500 font-mono">
                    {w.updated_at ? new Date(w.updated_at).toLocaleDateString() : 'Active'}
                  </span>
                </div>

                <div className="grid grid-cols-3 gap-2 text-center text-xs">
                  <div className="p-2 rounded bg-slate-950/60 border border-slate-800">
                    <div className="text-[10px] text-slate-500">Impact</div>
                    <div className="font-mono font-semibold text-slate-200">{w.impact_weight.toFixed(2)}</div>
                  </div>
                  <div className="p-2 rounded bg-slate-950/60 border border-slate-800">
                    <div className="text-[10px] text-slate-500">Urgency</div>
                    <div className="font-mono font-semibold text-slate-200">{w.urgency_weight.toFixed(2)}</div>
                  </div>
                  <div className="p-2 rounded bg-slate-950/60 border border-slate-800">
                    <div className="text-[10px] text-slate-500">Novelty</div>
                    <div className="font-mono font-semibold text-slate-200">{w.novelty_weight.toFixed(2)}</div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Recalibration Outcome & Side-by-Side Comparison */}
      {recalibrationResult && (
        <div className="rounded-xl border border-blue-900/40 bg-slate-900/70 p-6 space-y-4 shadow-md">
          <div className="flex items-center justify-between pb-3 border-b border-slate-800">
            <h2 className="text-sm font-semibold uppercase tracking-wider text-blue-400">
              Recalibration Run Results ({recalibrationResult.calibration_version})
            </h2>
            <span className="text-xs font-mono text-slate-400">
              Applied Feedback: {recalibrationResult.applied_feedback_count} submissions
            </span>
          </div>

          {recalibrationResult.comparisons && recalibrationResult.comparisons.length > 0 && (
            <div className="space-y-3">
              <h3 className="text-xs font-semibold text-slate-400 uppercase">
                Side-by-Side Routing Before / After Comparison
              </h3>
              <div className="space-y-2">
                {recalibrationResult.comparisons.map((c, idx) => (
                  <div
                    key={idx}
                    className="p-3 rounded-lg bg-slate-950/60 border border-slate-800 text-xs grid grid-cols-1 md:grid-cols-2 gap-3"
                  >
                    <div className="space-y-1">
                      <div className="text-[10px] text-slate-500 uppercase">Baseline Routing</div>
                      <div className="text-slate-300">Priority: <strong>{c.baseline_priority}</strong> (Score: {Math.round(c.baseline_relevance_score * 100)}%)</div>
                      <div className="text-slate-400 text-[11px]">{c.baseline_suggested_action}</div>
                    </div>
                    <div className="space-y-1 border-t md:border-t-0 md:border-l border-slate-800 md:pl-3 pt-2 md:pt-0">
                      <div className="text-[10px] text-emerald-400 uppercase">Calibrated Outcome (+{c.confidence_uplift_pct}%)</div>
                      <div className="text-emerald-300">Priority: <strong>{c.calibrated_priority}</strong> (Score: {Math.round(c.calibrated_relevance_score * 100)}%)</div>
                      <div className="text-slate-300 text-[11px]">{c.calibrated_suggested_action}</div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {recalibrationResult.watch_rule_suggestions && recalibrationResult.watch_rule_suggestions.length > 0 && (
            <div className="space-y-3 pt-3 border-t border-slate-800">
              <h3 className="text-xs font-semibold text-amber-400 uppercase">
                Suggested Monitoring Watch Rules
              </h3>
              <div className="space-y-2">
                {recalibrationResult.watch_rule_suggestions.map((sug) => (
                  <div
                    key={sug.suggestion_id}
                    className="p-3 rounded-lg bg-slate-950/60 border border-amber-800/40 text-xs flex items-center justify-between gap-3"
                  >
                    <div className="space-y-0.5">
                      <div className="font-semibold text-slate-200">{sug.expected_event}</div>
                      <div className="text-slate-400 text-[11px]">{sug.rationale} ({sug.responsible_function})</div>
                    </div>
                    <button
                      onClick={() => handleConfirmWatch(sug)}
                      className="px-3 py-1 bg-amber-600 hover:bg-amber-500 rounded text-slate-950 font-semibold text-xs shrink-0 transition"
                    >
                      Confirm Rule
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Immutable Run History Table */}
      {weightsData?.run_history && weightsData.run_history.length > 0 && (
        <div className="space-y-3 pt-4 border-t border-slate-800">
          <h2 className="text-xs font-semibold uppercase tracking-wider text-slate-400">
            Immutable Calibration Audit Run Log
          </h2>
          <div className="rounded-xl border border-slate-800 bg-slate-900/60 overflow-x-auto">
            <table className="w-full text-left text-xs text-slate-300">
              <thead className="bg-slate-950/80 text-[11px] text-slate-400 uppercase border-b border-slate-800">
                <tr>
                  <th className="p-3">Run ID</th>
                  <th className="p-3">Triggered At</th>
                  <th className="p-3">Version</th>
                  <th className="p-3">Feedback Applied</th>
                  <th className="p-3">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 font-mono">
                {weightsData.run_history.map((run) => (
                  <tr key={run.run_id} className="hover:bg-slate-850">
                    <td className="p-3 font-mono text-[11px] text-slate-400 truncate max-w-xs">{run.run_id}</td>
                    <td className="p-3 text-[11px]">{new Date(run.triggered_at).toLocaleString()}</td>
                    <td className="p-3 text-blue-400">{run.scoring_version}</td>
                    <td className="p-3">{run.feedback_count} submissions</td>
                    <td className="p-3 text-emerald-400 uppercase text-[10px]">{run.status}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  )
}
