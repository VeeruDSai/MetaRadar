'use client'

import React from 'react'

export interface EmptyStateProps {
  title: string
  description?: string
  actionLabel?: string
  onAction?: () => void
  icon?: React.ReactNode
}

export function EmptyState({
  title,
  description,
  actionLabel,
  onAction,
  icon,
}: EmptyStateProps) {
  return (
    <div className="rounded-xl border border-dashed border-[var(--border)] bg-[var(--surface-subtle)] p-8 text-center space-y-3">
      {icon ? (
        <div className="mx-auto flex h-10 w-10 items-center justify-center text-[var(--muted-foreground)]">
          {icon}
        </div>
      ) : (
        <div className="mx-auto flex h-10 w-10 items-center justify-center rounded-full bg-[var(--surface-muted)] text-[var(--muted-foreground)] text-sm">
          ∅
        </div>
      )}
      <div className="space-y-1">
        <h4 className="text-sm font-medium text-[var(--foreground)]">{title}</h4>
        {description && <p className="text-xs text-[var(--muted-foreground)] max-w-md mx-auto">{description}</p>}
      </div>
      {actionLabel && onAction && (
        <button
          onClick={onAction}
          className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-[var(--surface-muted)] hover:bg-[var(--surface-subtle)] text-xs font-medium text-[var(--foreground)] transition border border-[var(--border)]"
        >
          {actionLabel}
        </button>
      )}
    </div>
  )
}
