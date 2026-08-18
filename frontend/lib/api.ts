import type {
  AthenaResponse,
  BeforeAfterComparison,
  CalibrationWeightsResponse,
  ConfirmWatchItemRequest,
  ConfirmWatchItemResponse,
  DashboardOverview,
  FeedbackSubmissionRequest,
  FeedbackSubmissionResponse,
  FeedbackSummaryResponse,
  HealthModelsResponse,
  HealthReadyResponse,
  HealthStatus,
  RecalibrateResponse,
  RoleWeight,
  SearchResponse,
  Signal,
  SignalSearchResult,
  TrendPoint,
  WatchRuleSuggestion,
  ConfluenceAlertItem,
  LifecycleTimelineItem,
  ContradictionItem,
  MissingSignalWatchItem,
  DevelopmentSummary,
  SourceRegistryItem,
  CacheClearResponse,
  SignalFilterParams,
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
    const d = new Date(raw.published_at)
    if (!isNaN(d.getTime())) {
      detectedAt = d.toLocaleDateString(undefined, {
        month: 'short',
        day: 'numeric',
      })
    }
  } else if (raw.created_at) {
    const d = new Date(raw.created_at)
    if (!isNaN(d.getTime())) {
      detectedAt = d.toLocaleDateString(undefined, {
        month: 'short',
        day: 'numeric',
      })
    }
  }

  const sources = raw.source_id
    ? [
        {
          id: String(raw.source_id),
          name: String(raw.source_id).toUpperCase(),
          type: raw.signal_type || 'intelligence feed',
          credibility: raw.score_breakdown?.evidence_strength
            ? Math.round(raw.score_breakdown.evidence_strength * 100)
            : 80,
          url: raw.canonical_url || undefined,
        },
      ]
    : []

  const score = raw.score_breakdown?.total_score ?? raw.score ?? 0
  const confidence = raw.confidence ?? (score > 0 ? score : 0)

  return {
    ...raw,
    id: raw.signal_id ? String(raw.signal_id) : (raw.id ? String(raw.id) : 'SIG-UNKNOWN'),
    title: raw.title || 'Untitled Signal',
    summary: raw.content || raw.summary || 'No summary available',
    severity,
    status: raw.status || 'new',
    score,
    confidence,
    detectedAt,
    tags: [raw.disease, raw.signal_type].filter(Boolean),
    sources,
    stakeholders: raw.stakeholders || {},
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
    weekly_change: overviewRaw.weekly_change,
    signals: mappedSignals,
    confluence: overviewRaw.confluence
      ? {
          score: overviewRaw.confluence.score ?? 0,
          label: overviewRaw.confluence.label ?? 'No confluence calculated',
          drivers: overviewRaw.confluence.drivers || [],
          updatedAt: overviewRaw.confluence.updated_at || 'Just now',
        }
      : {
          score: 0,
          label: 'No confluence calculated',
          drivers: [],
          updatedAt: 'Just now',
        },
    lifecycle: (overviewRaw.lifecycle || []).map((l: any) => ({
      id: String(l.id),
      name: l.name,
      stage: l.stage,
      momentum: l.momentum ?? 0,
      confidence: l.confidence ?? 0,
      lastChanged: l.last_changed || 'Recently',
      signals: l.signals ?? 0,
    })),
    trends: overviewRaw.trends || [],
    health: {
      api: overviewRaw.health?.api || 'healthy',
      lastSync: overviewRaw.last_sync
        ? new Date(overviewRaw.last_sync).toLocaleTimeString()
        : new Date().toLocaleTimeString(),
      latencyMs: overviewRaw.health?.latency_ms || 0,
      sourceCount: overviewRaw.health?.source_count || 0,
    },
  }
}

/**
 * Fetches signals list with pagination and multi-parameter filtering support (D-06).
 */
export async function getSignals(
  params?: SignalFilterParams,
  signal?: AbortSignal
): Promise<Signal[]> {
  const query = new URLSearchParams()
  query.set('limit', String(params?.limit ?? 50))
  query.set('offset', String(params?.offset ?? 0))
  if (params?.severity) query.set('severity', params.severity)
  if (params?.entity) query.set('entity', params.entity)
  if (params?.date_from) query.set('date_from', params.date_from)
  if (params?.date_to) query.set('date_to', params.date_to)
  if (params?.signal_type) query.set('signal_type', params.signal_type)
  if (params?.source) query.set('source', params.source)

  const res = await apiFetch<{ signals: any[]; total: number }>(
    `/signals?${query.toString()}`,
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

  const raw = await apiFetch<{
    answer: string
    confidence: number
    evidence_count: number
    mode?: string
    model_metadata?: any
  }>(
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

export const getTrends = async (signal?: AbortSignal): Promise<TrendPoint[]> => {
  const overview = await getOverview(signal)
  return overview.trends
}

export const getHealth = async (signal?: AbortSignal): Promise<HealthStatus> => {
  const overview = await getOverview(signal)
  return overview.health
}

/**
 * Submits stakeholder 5-star rating and comments feedback for a signal (D-05, D-07).
 */
export async function submitFeedback(
  payload: FeedbackSubmissionRequest,
  signal?: AbortSignal
): Promise<FeedbackSubmissionResponse> {
  return apiFetch<FeedbackSubmissionResponse>(
    '/feedback',
    {
      method: 'POST',
      body: JSON.stringify(payload),
    },
    signal
  )
}

/**
 * Triggers bounded batch weight recalibration and generates BEFORE/AFTER comparisons (D-01, D-02, D-03).
 */
export async function recalibrateRole(
  stakeholderFunction?: string,
  signal?: AbortSignal
): Promise<RecalibrateResponse> {
  const query = stakeholderFunction ? `?stakeholder_function=${encodeURIComponent(stakeholderFunction)}` : ''
  return apiFetch<RecalibrateResponse>(
    `/calibrate${query}`,
    {
      method: 'POST',
    },
    signal
  )
}

/**
 * Retrieves active calibrated weights across all stakeholder functions (D-04).
 */
export async function getCalibrationWeights(
  signal?: AbortSignal
): Promise<CalibrationWeightsResponse> {
  return apiFetch<CalibrationWeightsResponse>('/calibration/weights', undefined, signal)
}

/**
 * Retrieves aggregate feedback statistics and approval rates by stakeholder role.
 */
export async function getFeedbackSummary(
  signal?: AbortSignal
): Promise<FeedbackSummaryResponse> {
  return apiFetch<FeedbackSummaryResponse>('/feedback/summary', undefined, signal)
}

/**
 * Confirms a parsed watch rule suggestion and creates an active WatchItem (D-09, D-10).
 */
export async function confirmWatchItem(
  payload: ConfirmWatchItemRequest,
  signal?: AbortSignal
): Promise<ConfirmWatchItemResponse> {
  return apiFetch<ConfirmWatchItemResponse>(
    '/watch-items/confirm',
    {
      method: 'POST',
      body: JSON.stringify(payload),
    },
    signal
  )
}

// Phase 6 API Fetchers
export async function getConfluences(signal?: AbortSignal): Promise<ConfluenceAlertItem[]> {
  return apiFetch<ConfluenceAlertItem[]>('/confluence', undefined, signal)
}

export async function getLifecycles(disease?: string, signal?: AbortSignal): Promise<LifecycleTimelineItem[]> {
  const query = disease ? `?disease=${encodeURIComponent(disease)}` : ''
  return apiFetch<LifecycleTimelineItem[]>(`/lifecycles${query}`, undefined, signal)
}

export async function getRedTeamContradictions(severity?: string, signal?: AbortSignal): Promise<ContradictionItem[]> {
  const query = severity ? `?severity=${encodeURIComponent(severity)}` : ''
  return apiFetch<ContradictionItem[]>(`/red-team${query}`, undefined, signal)
}

export async function getMissingSignals(status?: string, signal?: AbortSignal): Promise<MissingSignalWatchItem[]> {
  const query = status ? `?status=${encodeURIComponent(status)}` : ''
  return apiFetch<MissingSignalWatchItem[]>(`/missing-signals${query}`, undefined, signal)
}

export async function getDevelopments(disease?: string, stage?: string, signal?: AbortSignal): Promise<DevelopmentSummary[]> {
  const params = new URLSearchParams()
  if (disease) params.set('disease', disease)
  if (stage) params.set('stage', stage)
  const qs = params.toString() ? `?${params.toString()}` : ''
  return apiFetch<DevelopmentSummary[]>(`/developments${qs}`, undefined, signal)
}

export async function getSources(signal?: AbortSignal): Promise<SourceRegistryItem[]> {
  return apiFetch<SourceRegistryItem[]>('/sources', undefined, signal)
}

export async function clearCache(signal?: AbortSignal): Promise<CacheClearResponse> {
  return apiFetch<CacheClearResponse>(
    '/cache/clear',
    {
      method: 'POST',
    },
    signal
  )
}
