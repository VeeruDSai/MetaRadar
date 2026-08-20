'use client'

import React, { useState } from 'react'

export interface ErrorStateProps {
  title?: string
  message: string
  requestId?: string
  endpoint?: string
  statusCode?: number
  onRetry?: () => void
  compact?: boolean
}

export function ErrorState({
  title = 'Request Failed',
  message,
  requestId,
  endpoint,
  statusCode,
  onRetry,
  compact = false,
}: ErrorStateProps) {
  const [detailsOpen, setDetailsOpen] = useState(false)
  const [copied, setCopied] = useState(false)

  const handleCopyRequestId = () => {
    if (requestId && typeof navigator !== 'undefined') {
      navigator.clipboard.writeText(requestId)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    }
  }

  if (compact) {
    return (
      <div
        role="alert"
        aria-live="assertive"
        className="rounded-lg border border-red-500/30 bg-red-950/20 p-3 text-xs text-red-200 flex items-center justify-between gap-2"
      >
        <div className="flex items-center gap-2 truncate">
          <span className="w-1.5 h-1.5 rounded-full bg-red-400 shrink-0" />
          <span className="truncate">{message}</span>
        </div>
        {onRetry && (
          <button
            onClick={onRetry}
            className="px-2 py-1 bg-red-900/40 hover:bg-red-800/60 rounded text-red-100 transition shrink-0"
          >
            Retry
          </button>
        )}
      </div>
    )
  }

  return (
    <div
      role="alert"
      aria-live="assertive"
      className="rounded-xl border border-red-500/30 bg-red-950/20 p-6 space-y-4 shadow-sm"
    >
      <div className="flex items-start justify-between gap-4">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <span className="inline-block w-2.5 h-2.5 rounded-full bg-red-500 animate-pulse" />
            <h3 className="text-sm font-semibold text-red-400">{title}</h3>
            {statusCode && (
              <span className="px-1.5 py-0.5 rounded text-[10px] font-mono bg-red-900/60 text-red-200 border border-red-700/50">
                HTTP {statusCode}
              </span>
            )}
          </div>
          <p className="text-sm text-slate-300">{message}</p>
        </div>

        {onRetry && (
          <button
            onClick={onRetry}
            className="shrink-0 px-3.5 py-1.5 rounded-lg bg-red-900/60 hover:bg-red-800 border border-red-700/60 text-xs font-medium text-red-100 transition shadow"
          >
            Retry Request
          </button>
        )}
      </div>

      {requestId && (
        <div className="flex items-center gap-2 text-xs text-slate-400 bg-slate-900/60 rounded-md px-3 py-1.5 border border-slate-800">
          <span className="text-slate-500">Correlation ID:</span>
          <code className="font-mono text-slate-300 select-all">{requestId}</code>
          <button
            type="button"
            onClick={handleCopyRequestId}
            aria-label="Copy correlation ID"
            className="ml-auto text-slate-400 hover:text-slate-200 transition text-[11px] px-1.5 py-0.5 rounded hover:bg-slate-800"
          >
            {copied ? '✓ Copied' : 'Copy ID'}
          </button>
        </div>
      )}

      {(endpoint || statusCode || requestId) && (
        <div>
          <button
            type="button"
            className="text-xs text-slate-400 hover:text-slate-200 transition flex items-center gap-1"
            onClick={() => setDetailsOpen((v) => !v)}
            aria-expanded={detailsOpen}
          >
            <span>{detailsOpen ? '▼ Hide' : '▶ Show'} Technical Diagnostics</span>
          </button>

          {detailsOpen && (
            <pre className="mt-2 text-[11px] font-mono text-slate-400 bg-slate-950/80 rounded-lg p-3 overflow-x-auto border border-slate-800">
              {JSON.stringify(
                {
                  endpoint,
                  status_code: statusCode,
                  correlation_id: requestId,
                  timestamp: new Date().toISOString(),
                },
                null,
                2
              )}
            </pre>
          )}
        </div>
      )}
    </div>
  )
}
