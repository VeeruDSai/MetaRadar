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
  source_name?: string
  external_id?: string
  development_id?: string
  credibility?: number
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
  ingested_at?: string
  data_mode?: DataMode
  is_synthetic?: boolean
  pii_scrubbed?: boolean
  confidence?: number
  confidence_type?: ConfidenceType
  confidence_rationale?: string
  provenance_status?: "available" | "missing_url" | "missing_provider_field" | "invalid_url" | "fixture"
  evidence_text?: string
  raw_record_reference?: string
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

  // Deterministic identity: fall back to the stable fingerprint, never a random
  // id that changes on every re-map and breaks React row identity.
  const sid = raw.signal_id || raw.id || raw.fingerprint || 'SIG-UNKNOWN'
  const priorityStr = (raw.priority || 'MEDIUM').toUpperCase()
  const severity = severityMap[priorityStr] || 'medium'
  const timeLabel = raw.detectedAt || formatTimeAgo(raw.published_at || raw.created_at)

  // Use honest score from score_breakdown or raw score without fabricating arbitrary constants
  let score = 0
  if (raw.score_breakdown?.total !== undefined && raw.score_breakdown.total > 0) {
    score = Math.round(raw.score_breakdown.total)
  } else if (raw.score !== undefined && raw.score > 0) {
    score = Math.round(raw.score)
  }

  const score_breakdown: ScoreBreakdown | undefined = raw.score_breakdown

  const confidence = raw.confidence !== undefined && raw.confidence !== null
    ? Math.round(raw.confidence <= 1 ? raw.confidence * 100 : raw.confidence)
    : undefined

  // Map sources — credibility is only set when the backend actually supplies it.
  let sources: SignalSource[] = []
  if (raw.sources && raw.sources.length > 0) {
    sources = raw.sources
  } else if (raw.source_id) {
    const derived: SignalSource = {
      id: raw.source_id,
      name: raw.source_name || raw.source_id.toUpperCase().replace(/_/g, ' '),
      type: raw.signal_type || 'SOURCE',
      url: raw.canonical_url,
    }
    if (raw.credibility !== undefined && raw.credibility !== null) {
      derived.credibility = raw.credibility
    }
    sources = [derived]
  }

  // Map stakeholders — render only real backend data; never invent values
  // via magic multipliers applied to unrelated score components.
  const stakeholders: Record<string, number> = raw.stakeholders || {}

  const summary = raw.summary || raw.content || (raw.facts && raw.facts.length > 0 ? raw.facts.join(' ') : raw.title)
  const is_synth = Boolean(raw.is_synthetic)
  const data_mode = raw.data_mode || (is_synth ? 'test_fixture' : 'live')
  const prov_status = raw.provenance_status || (is_synth ? 'fixture' : raw.canonical_url ? 'available' : 'missing_url')

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
    score_breakdown,
    data_mode,
    is_synthetic: is_synth,
    scoring_status: raw.scoring_status || (score_breakdown ? 'computed' : 'not_computed'),
    confidence_type: raw.confidence_type || 'extraction',
    confidence_rationale: raw.confidence_rationale,
    source_name: raw.source_name || (raw.source_id ? raw.source_id.toUpperCase().replace(/_/g, ' ') : undefined),
    external_id: raw.external_id || raw.pmid || raw.nct_id || raw.regulatory_id || sid,
    canonical_url: raw.canonical_url,
    provenance_status: prov_status,
    evidence_text: raw.evidence_text || raw.content || raw.title,
    raw_record_reference: raw.raw_record_reference,
    ingested_at: raw.ingested_at || raw.retrieved_at || raw.created_at,
  }
}
