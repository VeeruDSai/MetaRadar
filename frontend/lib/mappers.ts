import type {
  Signal,
  SignalSource,
  ScoreBreakdown,
  ModelMetadata,
  DataMode,
  ConfidenceType,
} from '@/types/api'

export interface RawSignalPayload {
  signal_id?: string
  id?: string
  source_id?: string
  development_id?: string
  pipeline_run_id?: string
  pmid?: string
  nct_id?: string
  regulatory_id?: string
  fingerprint?: string
  canonical_url?: string
  signal_type?: string
  disease?: string
  title: string
  content?: string
  published_at?: string
  retrieved_at?: string
  data_mode?: DataMode
  is_synthetic?: boolean
  confidence?: number
  confidence_type?: ConfidenceType
  confidence_rationale?: string
  scoring_status?: "computed" | "not_computed"
  facts?: string[]
  interpretation?: string
  speculation?: string
  priority?: "CRITICAL" | "HIGH" | "MEDIUM" | "LOW"
  score_breakdown?: ScoreBreakdown
  model_metadata?: ModelMetadata
  scoring_model_version?: string
  scoring_config_version?: string
  embedding_model_version?: string
  prompt_version?: string
  created_at?: string
  summary?: string
  severity?: string
  status?: string
  score?: number
  detectedAt?: string
  tags?: string[]
  sources?: SignalSource[]
  stakeholders?: Record<string, number>
}

export function formatTimeAgo(isoString?: string): string {
  if (!isoString) return 'recently'
  try {
    const pubDate = new Date(isoString)
    const now = new Date()
    const diffMs = Math.max(0, now.getTime() - pubDate.getTime())
    const diffMins = Math.floor(diffMs / 60000)
    const diffHours = Math.floor(diffMins / 60)
    const diffDays = Math.floor(diffHours / 24)

    if (diffMins < 1) return 'just now'
    if (diffMins < 60) return `${diffMins} min ago`
    if (diffHours < 24) return `${diffHours} hr ago`
    if (diffDays === 1) return 'yesterday'
    if (diffDays < 30) return `${diffDays} days ago`
    return pubDate.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
  } catch {
    return 'recently'
  }
}

export function mapSignal(raw: RawSignalPayload): Signal {
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

  const sid = raw.signal_id || raw.id || `SIG-${Math.random().toString(36).substring(2, 7)}`
  const priorityStr = (raw.priority || 'MEDIUM').toUpperCase()
  const severity = severityMap[priorityStr] || 'medium'
  const timeLabel = raw.detectedAt || formatTimeAgo(raw.published_at || raw.created_at)

  // Compute honest score
  let score = 50
  if (raw.score_breakdown?.total !== undefined) {
    score = Math.round(raw.score_breakdown.total)
  } else if (raw.score !== undefined) {
    score = Math.round(raw.score)
  } else if (priorityStr === 'CRITICAL') {
    score = 85
  } else if (priorityStr === 'HIGH') {
    score = 70
  } else if (priorityStr === 'MEDIUM') {
    score = 50
  } else if (priorityStr === 'LOW') {
    score = 30
  }

  const confidence = raw.confidence !== undefined ? Math.round(raw.confidence <= 1 ? raw.confidence * 100 : raw.confidence) : 85

  // Map sources
  let sources: SignalSource[] = []
  if (raw.sources && raw.sources.length > 0) {
    sources = raw.sources
  } else if (raw.source_id) {
    sources = [{
      id: raw.source_id,
      name: raw.source_id.toUpperCase().replace(/_/g, ' '),
      type: raw.signal_type || 'SOURCE',
      credibility: 90,
      url: raw.canonical_url,
    }]
  }

  // Map stakeholders
  const stakeholders: Record<string, number> = raw.stakeholders || {
    Clinical: raw.score_breakdown?.clinical ? Math.round(raw.score_breakdown.clinical * 3.3) : 75,
    Regulatory: raw.score_breakdown?.regulatory ? Math.round(raw.score_breakdown.regulatory * 4.0) : 70,
    Market: 65,
    Operations: 60,
  }

  const summary = raw.summary || raw.content || (raw.facts && raw.facts.length > 0 ? raw.facts.join(' ') : raw.title)

  return {
    ...raw,
    id: sid,
    signal_id: sid,
    title: raw.title || 'Untitled Signal',
    summary,
    severity,
    status: raw.status || 'new',
    score,
    confidence,
    detectedAt: timeLabel,
    tags: raw.tags || [raw.disease || 'haemophilia', raw.signal_type || 'intelligence'].filter(Boolean),
    sources,
    stakeholders,
    data_mode: raw.data_mode || 'live',
    is_synthetic: raw.is_synthetic || false,
    scoring_status: raw.scoring_status || 'computed',
    confidence_type: raw.confidence_type || 'extraction',
  }
}
