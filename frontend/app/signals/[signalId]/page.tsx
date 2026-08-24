'use client'

import React, { useEffect, useState } from 'react'
import { useParams, useRouter } from 'next/navigation'
import { Shell } from '@/components/metaradar'
import { SignalDetailWorkspace } from '@/components/signals/SignalDetailWorkspace'
import { fetchSignal, fetchSignals, getConfluences, getRedTeamContradictions } from '@/lib/api'
import type { Signal, ConfluenceAlertItem, ContradictionItem } from '@/types/api'
import { ArrowLeft, RefreshCw } from 'lucide-react'
import Link from 'next/link'

export default function SignalDetailPage() {
  const params = useParams()
  const router = useRouter()
  const rawId = params?.signalId as string
  const signalId = rawId ? decodeURIComponent(rawId) : ''

  const [signal, setSignal] = useState<Signal | null>(null)
  const [confluences, setConfluences] = useState<ConfluenceAlertItem[]>([])
  const [contradictions, setContradictions] = useState<ContradictionItem[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!signalId) return

    let isMounted = true
    const controller = new AbortController()

    async function loadData() {
      setLoading(true)
      setError(null)
      try {
        // Try fetching single signal detail by ID
        let foundSignal: Signal | null = null
        try {
          foundSignal = await fetchSignal(signalId, controller.signal)
        } catch (fetchErr) {
          // If direct endpoint failed, search in recent signals list
          const listRes = await fetchSignals({ limit: 50 }, controller.signal)
          foundSignal =
            listRes.signals.find(
              (s) =>
                s.id === signalId ||
                s.signal_id === signalId ||
                s.external_id === signalId ||
                s.fingerprint === signalId ||
                s.pmid === signalId ||
                s.nct_id === signalId
            ) || null
        }

        if (!foundSignal) {
          throw new Error(`Signal with identifier "${signalId}" could not be found.`)
        }

        // Fetch supporting confluences and contradictions
        const [confs, contra] = await Promise.all([
          getConfluences(50, controller.signal).catch(() => []),
          getRedTeamContradictions(undefined, 50, controller.signal).catch(() => []),
        ])

        if (isMounted) {
          setSignal(foundSignal)
          setConfluences(confs)
          setContradictions(contra)
          setLoading(false)
        }
      } catch (err: any) {
        if (isMounted && !controller.signal.aborted) {
          setError(err?.message || 'Failed to load signal detail.')
          setLoading(false)
        }
      }
    }

    loadData()

    return () => {
      isMounted = false
      controller.abort()
    }
  }, [signalId])

  if (loading) {
    return (
      <Shell>
        <div className="flex flex-col items-center justify-center min-h-[400px] gap-3">
          <RefreshCw size={24} className="animate-spin text-[var(--primary)]" />
          <span className="text-xs text-[var(--muted-foreground)]">Loading signal intelligence...</span>
        </div>
      </Shell>
    )
  }

  if (error || !signal) {
    return (
      <Shell>
        <div className="flex flex-col items-center justify-center min-h-[400px] gap-4 text-center max-w-md mx-auto">
          <div className="p-4 rounded-full bg-[var(--danger)]/10 text-[var(--danger)]">
            <ArrowLeft size={24} />
          </div>
          <div>
            <h2 className="text-base font-bold text-[var(--foreground)] mb-1">Signal Not Found</h2>
            <p className="text-xs text-[var(--muted-foreground)] m-0">
              {error || `Unable to locate signal with ID ${signalId}`}
            </p>
          </div>
          <Link
            href="/signals"
            className="px-4 py-2 text-xs font-semibold rounded-md bg-[var(--primary)] text-[var(--primary-foreground)] hover:opacity-90 transition"
          >
            Return to Signals Workspace
          </Link>
        </div>
      </Shell>
    )
  }

  return (
    <Shell>
      <SignalDetailWorkspace
        signal={signal}
        confluences={confluences}
        contradictions={contradictions}
      />
    </Shell>
  )
}
