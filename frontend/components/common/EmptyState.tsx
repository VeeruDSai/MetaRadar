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
    <div className="rounded-xl border border-dashed border-slate-800 bg-slate-900/20 p-8 text-center space-y-3">
      {icon ? (
        <div className="mx-auto flex h-10 w-10 items-center justify-center text-slate-500">
          {icon}
        </div>
      ) : (
        <div className="mx-auto flex h-10 w-10 items-center justify-center rounded-full bg-slate-800/60 text-slate-400">
          ∅
        </div>
      )}
      <div className="space-y-1">
        <h4 className="text-sm font-medium text-slate-300">{title}</h4>
        {description && <p className="text-xs text-slate-500 max-w-md mx-auto">{description}</p>}
      </div>
      {actionLabel && onAction && (
        <button
          onClick={onAction}
          className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-xs font-medium text-slate-200 transition"
        >
          {actionLabel}
        </button>
      )}
    </div>
  )
}
