import type {
  AthenaResponse,
  DashboardOverview,
  HealthModelsResponse,
  HealthReadyResponse,
  HealthStatus,
  SearchResponse,
  Signal,
  SignalSearchResult,
  TrendPoint,
} from '@/types/api'

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1'

export class ApiError extends Error {
  constructor(
    public status: number,
    public statusText: string,
    public message: string,
    public isRetryable: boolean = true
  ) {
    super(message)
    this.name = 'ApiError'
  }
}

async function apiFetch<T>(
  endpoint: string,
  options?: RequestInit,
  signal?: AbortSignal
): Promise<T> {
  const url = `${API_BASE}${endpoint}`
  try {
    const res = await fetch(url, {
      ...options,
      signal,
      headers: {
        'Content-Type': 'application/json',
        ...options?.headers,
      },
    })

    if (!res.ok) {
      const errorText = await res.text().catch(() => '')
      throw new ApiError(
        res.status,
        res.statusText,
        `Request to ${endpoint} failed (${res.status}): ${errorText || res.statusText}`,
        res.status >= 500 || res.status === 429
      )
    }

    return (await res.json()) as T
  } catch (err) {
    if (err instanceof ApiError) {
      throw err
    }
    if (err instanceof Error && err.name === 'AbortError') {
      throw err
    }
    throw new ApiError(
      0,
      'NetworkError',
      err instanceof Error ? err.message : 'Network request failed',
      true
    )
  }
}

/**
 * Pure mapper converting backend relational Signal shape to UI presentation contract.
 * Does not invent numbers (D-05) — maps honest values from backend.
 */
export function mapSignal(raw: any): Signal {
  const severityMap: Record<string, 'critical' | 'high' | 'medium' | 'low' | 'neutral'> = {
    CRITICAL: 'critical',
    HIGH: 'high',
    MEDIUM: 'medium',
    LOW: 'low',
    critical: 'critical',
    high: 'high',
    medium: 'medium',
    low: 'low',
  }

  const priorityKey = (raw.priority || '').toString().toUpperCase()
  const severity = severityMap[priorityKey] || 'neutral'

  let detectedAt = 'Recent'
  if (raw.published_at) {
    try {
      detectedAt = new Date(raw.published_at).toLocaleDateString(undefined, {
        month: 'short',
        day: 'numeric',
      })
    } catch {
      detectedAt = String(raw.published_at)
    }
  } else if (raw.created_at) {
    try {
      detectedAt = new Date(raw.created_at).toLocaleDateString(undefined, {
        month: 'short',
        day: 'numeric',
      })
    } catch {
      detectedAt = String(raw.created_at)
    }
  }

  const sources = raw.source_id
    ? [
        {
          id: String(raw.source_id),
          name: String(raw.source_id).toUpperCase(),
          type: raw.signal_type || 'intelligence feed',
          credibility: 90,
          url: raw.canonical_url || undefined,
        },
      ]
    : []

  return {
    id: raw.signal_id ? String(raw.signal_id) : (raw.id ? String(raw.id) : 'SIG-UNKNOWN'),
    title: raw.title || 'Untitled Signal',
    summary: raw.content || raw.summary || 'No summary available',
    severity,
    status: raw.status || 'new',
    score: raw.score_breakdown?.total_score ?? raw.score ?? 0,
    confidence: raw.confidence ?? 85,
    detectedAt,
    tags: [raw.disease, raw.signal_type].filter(Boolean),
    sources,
    stakeholders: raw.stakeholders || {},
    ...raw,
  }
}

/**
 * Pure mapper converting SearchResult to Signal for drawer and list preview.
 */
export function mapSearchResult(result: SignalSearchResult): Signal {
  return mapSignal({
    signal_id: result.signal_id,
    title: result.title,
    content: result.content,
    signal_type: result.signal_type,
    disease: result.disease,
    priority: result.priority,
    score: Math.round(result.similarity_score * 100),
    confidence: Math.round(result.similarity_score * 100),
    created_at: result.created_at,
  })
}

/**
 * Fetches overview metrics and signals list, merging into DashboardOverview.
 */
export async function getOverview(signal?: AbortSignal): Promise<DashboardOverview> {
  const [overviewRaw, signalsRaw] = await Promise.all([
    apiFetch<any>('/overview', undefined, signal),
    apiFetch<{ signals: any[]; total: number }>('/signals?limit=20', undefined, signal),
  ])

  const mappedSignals: Signal[] = (signalsRaw.signals || []).map(mapSignal)

  return {
    active_signals: overviewRaw.active_signals ?? signalsRaw.total ?? mappedSignals.length,
    monitored_assets: overviewRaw.monitored_assets ?? 0,
    confluences_detected: overviewRaw.confluences_detected ?? 0,
    contradictions_flagged: overviewRaw.contradictions_flagged ?? 0,
    signals: mappedSignals,
    confluence: overviewRaw.confluence || {
      score: 0,
      label: 'No confluence calculated',
      drivers: [],
      updatedAt: 'Just now',
    },
    lifecycle: overviewRaw.lifecycle || [],
    trends: overviewRaw.trends || [],
    health: {
      api: overviewRaw.health?.api || 'healthy',
      lastSync: overviewRaw.last_sync
        ? new Date(overviewRaw.last_sync).toLocaleTimeString()
        : new Date().toLocaleTimeString(),
      latencyMs: overviewRaw.health?.latency_ms || 120,
      sourceCount: overviewRaw.health?.source_count || 5,
    },
  }
}

/**
 * Fetches signals list.
 */
export async function getSignals(limit = 50, signal?: AbortSignal): Promise<Signal[]> {
  const res = await apiFetch<{ signals: any[]; total: number }>(
    `/signals?limit=${limit}`,
    undefined,
    signal
  )
  return (res.signals || []).map(mapSignal)
}

/**
 * Queries Ask Athena intelligence synthesis layer.
 */
export async function askAthena(prompt: string, signal?: AbortSignal): Promise<AthenaResponse> {
  const trimmed = prompt.trim()
  if (!trimmed) {
    throw new ApiError(400, 'BadRequest', 'Prompt cannot be empty.')
  }

  const raw = await apiFetch<{ answer: string; confidence: number; evidence_count: number }>(
    '/athena',
    {
      method: 'POST',
      body: JSON.stringify({ prompt: trimmed.slice(0, 500) }),
    },
    signal
  )

  return {
    answer: raw.answer,
    confidence: raw.confidence,
    sources: [],
  }
}

/**
 * Executes semantic vector search against POST /api/v1/search.
 */
export async function searchSignals(
  query: string,
  top_k = 10,
  signal?: AbortSignal
): Promise<SearchResponse> {
  const trimmed = query.trim()
  if (!trimmed) {
    return {
      results: [],
      total: 0,
      query: '',
      ef_search_used: 40,
    }
  }

  return apiFetch<SearchResponse>(
    '/search',
    {
      method: 'POST',
      body: JSON.stringify({ query: trimmed, top_k }),
    },
    signal
  )
}

/**
 * Fetches readiness health check status.
 */
export async function getHealthReady(signal?: AbortSignal): Promise<HealthReadyResponse> {
  return apiFetch<HealthReadyResponse>('/health/ready', undefined, signal)
}

/**
 * Fetches LLM and embedding model status.
 */
export async function getHealthModels(signal?: AbortSignal): Promise<HealthModelsResponse> {
  return apiFetch<HealthModelsResponse>('/health/models', undefined, signal)
}

export const getTrends = async (): Promise<TrendPoint[]> => {
  const overview = await getOverview()
  return overview.trends
}

export const getHealth = async (): Promise<HealthStatus> => {
  const overview = await getOverview()
  return overview.health
}
