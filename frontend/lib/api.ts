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
  SourceHealthLogItem,
  ActivityLogItem,
  CacheClearResponse,
  SignalFilterParams,
} from '@/types/api'

import { ApiError } from './errors'
import { mapSignal } from './mappers'

export { ApiError, mapSignal }

// Aliases for seamless backward compatibility across UI components
export const getOverview = fetchOverview

export async function getHealthReady(signal?: AbortSignal): Promise<HealthReadyResponse> {
  return apiFetch<HealthReadyResponse>('/health/ready', undefined, signal)
}

export async function getSignals(
  filters?: SignalFilterParams | AbortSignal,
  signal?: AbortSignal
): Promise<Signal[]> {
  const actualFilters = filters instanceof AbortSignal ? undefined : filters
  const actualSignal = filters instanceof AbortSignal ? filters : signal
  const res = await fetchSignals(actualFilters, actualSignal)
  return res.signals
}

export async function getConfluences(
  limitOrSignal?: number | AbortSignal,
  signal?: AbortSignal
): Promise<ConfluenceAlertItem[]> {
  const limit = typeof limitOrSignal === 'number' ? limitOrSignal : 50
  const actualSignal = limitOrSignal instanceof AbortSignal ? limitOrSignal : signal
  return fetchConfluenceAlerts(limit, actualSignal)
}

export async function getLifecycles(
  diseaseOrSignal?: string | AbortSignal,
  limitOrSignal?: number | AbortSignal,
  maybeSignal?: AbortSignal
): Promise<LifecycleTimelineItem[]> {
  const disease = typeof diseaseOrSignal === 'string' ? diseaseOrSignal : undefined
  const limit = typeof limitOrSignal === 'number' ? limitOrSignal : 50
  const actualSignal =
    diseaseOrSignal instanceof AbortSignal
      ? diseaseOrSignal
      : limitOrSignal instanceof AbortSignal
      ? limitOrSignal
      : maybeSignal
  return fetchLifecycleTimelines(disease, limit, actualSignal)
}

export async function getRedTeamContradictions(
  severityOrSignal?: string | AbortSignal,
  limitOrSignal?: number | AbortSignal,
  maybeSignal?: AbortSignal
): Promise<ContradictionItem[]> {
  const severity = typeof severityOrSignal === 'string' ? severityOrSignal : undefined
  const limit = typeof limitOrSignal === 'number' ? limitOrSignal : 50
  const actualSignal =
    severityOrSignal instanceof AbortSignal
      ? severityOrSignal
      : limitOrSignal instanceof AbortSignal
      ? limitOrSignal
      : maybeSignal
  return fetchRedTeamContradictions(severity, limit, actualSignal)
}

export async function getMissingSignals(
  statusOrSignal?: string | AbortSignal,
  limitOrSignal?: number | AbortSignal,
  maybeSignal?: AbortSignal
): Promise<MissingSignalWatchItem[]> {
  const status = typeof statusOrSignal === 'string' ? statusOrSignal : undefined
  const limit = typeof limitOrSignal === 'number' ? limitOrSignal : 50
  const actualSignal =
    statusOrSignal instanceof AbortSignal
      ? statusOrSignal
      : limitOrSignal instanceof AbortSignal
      ? limitOrSignal
      : maybeSignal
  return fetchMissingSignals(status, limit, actualSignal)
}

export async function getDevelopments(
  diseaseOrSignal?: string | AbortSignal,
  limit?: number,
  signal?: AbortSignal
): Promise<DevelopmentSummary[]> {
  const actualSignal = diseaseOrSignal instanceof AbortSignal ? diseaseOrSignal : signal
  return fetchDevelopments(limit || 50, actualSignal)
}

export const getSources = fetchSources
export const getCalibrationWeights = fetchCalibrationWeights
export const getFeedbackSummary = fetchFeedbackSummary
export const getHealthModels = fetchHealthModels
export const submitFeedback = submitSignalFeedback
export const recalibrateRole = triggerRecalibration

export function mapSearchResult(r: any): Signal {
  return mapSignal({
    signal_id: r.signal_id,
    title: r.title,
    content: r.content,
    signal_type: r.signal_type,
    disease: r.disease,
    priority: r.priority,
    // Only use the real similarity score; never invent a default relevance.
    score: typeof r.similarity_score === 'number' ? Math.round(r.similarity_score * 100) : 0,
    created_at: r.created_at,
  })
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1'

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

    const requestId = res.headers.get('x-request-id') || undefined

    if (!res.ok) {
      const errorText = await res.text().catch(() => '')
      throw new ApiError(
        res.status,
        res.statusText,
        `Request to ${endpoint} failed (${res.status}): ${errorText || res.statusText}`,
        res.status >= 500 || res.status === 429,
        requestId,
        endpoint
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
      true,
      undefined,
      endpoint
    )
  }
}

// ---------------------------------------------------------------------------
// 1. Dashboard Overview & Signals
// ---------------------------------------------------------------------------

export async function fetchOverview(signal?: AbortSignal): Promise<DashboardOverview> {
  const data = await apiFetch<any>('/overview', undefined, signal)

  // Fetch signals to populate full dashboard signals array
  const signalsData = await apiFetch<{ signals: any[]; total: number }>(
    '/signals?limit=10',
    undefined,
    signal
  ).catch(() => ({ signals: [], total: 0 }))

  const signals = (signalsData.signals || []).map(mapSignal)

  return {
    active_signals: data.active_signals,
    monitored_assets: data.monitored_assets,
    confluences_detected: data.confluences_detected,
    contradictions_flagged: data.contradictions_flagged,
    weekly_change: data.weekly_change,
    signals,
    confluence: {
      score: data.confluence?.score || 0,
      label: data.confluence?.label || 'No active confluences',
      drivers: data.confluence?.drivers || [],
      updatedAt: data.confluence?.updated_at || 'Just now',
    },
    lifecycle: (data.lifecycle || []).map((l: any) => ({
      id: l.id,
      name: l.name,
      stage: l.stage,
      momentum: l.momentum,
      confidence: l.confidence,
      lastChanged: l.last_changed || 'Recently',
      signals: l.signals || 0,
    })),
    trends: (data.trends || []).map((t: any) => ({
      label: t.label,
      value: t.value,
      baseline: t.baseline,
    })),
    health: {
      api: data.health?.api || 'healthy',
      lastSync: data.last_sync || data.health?.last_sync || 'Just now',
      latencyMs: data.health?.latency_ms ?? 0,
      sourceCount: data.health?.source_count ?? data.health?.sourceCount ?? 0,
    },
  }
}

export async function fetchSignals(
  filters?: SignalFilterParams,
  signal?: AbortSignal
): Promise<{ signals: Signal[]; total: number }> {
  const queryParams = new URLSearchParams()
  if (filters?.severity) queryParams.set('severity', filters.severity)
  if (filters?.entity) queryParams.set('entity', filters.entity)
  if (filters?.date_from) queryParams.set('date_from', filters.date_from)
  if (filters?.date_to) queryParams.set('date_to', filters.date_to)
  if (filters?.signal_type) queryParams.set('signal_type', filters.signal_type)
  if (filters?.source) queryParams.set('source', filters.source)
  if (filters?.limit) queryParams.set('limit', String(filters.limit))
  if (filters?.offset) queryParams.set('offset', String(filters.offset))

  const qs = queryParams.toString()
  const endpoint = qs ? `/signals?${qs}` : '/signals'

  const data = await apiFetch<{ signals: any[]; total: number }>(endpoint, undefined, signal)
  return {
    signals: (data.signals || []).map(mapSignal),
    total: data.total || 0,
  }
}

export async function askAthena(prompt: string, signal?: AbortSignal): Promise<AthenaResponse> {
  const res = await apiFetch<any>(
    '/athena',
    {
      method: 'POST',
      body: JSON.stringify({ prompt }),
    },
    signal
  )

  return {
    answer: res.answer,
    confidence: res.confidence,
    confidence_type: res.confidence_type,
    evidence_count: res.evidence_count,
    mode: res.mode,
    model_metadata: res.model_metadata,
    evidence: res.evidence || [],
    response_type: res.response_type,
  }
}

// ---------------------------------------------------------------------------
// 2. Health & Diagnostics
// ---------------------------------------------------------------------------

export async function fetchHealth(signal?: AbortSignal): Promise<HealthStatus> {
  const t0 = performance.now()
  const ready = await apiFetch<HealthReadyResponse>('/health/ready', undefined, signal).catch(() => ({
    status: 'degraded' as const,
    database: false,
    redis: false,
    timestamp: new Date().toISOString(),
  }))
  const latency = Math.round(performance.now() - t0)

  // Real connector count from the connectors health endpoint; 0 when the
  // telemetry is unavailable — never a hardcoded fabricated count.
  const connectors = await apiFetch<{ connectors?: unknown[] }>(
    '/health/connectors',
    undefined,
    signal
  ).catch(() => ({ connectors: [] as unknown[] }))
  const sourceCount = Array.isArray(connectors?.connectors) ? connectors.connectors.length : 0

  return {
    api: ready.status === 'ready' ? 'healthy' : 'degraded',
    lastSync: 'Live',
    latencyMs: latency,
    sourceCount,
  }
}

export async function fetchHealthModels(signal?: AbortSignal): Promise<HealthModelsResponse> {
  return apiFetch<HealthModelsResponse>('/health/models', undefined, signal)
}

export async function fetchHealthConnectors(signal?: AbortSignal): Promise<any> {
  return apiFetch<any>('/health/connectors', undefined, signal)
}

// ---------------------------------------------------------------------------
// 3. Search & Vector Retrieval
// ---------------------------------------------------------------------------

export async function searchSignals(
  query: string,
  filters?: any,
  signal?: AbortSignal
): Promise<SearchResponse> {
  return apiFetch<SearchResponse>(
    '/search',
    {
      method: 'POST',
      body: JSON.stringify({ query, filters, top_k: 20 }),
    },
    signal
  )
}

// ---------------------------------------------------------------------------
// 4. Stakeholder Feedback & Recalibration
// ---------------------------------------------------------------------------

export async function submitSignalFeedback(
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

export async function fetchFeedbackSummary(signal?: AbortSignal): Promise<FeedbackSummaryResponse> {
  return apiFetch<FeedbackSummaryResponse>('/feedback/summary', undefined, signal)
}

export async function fetchCalibrationWeights(signal?: AbortSignal): Promise<CalibrationWeightsResponse> {
  return apiFetch<CalibrationWeightsResponse>('/calibration/weights', undefined, signal)
}

export async function triggerRecalibration(
  stakeholderFunction?: string,
  signal?: AbortSignal
): Promise<RecalibrateResponse> {
  const queryParam = stakeholderFunction ? `?stakeholder_function=${encodeURIComponent(stakeholderFunction)}` : ''
  return apiFetch<RecalibrateResponse>(
    `/calibrate${queryParam}`,
    {
      method: 'POST',
    },
    signal
  )
}

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

// ---------------------------------------------------------------------------
// 5. Intelligence Views & Parity APIs
// ---------------------------------------------------------------------------

export async function fetchConfluenceAlerts(limit: number = 50, signal?: AbortSignal): Promise<ConfluenceAlertItem[]> {
  return apiFetch<ConfluenceAlertItem[]>(`/confluence?limit=${limit}`, undefined, signal)
}

export async function fetchLifecycleTimelines(
  disease?: string,
  limit: number = 50,
  signal?: AbortSignal
): Promise<LifecycleTimelineItem[]> {
  const q = disease ? `?disease=${encodeURIComponent(disease)}&limit=${limit}` : `?limit=${limit}`
  return apiFetch<LifecycleTimelineItem[]>(`/lifecycles${q}`, undefined, signal)
}

export async function fetchRedTeamContradictions(
  severity?: string,
  limit: number = 50,
  signal?: AbortSignal
): Promise<ContradictionItem[]> {
  const q = severity ? `?severity=${encodeURIComponent(severity)}&limit=${limit}` : `?limit=${limit}`
  return apiFetch<ContradictionItem[]>(`/red-team${q}`, undefined, signal)
}

export async function fetchMissingSignals(
  statusFilter?: string,
  limit: number = 50,
  signal?: AbortSignal
): Promise<MissingSignalWatchItem[]> {
  const q = statusFilter ? `?status=${encodeURIComponent(statusFilter)}&limit=${limit}` : `?limit=${limit}`
  return apiFetch<MissingSignalWatchItem[]>(`/missing-signals${q}`, undefined, signal)
}

export async function fetchDevelopments(limit: number = 50, signal?: AbortSignal): Promise<DevelopmentSummary[]> {
  return apiFetch<DevelopmentSummary[]>(`/developments?limit=${limit}`, undefined, signal)
}

export async function fetchSources(signal?: AbortSignal): Promise<SourceRegistryItem[]> {
  return apiFetch<SourceRegistryItem[]>('/sources', undefined, signal)
}

export async function fetchSourcesHealth(signal?: AbortSignal): Promise<SourceRegistryItem[]> {
  return apiFetch<SourceRegistryItem[]>('/sources/health', undefined, signal)
}

export async function fetchActivityLogs(limit: number = 50, signal?: AbortSignal): Promise<ActivityLogItem[]> {
  return apiFetch<ActivityLogItem[]>(`/observability/activity?limit=${limit}`, undefined, signal)
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

export async function triggerIngestionRun(
  connector_ids?: string[],
  force_backfill: boolean = false,
  signal?: AbortSignal
): Promise<any> {
  return apiFetch<any>(
    '/ingestion/run',
    {
      method: 'POST',
      body: JSON.stringify({ connector_ids, force_backfill }),
    },
    signal
  )
}

export async function triggerIngestAndPipelineSync(
  connector_ids?: string[],
  batch_size: number = 50,
  signal?: AbortSignal
): Promise<any> {
  return apiFetch<any>(
    '/ingestion/sync-live',
    {
      method: 'POST',
      body: JSON.stringify({ connector_ids, batch_size }),
    },
    signal
  )
}

export async function inspectConfluence(
  confluence_id: string,
  signal?: AbortSignal
): Promise<any> {
  return apiFetch<any>(`/confluence/${encodeURIComponent(confluence_id)}/inspect`, undefined, signal)
}
