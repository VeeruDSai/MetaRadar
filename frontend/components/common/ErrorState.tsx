'use client'

import React, { useState } from 'react'
import { Card, Badge } from '@/components/metaradar'
import { AlertTriangle, RefreshCw } from 'lucide-react'

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
        className="p-3 rounded border text-xs flex items-center justify-between gap-2"
        style={{
          background: 'color-mix(in srgb, var(--danger) 8%, var(--surface))',
          borderColor: 'color-mix(in srgb, var(--danger) 30%, var(--border))',
          color: 'var(--danger)',
        }}
      >
        <div className="flex items-center gap-2 truncate">
          <AlertTriangle size={14} className="shrink-0" />
          <span className="truncate">{message}</span>
        </div>
        {onRetry && (
          <button
            onClick={onRetry}
            className="px-2 py-1 rounded text-xs font-semibold shrink-0 border"
            style={{
              borderColor: 'color-mix(in srgb, var(--danger) 40%, var(--border))',
              background: 'var(--surface)',
              color: 'var(--foreground)',
            }}
          >
            Retry
          </button>
        )}
      </div>
    )
  }

  return (
    <Card
      role="alert"
      aria-live="assertive"
      className="space-y-3"
      style={{
        background: 'color-mix(in srgb, var(--danger) 6%, var(--surface))',
        borderColor: 'color-mix(in srgb, var(--danger) 30%, var(--border))',
      }}
    >
      <div className="flex items-start justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <AlertTriangle size={16} style={{ color: 'var(--danger)' }} />
            <strong className="text-sm font-semibold" style={{ color: 'var(--danger)' }}>
              {title}
            </strong>
            {statusCode && (
              <Badge tone="critical">HTTP {statusCode}</Badge>
            )}
          </div>
          <p className="text-xs text-[var(--foreground)] m-0 leading-relaxed">{message}</p>
        </div>

        {onRetry && (
          <button
            onClick={onRetry}
            className="inline-flex items-center gap-1 px-3 py-1.5 rounded text-xs font-semibold border"
            style={{
              background: 'var(--surface)',
              borderColor: 'color-mix(in srgb, var(--danger) 40%, var(--border))',
              color: 'var(--foreground)',
            }}
          >
            <RefreshCw size={12} />
            <span>Retry</span>
          </button>
        )}
      </div>

      {requestId && (
        <div
          className="flex items-center gap-2 text-xs p-2 rounded border border-[var(--border)]"
          style={{ background: 'var(--surface)' }}
        >
          <span className="text-[var(--muted-foreground)]">Correlation ID:</span>
          <code className="font-mono text-[var(--foreground)] text-[11px] select-all">{requestId}</code>
          <button
            type="button"
            onClick={handleCopyRequestId}
            aria-label="Copy correlation ID"
            className="ml-auto text-[var(--muted-foreground)] hover:text-[var(--foreground)] text-[11px] px-2 py-0.5 rounded border border-[var(--border)] bg-transparent"
          >
            {copied ? '✓ Copied' : 'Copy ID'}
          </button>
        </div>
      )}

      {(endpoint || statusCode || requestId) && (
        <div>
          <button
            type="button"
            className="text-xs text-[var(--muted-foreground)] hover:text-[var(--foreground)] flex items-center gap-1 border-0 bg-transparent p-0"
            onClick={() => setDetailsOpen((v) => !v)}
            aria-expanded={detailsOpen}
          >
            <span>{detailsOpen ? '▼ Hide' : '▶ Show'} Technical Diagnostics</span>
          </button>

          {detailsOpen && (
            <pre
              className="mt-2 text-[11px] font-mono p-3 rounded border border-[var(--border)] overflow-x-auto"
              style={{ background: 'var(--surface-secondary)', color: 'var(--muted-foreground)' }}
            >
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
    </Card>
  )
}
