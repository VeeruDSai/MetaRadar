'use client'

import React, { useState, useRef, useEffect } from 'react'
import { useAuth } from '@/context/AuthContext'

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
    label: 'Pharmacovigilance',
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
    badgeColor: 'bg-slate-500/15 dark:bg-slate-500/20',
    textColor: 'text-slate-700 dark:text-slate-300',
    borderColor: 'border-slate-500/30',
  },
]

export function PersonaSwitcher() {
  const { user, role, demoLogin, isLoading } = useAuth()
  const [isOpen, setIsOpen] = useState(false)
  const menuRef = useRef<HTMLDivElement>(null)

  const activePersona = PERSONAS.find((p) => p.id === role) || PERSONAS[0]

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
        setIsOpen(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  const handleSelect = async (personaId: string) => {
    if (personaId === role) {
      setIsOpen(false)
      return
    }
    try {
      await demoLogin(personaId)
    } catch {
      // Error handled in AuthContext
    } finally {
      setIsOpen(false)
    }
  }

  return (
    <div className="relative inline-block text-left" ref={menuRef}>
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        disabled={isLoading}
        aria-haspopup="true"
        aria-expanded={isOpen}
        className={`flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-semibold border transition-all duration-150 ${activePersona.badgeColor} ${activePersona.textColor} ${activePersona.borderColor} hover:opacity-90 active:scale-95 disabled:opacity-50`}
        title={`Logged in as ${user?.display_name || activePersona.label}. Click to switch stakeholder persona.`}
      >
        <span className="w-2 h-2 rounded-full bg-current animate-pulse" />
        <span>{activePersona.label}</span>
        {user?.display_name && (
          <span className="opacity-70 font-normal hidden md:inline">({user.display_name})</span>
        )}
        <svg
          className={`w-3 h-3 transition-transform duration-200 ${isOpen ? 'rotate-180' : ''}`}
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {isOpen && (
        <div
          className="absolute right-0 mt-2 w-72 origin-top-right rounded-xl bg-card border border-border shadow-xl ring-1 ring-black/5 focus:outline-none z-50 overflow-hidden animate-in fade-in zoom-in-95 duration-100"
          role="menu"
        >
          <div className="px-3 py-2 border-b border-border bg-muted/30">
            <div className="text-[11px] font-semibold tracking-wider text-muted-foreground uppercase">
              Switch Stakeholder Persona (Demo)
            </div>
            <div className="text-[10px] text-muted-foreground mt-0.5">
              Live role scoping, permissions & queue isolation
            </div>
          </div>
          <div className="p-1.5 space-y-0.5">
            {PERSONAS.map((p) => {
              const isSelected = p.id === role
              return (
                <button
                  key={p.id}
                  type="button"
                  onClick={() => handleSelect(p.id)}
                  className={`w-full text-left px-3 py-2 rounded-lg text-xs transition-colors flex items-start justify-between gap-2 ${
                    isSelected
                      ? `${p.badgeColor} ${p.textColor} font-semibold border ${p.borderColor}`
                      : 'hover:bg-muted text-foreground'
                  }`}
                  role="menuitem"
                >
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-1.5">
                      <span className="truncate">{p.label}</span>
                      {isSelected && (
                        <span className="text-[10px] uppercase font-bold tracking-wider px-1.5 py-0.2 rounded-full bg-current/20">
                          Active
                        </span>
                      )}
                    </div>
                    <p className="text-[10px] text-muted-foreground line-clamp-1 mt-0.5">
                      {p.description}
                    </p>
                  </div>
                </button>
              )
            })}
          </div>
        </div>
      )}
    </div>
  )
}
