import type {
  AthenaEvidenceCitation,
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
  SignalReviewPayload,
  AuditLogItem,
  UserMe,
  LoginRequest,
  DemoLoginRequest,
  CsrfResponse,
  LogoutResponse,
  FunctionStatsResponse,
  FunctionCalibrationProfile,
  CalibrationStatusResponse,
  LeadershipSummaryResponse,
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

export async function getSignal(
  signalId: string,
  signal?: AbortSignal
): Promise<Signal> {
  return fetchSignal(signalId, signal)
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

function getCsrfCookie(): string | null {
  if (typeof document === 'undefined') return null
  const match = document.cookie.match(/(?:^|;\s*)metaradar_csrf=([^;]+)/)
  return match ? decodeURIComponent(match[1]) : null
}

let cachedCsrfToken: string | null = null

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1'

export async function fetchCsrfToken(signal?: AbortSignal): Promise<string> {
  try {
    const fetchOptions: RequestInit = {
      credentials: 'include',
    }
    if (typeof AbortSignal !== 'undefined' && signal instanceof AbortSignal) {
      fetchOptions.signal = signal
    }
    const res = await fetch(`${API_BASE}/auth/csrf`, fetchOptions)
    if (res.ok) {
      const data = (await res.json()) as CsrfResponse
      cachedCsrfToken = data.csrf_token
      return data.csrf_token
    }
  } catch {}
  return ''
}


async function apiFetch<T>(
  endpoint: string,
  options?: RequestInit,
  signal?: AbortSignal
): Promise<T> {
  const url = `${API_BASE}${endpoint}`
  try {
    const method = (options?.method || 'GET').toUpperCase()
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      ...(options?.headers as Record<string, string>),
    }

    // Attach CSRF token on mutating requests
    if (['POST', 'PUT', 'DELETE', 'PATCH'].includes(method)) {
      let csrf = getCsrfCookie() || cachedCsrfToken
      if (!csrf && typeof window !== 'undefined') {
        csrf = await fetchCsrfToken(signal)
      }
      if (csrf) {
        headers['X-CSRF-Token'] = csrf
      }
    }

    const fetchOptions: RequestInit = {
      ...options,
      credentials: 'include',
      headers,
    }
    // Only attach signal when it is a valid AbortSignal instance
    if (typeof AbortSignal !== 'undefined' && signal instanceof AbortSignal) {
      fetchOptions.signal = signal
    }
    const res = await fetch(url, fetchOptions)

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
  if (filters?.all_functions) queryParams.set('all_functions', 'true')

  const qs = queryParams.toString()
  const endpoint = qs ? `/signals?${qs}` : '/signals'

  const data = await apiFetch<{ signals: any[]; total: number }>(endpoint, undefined, signal)
  return {
    signals: (data.signals || []).map(mapSignal),
    total: data.total || 0,
  }
}

export async function fetchSignal(
  signalId: string,
  signal?: AbortSignal
): Promise<Signal> {
  const data = await apiFetch<any>(`/signals/${encodeURIComponent(signalId)}`, undefined, signal)
  return mapSignal(data)
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

export interface AthenaStreamMeta {
  evidence: AthenaEvidenceCitation[]
  evidence_count: number
  response_type?: string
}

export interface AthenaStreamHandlers {
  onMeta?: (meta: AthenaStreamMeta) => void
  onToken?: (delta: string) => void
  onDegraded?: (mode: string) => void
  onError?: (message: string) => void
}

/**
 * Streams an Athena answer live from POST /athena/stream (Server-Sent Events).
 * Event contract mirrors the backend endpoint: meta -> token* -> done,
 * with degraded/error as honest failure signals. Resolves when the stream ends.
 */
export async function streamAthena(
  prompt: string,
  handlers: AthenaStreamHandlers,
  signal?: AbortSignal
): Promise<void> {
  const url = `${API_BASE}/athena/stream`
  let csrf = getCsrfCookie() || cachedCsrfToken
  if (!csrf && typeof window !== 'undefined') {
    csrf = await fetchCsrfToken(signal)
  }
  const headers: Record<string, string> = { 'Content-Type': 'application/json' }
  if (csrf) {
    headers['X-CSRF-Token'] = csrf
  }
  const res = await fetch(url, {
    method: 'POST',
    headers,
    credentials: 'include',
    body: JSON.stringify({ prompt }),
    signal,
  }).catch((err: unknown) => {


    if (err instanceof Error && err.name === 'AbortError') throw err
    throw new ApiError(0, 'NetworkError', err instanceof Error ? err.message : 'Network request failed', true, undefined, '/athena/stream')
  })

  if (!res.ok || !res.body) {
    const errorText = await res.text().catch(() => '')
    throw new ApiError(
      res.status,
      res.statusText,
      `Request to /athena/stream failed (${res.status}): ${errorText || res.statusText}`,
      res.status >= 500 || res.status === 429,
      res.headers.get('x-request-id') || undefined,
      '/athena/stream'
    )
  }

  const reader = res.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''

  const dispatchFrame = (frame: string) => {
    let eventName = 'message'
    const dataLines: string[] = []
    for (const rawLine of frame.split('\n')) {
      const line = rawLine.endsWith('\r') ? rawLine.slice(0, -1) : rawLine
      if (line.startsWith('event:')) {
        eventName = line.slice(6).trim()
      } else if (line.startsWith('data:')) {
        dataLines.push(line.slice(5).trimStart())
      }
    }
    if (dataLines.length === 0) return
    let payload: Record<string, unknown>
    try {
      payload = JSON.parse(dataLines.join('\n')) as Record<string, unknown>
    } catch {
      return
    }

    switch (eventName) {
      case 'meta':
        handlers.onMeta?.({
          evidence: Array.isArray(payload.evidence) ? (payload.evidence as AthenaEvidenceCitation[]) : [],
          evidence_count: typeof payload.evidence_count === 'number' ? payload.evidence_count : 0,
          response_type: typeof payload.response_type === 'string' ? payload.response_type : undefined,
        })
        break
      case 'token':
        if (typeof payload.t === 'string' && payload.t.length > 0) handlers.onToken?.(payload.t)
        break
      case 'degraded':
        handlers.onDegraded?.(typeof payload.mode === 'string' ? payload.mode : 'degraded_factual')
        break
      case 'error':
        handlers.onError?.(typeof payload.message === 'string' ? payload.message : 'Generation failed mid-stream.')
        break
      case 'done':
      default:
        break
    }
  }

  while (true) {
    const { done, value } = await reader.read()
    if (done) break
    buffer += decoder.decode(value, { stream: true })
    let frameEnd = buffer.indexOf('\n\n')
    while (frameEnd !== -1) {
      dispatchFrame(buffer.slice(0, frameEnd))
      buffer = buffer.slice(frameEnd + 2)
      frameEnd = buffer.indexOf('\n\n')
    }
  }
  // Flush any trailing frame not terminated by a blank line
  if (buffer.trim().length > 0) dispatchFrame(buffer)

  return undefined
}

export interface AthenaSuggestedQuestionsResponse {
  questions: string[]
  signals_count: number
  generated_by: string
  landscape: string
}

export async function getAthenaSuggestedQuestions(
  signal?: AbortSignal
): Promise<AthenaSuggestedQuestionsResponse> {
  try {
    const res = await apiFetch<AthenaSuggestedQuestionsResponse>(
      '/athena/suggested-questions',
      { method: 'GET' },
      signal
    )
    return res
  } catch {
    return {
      questions: [
        'What are the 5-year durability outcomes and bleed reductions for AAV5 gene therapy in Haemophilia A?',
        'How do the Phase 3 FRONTIER-2 Mim8 zero-bleed readouts compare with prophylactic factor infusions?',
        'What regulatory action milestones and PDUFA timelines are expected for anti-TFPI prophylaxis?',
        'What are the EMA CHMP 5-year safety conclusions regarding vector shedding and liver transaminitis?',
      ],
      signals_count: 4,
      generated_by: 'gemma_3_4b',
      landscape: 'haemophilia',
    }
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
  limitOrFilters?: number | Record<string, any>,
  filters?: Record<string, any>,
  signal?: AbortSignal
): Promise<SearchResponse> {
  let top_k = 20
  let actualFilters: Record<string, any> | undefined = undefined

  if (typeof limitOrFilters === 'number') {
    top_k = limitOrFilters
    if (typeof filters === 'object' && filters !== null) {
      actualFilters = filters
    }
  } else if (typeof limitOrFilters === 'object' && limitOrFilters !== null) {
    actualFilters = limitOrFilters
  }

  const payload: Record<string, any> = { query, top_k }
  if (actualFilters) {
    payload.filters = actualFilters
  }

  return apiFetch<SearchResponse>(
    '/search',
    {
      method: 'POST',
      body: JSON.stringify(payload),
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

export async function submitSignalReview(
  signalId: string,
  payload: SignalReviewPayload,
  signal?: AbortSignal
): Promise<Signal> {
  const data = await apiFetch<any>(
    `/signals/${encodeURIComponent(signalId)}/review`,
    {
      method: 'POST',
      body: JSON.stringify(payload),
    },
    signal
  )
  return mapSignal(data)
}

export async function fetchSignalAuditHistory(
  signalId: string,
  signal?: AbortSignal
): Promise<AuditLogItem[]> {
  return apiFetch<AuditLogItem[]>(
    `/signals/${encodeURIComponent(signalId)}/audit-history`,
    undefined,
    signal
  )
}

// ---------------------------------------------------------------------------
// Auth & Identity API
// ---------------------------------------------------------------------------

export async function login(payload: LoginRequest, signal?: AbortSignal): Promise<UserMe> {
  return apiFetch<UserMe>(
    '/auth/login',
    {
      method: 'POST',
      body: JSON.stringify(payload),
    },
    signal
  )
}

export async function demoLogin(role: string, signal?: AbortSignal): Promise<UserMe> {
  return apiFetch<UserMe>(
    '/auth/demo-login',
    {
      method: 'POST',
      body: JSON.stringify({ role }),
    },
    signal
  )
}

export async function logout(signal?: AbortSignal): Promise<LogoutResponse> {
  return apiFetch<LogoutResponse>(
    '/auth/logout',
    {
      method: 'POST',
    },
    signal
  )
}

export async function getMe(signal?: AbortSignal): Promise<UserMe> {
  return apiFetch<UserMe>('/auth/me', undefined, signal)
}

// ---------------------------------------------------------------------------
// Operational Workspaces & Leadership API
// ---------------------------------------------------------------------------

export async function getFunctionQueue(
  functionId: string,
  limit = 50,
  offset = 0,
  signal?: AbortSignal
): Promise<{ signals: Signal[]; total: number }> {
  const data = await apiFetch<{ signals: any[]; total: number }>(
    `/signals/queue/${encodeURIComponent(functionId)}?limit=${limit}&offset=${offset}`,
    undefined,
    signal
  )
  return {
    signals: (data.signals || []).map(mapSignal),
    total: data.total,
  }
}

export async function getFunctionStats(
  functionId: string,
  signal?: AbortSignal
): Promise<FunctionStatsResponse> {
  const data = await apiFetch<any>(
    `/function-stats/${encodeURIComponent(functionId)}`,
    undefined,
    signal
  )
  return {
    ...data,
    recent_decisions: (data.recent_decisions || []).map(mapSignal),
  }
}

export async function getCalibrationStatus(
  signal?: AbortSignal
): Promise<CalibrationStatusResponse> {
  return apiFetch<CalibrationStatusResponse>('/calibration/status', undefined, signal)
}

export async function getLeadershipSummary(
  signal?: AbortSignal
): Promise<LeadershipSummaryResponse> {
  const data = await apiFetch<any>('/leadership/summary', undefined, signal)
  return {
    pending_escalations: (data.pending_escalations || []).map(mapSignal),
    critical_unreviewed: (data.critical_unreviewed || []).map(mapSignal),
    per_function_counts: data.per_function_counts || {},
    total_open_signals: data.total_open_signals || 0,
  }
}

