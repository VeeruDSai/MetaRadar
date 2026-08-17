'use client'

import { useState, useEffect, useCallback, useRef } from 'react'

export interface LiveDataState<T> {
  data: T | null
  loading: boolean
  isRefreshing: boolean
  error: Error | null
  lastUpdated: Date | null
  refetch: () => Promise<void>
}

/**
 * Custom React hook for concurrency-safe, visibility-aware polling.
 * - Polls at intervalMs (default 30s)
 * - Automatically pauses when browser tab is hidden (document.visibilityState === 'hidden')
 * - Immediately refreshes upon tab refocus
 * - Uses AbortController and in-flight tracking to prevent overlapping/stale requests
 */
export function useLiveData<T>(
  fetcher: (signal?: AbortSignal) => Promise<T>,
  intervalMs = 30000
): LiveDataState<T> {
  const [data, setData] = useState<T | null>(null)
  const [loading, setLoading] = useState<boolean>(true)
  const [isRefreshing, setIsRefreshing] = useState<boolean>(false)
  const [error, setError] = useState<Error | null>(null)
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null)

  const fetcherRef = useRef(fetcher)
  fetcherRef.current = fetcher

  const inFlightRef = useRef<boolean>(false)
  const abortControllerRef = useRef<AbortController | null>(null)

  const executeFetch = useCallback(async (isInitial = false) => {
    // If a fetch is already in flight, skip to avoid queueing duplicate requests
    if (inFlightRef.current) return

    // Cancel any previous pending abort controller
    if (abortControllerRef.current) {
      abortControllerRef.current.abort()
    }
    const controller = new AbortController()
    abortControllerRef.current = controller
    inFlightRef.current = true

    if (isInitial) {
      setLoading(true)
    } else {
      setIsRefreshing(true)
    }

    try {
      const result = await fetcherRef.current(controller.signal)
      // Check if aborted before updating state
      if (!controller.signal.aborted) {
        setData(result)
        setError(null)
        setLastUpdated(new Date())
      }
    } catch (err) {
      if (!controller.signal.aborted) {
        setError(err instanceof Error ? err : new Error(String(err)))
      }
    } finally {
      if (!controller.signal.aborted) {
        setLoading(false)
        setIsRefreshing(false)
      }
      inFlightRef.current = false
    }
  }, [])

  const refetch = useCallback(() => executeFetch(false), [executeFetch])

  useEffect(() => {
    // Execute initial fetch
    executeFetch(true)

    // Guard SSR
    if (typeof window === 'undefined' || typeof document === 'undefined') {
      return
    }

    let timer: NodeJS.Timeout | null = null

    const startPolling = () => {
      if (timer) clearInterval(timer)
      timer = setInterval(() => {
        if (document.visibilityState === 'visible') {
          executeFetch(false)
        }
      }, intervalMs)
    }

    const handleVisibilityChange = () => {
      if (document.visibilityState === 'visible') {
        executeFetch(false)
        startPolling()
      } else {
        if (timer) {
          clearInterval(timer)
          timer = null
        }
        if (abortControllerRef.current) {
          abortControllerRef.current.abort()
        }
        inFlightRef.current = false
      }
    }

    startPolling()
    document.addEventListener('visibilitychange', handleVisibilityChange)

    return () => {
      if (timer) clearInterval(timer)
      document.removeEventListener('visibilitychange', handleVisibilityChange)
      if (abortControllerRef.current) {
        abortControllerRef.current.abort()
      }
      inFlightRef.current = false
    }
  }, [executeFetch, intervalMs])

  return { data, loading, isRefreshing, error, lastUpdated, refetch }
}
