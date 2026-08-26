'use client'

import React, { useState, useEffect } from 'react'
import { UserCheck, ChevronDown, ShieldAlert } from 'lucide-react'

export interface DemoOperator {
  value: string
  label: string
  functionId: string
  badgeTone: string
}

export const DEMO_OPERATORS: DemoOperator[] = [
  {
    value: 'Demo Medical Affairs Reviewer',
    label: 'Medical Affairs',
    functionId: 'MEDICAL_AFFAIRS',
    badgeTone: 'var(--primary)',
  },
  {
    value: 'Demo Regulatory Affairs Reviewer',
    label: 'Regulatory Affairs',
    functionId: 'REGULATORY',
    badgeTone: 'var(--success)',
  },
  {
    value: 'Demo Safety Reviewer',
    label: 'Safety / Pharmacovigilance',
    functionId: 'SAFETY',
    badgeTone: 'var(--priority-critical)',
  },
  {
    value: 'Demo Market Access Reviewer',
    label: 'Market Access',
    functionId: 'MARKET_ACCESS',
    badgeTone: 'var(--warning)',
  },
  {
    value: 'Demo Communications Reviewer',
    label: 'Medical Communications',
    functionId: 'COMMUNICATIONS',
    badgeTone: 'var(--primary)',
  },
  {
    value: 'Demo Leadership Reviewer',
    label: 'Executive Leadership',
    functionId: 'LEADERSHIP',
    badgeTone: 'var(--priority-critical)',
  },
]

const STORAGE_KEY = 'metaradar_demo_operator'
const DEFAULT_OPERATOR = DEMO_OPERATORS[0].value

export function useDemoOperator() {
  const [operator, setOperator] = useState<string>(DEFAULT_OPERATOR)
  const [isHydrated, setIsHydrated] = useState(false)

  useEffect(() => {
    try {
      const stored = sessionStorage.getItem(STORAGE_KEY)
      if (stored) {
        setOperator(stored)
      }
    } catch {
      // sessionStorage not available (SSR or privacy mode)
    }
    setIsHydrated(true)
  }, [])

  const changeOperator = (newOp: string) => {
    setOperator(newOp)
    try {
      sessionStorage.setItem(STORAGE_KEY, newOp)
    } catch {
      // ignore
    }
    // Dispatch storage event for other components listening
    window.dispatchEvent(new Event('demo_operator_changed'))
  }

  return { operator, changeOperator, isHydrated }
}

export function DemoOperatorSelector() {
  const { operator, changeOperator, isHydrated } = useDemoOperator()
  const [isOpen, setIsOpen] = useState(false)

  // Close dropdown on outside click
  useEffect(() => {
    const handleOutsideClick = (e: MouseEvent) => {
      const target = e.target as HTMLElement
      if (!target.closest('#demo-operator-dropdown-container')) {
        setIsOpen(false)
      }
    }
    if (isOpen) {
      document.addEventListener('click', handleOutsideClick)
    }
    return () => document.removeEventListener('click', handleOutsideClick)
  }, [isOpen])

  const currentOp = DEMO_OPERATORS.find((o) => o.value === operator) || DEMO_OPERATORS[0]

  return (
    <div id="demo-operator-dropdown-container" className="relative inline-block text-left">
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-semibold bg-[var(--surface-secondary)] text-[var(--foreground)] border border-[var(--border)] hover:border-[var(--primary)]/50 transition-colors shadow-xs"
        title="Demo Reviewer Persona — used for workflow demonstration"
        aria-label="Select Demo Reviewer Role"
      >
        <span className="inline-flex items-center gap-1 text-[var(--warning)]">
          <UserCheck size={13} />
          <span className="uppercase text-[9px] font-bold tracking-wider">Demo Role:</span>
        </span>
        <span className="font-bold text-[var(--foreground)] truncate max-w-[140px]">
          {isHydrated ? currentOp.label : DEMO_OPERATORS[0].label}
        </span>
        <ChevronDown size={12} className="text-[var(--muted-foreground)] ml-0.5" />
      </button>

      {isOpen && (
        <div className="absolute right-0 mt-1.5 w-64 rounded-[var(--radius-md,8px)] bg-[var(--surface)] border border-[var(--border)] shadow-lg z-50 py-1.5 animate-in fade-in-50 zoom-in-95">
          <div className="px-3 py-1.5 border-b border-[var(--border)] mb-1">
            <span className="text-[10px] uppercase font-bold tracking-wider text-[var(--muted-foreground)] block">
              Simulate Reviewer Persona
            </span>
            <span className="text-[11px] text-[var(--muted-foreground)] block mt-0.5 leading-tight">
              Select an organizational role to test queue actions and audit recording.
            </span>
          </div>

          <div className="flex flex-col">
            {DEMO_OPERATORS.map((op) => {
              const isSelected = operator === op.value
              return (
                <button
                  key={op.value}
                  type="button"
                  onClick={() => {
                    changeOperator(op.value)
                    setIsOpen(false)
                  }}
                  className={`flex items-center justify-between px-3 py-2 text-xs text-left transition-colors ${
                    isSelected
                      ? 'bg-[var(--surface-secondary)] text-[var(--primary)] font-bold'
                      : 'text-[var(--foreground)] hover:bg-[var(--surface-secondary)]/60'
                  }`}
                >
                  <div className="flex flex-col">
                    <span className="font-semibold">{op.label}</span>
                    <span className="text-[10px] text-[var(--muted-foreground)] font-mono">
                      {op.functionId}
                    </span>
                  </div>
                  {isSelected && (
                    <span className="text-[10px] font-bold px-1.5 py-0.5 rounded bg-[var(--primary)]/10 text-[var(--primary)] border border-[var(--primary)]/20">
                      Active
                    </span>
                  )}
                </button>
              )
            })}
          </div>
        </div>
      )}
    </div>
  )
}
