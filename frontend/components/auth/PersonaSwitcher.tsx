'use client'

import React from 'react'
import { useAuth } from '@/context/AuthContext'
import { LogOut } from 'lucide-react'

export interface PersonaOption {
  id: string
  label: string
  description: string
  badgeColor: string
  textColor: string
  borderColor: string
}

export const PERSONAS: PersonaOption[] = [
  {
    id: 'DEVELOPER',
    label: 'Developer / Engineer',
    description: 'Full stack development, telemetry & platform administration',
    badgeColor: 'bg-cyan-500/15 dark:bg-cyan-500/20',
    textColor: 'text-cyan-700 dark:text-cyan-300',
    borderColor: 'border-cyan-500/30',
  },
  {
    id: 'MEDICAL_AFFAIRS',
    label: 'Medical Affairs',
    description: 'Evidence evaluation & clinical advisory',
    badgeColor: 'bg-emerald-500/15 dark:bg-emerald-500/20',
    textColor: 'text-emerald-700 dark:text-emerald-300',
    borderColor: 'border-emerald-500/30',
  },
  {
    id: 'REGULATORY',
    label: 'Regulatory Affairs',
    description: 'Labeling, filings & agency compliance',
    badgeColor: 'bg-blue-500/15 dark:bg-blue-500/20',
    textColor: 'text-blue-700 dark:text-blue-300',
    borderColor: 'border-blue-500/30',
  },
  {
    id: 'SAFETY',
    label: 'Safety & PV',
    description: 'Adverse event & safety triage',
    badgeColor: 'bg-rose-500/15 dark:bg-rose-500/20',
    textColor: 'text-rose-700 dark:text-rose-300',
    borderColor: 'border-rose-500/30',
  },
  {
    id: 'MARKET_ACCESS',
    label: 'Market Access',
    description: 'Reimbursement & health economics',
    badgeColor: 'bg-amber-500/15 dark:bg-amber-500/20',
    textColor: 'text-amber-700 dark:text-amber-300',
    borderColor: 'border-amber-500/30',
  },
  {
    id: 'COMMUNICATIONS',
    label: 'Communications',
    description: 'Scientific narrative & PR messaging',
    badgeColor: 'bg-purple-500/15 dark:bg-purple-500/20',
    textColor: 'text-purple-700 dark:text-purple-300',
    borderColor: 'border-purple-500/30',
  },
  {
    id: 'LEADERSHIP',
    label: 'Executive Leadership',
    description: 'Cross-functional portfolio & escalation steer',
    badgeColor: 'bg-indigo-500/15 dark:bg-indigo-500/20',
    textColor: 'text-indigo-700 dark:text-indigo-300',
    borderColor: 'border-indigo-500/30',
  },
  {
    id: 'ADMIN',
    label: 'System Admin',
    description: 'Platform configuration & security overrides',
    badgeColor: 'bg-muted/60',
    textColor: 'text-muted-foreground',
    borderColor: 'border-border/50',
  },
]

export function PersonaSwitcher() {
  const { user, role, logout } = useAuth()
  const activePersona = PERSONAS.find((p) => p.id === role) || PERSONAS[0]

  return (
    <div className="flex items-center gap-2">
      <div
        className={`flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-semibold border ${activePersona.badgeColor} ${activePersona.textColor} ${activePersona.borderColor}`}
        title={`Authenticated as ${user?.display_name || activePersona.label}`}
      >
        <span className="w-2 h-2 rounded-full bg-current animate-pulse" />
        <span>{activePersona.label}</span>
      </div>

      {user?.display_name && (
        <span className="text-xs text-[var(--muted-foreground)] font-medium hidden md:inline max-w-[140px] truncate">
          {user.display_name.split(' ')[0]} {user.display_name.split(' ')[1] || ''}
        </span>
      )}

      <button
        type="button"
        onClick={() => logout()}
        aria-label="Sign Out"
        title="Sign Out to Login Page"
        className="flex items-center justify-center p-1.5 rounded-lg text-[var(--muted-foreground)] hover:text-[var(--foreground)] hover:bg-[var(--surface-hover)] border border-transparent hover:border-[var(--border)] transition-colors"
      >
        <LogOut className="w-4 h-4" />
      </button>
    </div>
  )
}
