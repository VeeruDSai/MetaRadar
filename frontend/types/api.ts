// Hand-maintained TypeScript API contract — kept in sync manually with backend/app/schemas.
// This file is NOT generated from the OpenAPI schema: scripts/export_openapi.py re-emits this
// template verbatim (so CI can detect direct edits to the canonical copy) and dumps
// contracts/openapi.json for reference. To change the contract, edit the template inside
// scripts/export_openapi.py, run that script, and commit both files together.

export type DataMode = "live" | "recorded_demo" | "test_fixture" | "benchmark";

export type ConfidenceType = 
  | "extraction"
  | "classification"
  | "evidence"
  | "nli_heuristic"
  | "overdue_heuristic"
  | "model_reasoning"
  | "human_validation";

export interface ModelMetadata {
  provider: string;
  mode: "reasoning" | "degraded_factual";
  model: string;
  fallback_used: boolean;
  fallback_reason?: string;
  reasoning_available: boolean;
  actions_available: boolean;
  latency_ms?: number;
}

export interface ScoreBreakdown {
  novelty: number;
  clinical: number;
  regulatory: number;
  recency: number;
  total: number;
  version: string;
  priority_level?: string;
  reason?: string;

  // Legacy compatibility fields
  impact?: number;
  urgency?: number;
  evidence_strength?: number;
  strategic_relevance?: number;
  routing_relevance?: number;
  total_score?: number;
}

export interface SignalSource {
  id: string;
  name: string;
  type: string;
  credibility?: number;
  url?: string;
}

export interface Signal {
  signal_id?: string;
  source_id?: string;
  source_name?: string;
  external_id?: string;
  development_id?: string;
  pipeline_run_id?: string;
  pmid?: string;
  nct_id?: string;
  regulatory_id?: string;
  fingerprint?: string;
  canonical_url?: string;
  signal_type?: string;
  disease?: string;
  title: string;
  content?: string;
  published_at?: string;
  retrieved_at?: string;
  ingested_at?: string;
  
  // Truthfulness, DataMode & Provenance
  data_mode?: DataMode;
  is_synthetic?: boolean;
  pii_scrubbed?: boolean;
  confidence?: number;
  confidence_type?: ConfidenceType;
  confidence_rationale?: string;
  provenance_status?: "available" | "missing_url" | "missing_provider_field" | "invalid_url" | "fixture";
  evidence_text?: string;
  raw_record_reference?: string;
  scoring_status?: "computed" | "not_computed";

  facts?: string[];
  interpretation?: string;
  speculation?: string;
  priority?: "CRITICAL" | "HIGH" | "MEDIUM" | "LOW";
  score_breakdown?: ScoreBreakdown;
  model_metadata?: ModelMetadata;
  scoring_model_version?: string;
  scoring_config_version?: string;
  embedding_model_version?: string;
  prompt_version?: string;
  created_at?: string;

  // Decision Object & Persisted Review State
  what_changed?: string;
  why_it_matters?: string;
  relevant_function?: string;
  route_destination?: string;
  route_role?: string;
  is_escalated?: boolean;
  routing_reason?: string;
  routing_timestamp?: string;
  source_authority_tier?: string;
  validation_status?: string;
  suggested_action?: string;
  action_rationale?: string;
  review_status?: "UNREVIEWED" | "IN_REVIEW" | "REVIEWED" | "ACTION_REQUIRED" | "ACTIONED" | "DISMISSED" | string;
  reviewed_by?: string;
  reviewed_at?: string;
  review_decision?: string;
  review_notes?: string;
  resulting_action?: string;

  // Frontend UI & Dashboard properties
  id: string;
  summary: string;
  severity: "critical" | "high" | "medium" | "low" | "neutral";
  status: string;
  score: number;
  detectedAt: string;
  tags?: string[];
  sources: SignalSource[];
  stakeholders: Record<string, number>;
}

export interface SignalReviewPayload {
  status: "UNREVIEWED" | "IN_REVIEW" | "REVIEWED" | "ACTION_REQUIRED" | "ACTIONED" | "DISMISSED" | string;
  reviewer?: string;
  decision?: string;
  notes?: string;
  resulting_action?: string;
}

export interface AuditLogItem {
  audit_id: string;
  entity_name: string;
  entity_id: string;
  action: string;
  performed_by: string;
  timestamp: string;
  details?: Record<string, any>;
}

export interface Development {
  development_id: string;
  title: string;
  disease: string;
  asset_id?: string;
  company_id?: string;
  current_stage: string;
  created_at: string;
  updated_at: string;
}

export interface HealthResponse {
  status: string;
  service: string;
  version: string;
  timestamp: string;
}

export interface HealthReadyResponse {
  status: "ready" | "degraded";
  database: boolean;
  redis: boolean;
  redis_warning?: string;
  timestamp: string;
}

export interface HealthModelsResponse {
  llm_provider: string;
  ollama_host: string;
  gemma_available: boolean;
  grok_configured: boolean;
  grok_fallback_enabled: boolean;
  bart_degraded_available: boolean;
  embedding_model: string;
  embedding_revision: string;
  embedding_dimension: number;
}

export interface SignalSearchResult {
  signal_id: string;
  title: string;
  content: string;
  signal_type: string;
  disease: string;
  priority: string;
  similarity_score: number;
  embedding_model_version?: string;
  created_at?: string;
}

export interface SearchFilters {
  signal_type?: string;
  disease?: string;
  priority?: string;
}

export interface SearchRequest {
  query: string;
  filters?: SearchFilters;
  top_k?: number;
  ef_search?: number;
}

export interface SearchResponse {
  results: SignalSearchResult[];
  total: number;
  query: string;
  ef_search_used: number;
}

export interface ConnectorHealthStatus {
  source_id: string;
  name: string;
  tier?: number;
  status: string;
  freshness_class: string;
  quota_remaining?: number | null;
  last_success?: string | null;
  last_attempted?: string | null;
  last_error?: string | null;
  connector_status: string;
  latency_ms?: number | null;
  duration_ms?: number | null;
  records_fetched?: number;
  records_accepted?: number;
  records_rejected?: number;
  records_new?: number;
  records_updated?: number;
  records_duplicate?: number;
  upstream_data_timestamp?: string | null;
  next_scheduled_run?: string | null;
  consecutive_failures?: number;
  backoff_minutes?: number;
  http_status?: number | null;
  configuration_error_message?: string | null;
}

export interface HealthConnectorsResponse {
  connectors: ConnectorHealthStatus[];
  timestamp: string;
}

export interface PipelineRunRequest {
  batch_size?: number;
  calibration_weights?: Record<string, number>;
}

export interface PipelineRunResponse {
  pipeline_run_id: string;
  status: string;
  signals_processed: number;
  role_briefs_count: number;
  developments_count: number;
  confluence_stories_count: number;
  contradictions_count: number;
  missing_signals_count: number;
  node_statuses: Record<string, string>;
  errors: Array<Record<string, any>>;
  timestamp: string;
}

export interface AthenaEvidenceCitation {
  signal_id: string;
  title: string;
  source_id: string;
  canonical_url?: string;
  published_at?: string;
  excerpt: string;
  distance: number;
  is_synthetic?: boolean;
}

export interface AthenaResponse {
  answer: string;
  confidence: number;
  confidence_type?: string;
  evidence_count: number;
  mode: string;
  model_metadata?: ModelMetadata;
  evidence: AthenaEvidenceCitation[];
  response_type?: string;
}

export interface TrendPoint {
  label: string;
  value: number;
  baseline?: number;
}

export interface ConfluenceSummary {
  score: number;
  label: string;
  drivers: string[];
  updatedAt: string;
}

export interface LifecycleSummary {
  id: string;
  name: string;
  stage: string;
  momentum?: number;
  confidence?: number;
  lastChanged?: string;
  signals: number;
}

export interface DashboardHealth {
  api: string;
  lastSync: string;
  latencyMs: number;
  sourceCount: number;
}

export interface DashboardOverview {
  active_signals?: number;
  monitored_assets?: number;
  confluences_detected?: number;
  contradictions_flagged?: number;
  weekly_change?: string;
  signals: Signal[];
  confluence: ConfluenceSummary;
  lifecycle: LifecycleSummary[];
  trends: TrendPoint[];
  health: DashboardHealth;
}

export type HealthStatus = DashboardHealth;

// Phase 5 Calibration & Feedback Types
export interface FeedbackSubmissionRequest {
  signal_id: string;
  stakeholder_function: string;
  relevance_rating: number;
  urgency_rating: number;
  action_appropriate: boolean;
  comments?: string;
  user_id?: string;
}

export interface FeedbackSubmissionResponse {
  feedback_id: string;
  signal_id: string;
  stakeholder_function: string;
  status: string;
  unapplied_count: number;
  recalibration_triggered: boolean;
}

export interface RoleWeight {
  stakeholder_function: string;
  impact_weight: number;
  urgency_weight: number;
  novelty_weight: number;
  updated_at: string;
}

export interface CalibrationRun {
  run_id: string;
  triggered_at: string;
  completed_at?: string;
  status: string;
  feedback_count: number;
  previous_weights?: Record<string, any>;
  new_weights?: Record<string, any>;
  affected_functions?: string[];
  reason?: string;
  scoring_version: string;
}

export interface CalibrationWeightsResponse {
  version: string;
  weights: RoleWeight[];
  run_history?: CalibrationRun[];
  pending_feedback_count?: number;
}

export interface WatchRuleSuggestion {
  suggestion_id: string;
  development_id?: string;
  trigger_event: string;
  expected_event: string;
  monitoring_window_days: number;
  responsible_function: string;
  rationale: string;
}

export interface BeforeAfterComparison {
  signal_id: string;
  stakeholder_function: string;
  baseline_priority: string;
  calibrated_priority: string;
  baseline_relevance_score: number;
  calibrated_relevance_score: number;
  baseline_suggested_action: string;
  calibrated_suggested_action: string;
  confidence_uplift_pct: number;
}

export interface RecalibrateResponse {
  status: string;
  calibration_version: string;
  stakeholder_function?: string;
  applied_feedback_count: number;
  run_id?: string;
  updated_weights: RoleWeight[];
  comparisons: BeforeAfterComparison[];
  watch_rule_suggestions: WatchRuleSuggestion[];
}

export interface FeedbackRoleSummary {
  stakeholder_function: string;
  total_feedback_count: number;
  average_relevance: number;
  average_urgency: number;
  action_approval_rate: number;
}

export interface FeedbackSummaryResponse {
  total_feedback: number;
  roles: FeedbackRoleSummary[];
}

export interface ConfirmWatchItemRequest {
  development_id: string;
  trigger_event: string;
  expected_event: string;
  monitoring_window_days?: number;
  responsible_function: string;
}

export interface ConfirmWatchItemResponse {
  watch_id: string;
  status: string;
  responsible_function: string;
  monitoring_window_days: number;
}

export interface ConfluenceEvidenceSourceItem {
  source_name: string;
  source_type: string;
  external_id: string;
  source_url?: string;
  retrieved_at?: string;
  published_at?: string;
  verbatim_excerpt: string;
  points_contributed: number;
}

export interface ConfluenceInspectResponse {
  confluence_id: string;
  development_id?: string;
  development_title?: string;
  score: number;
  label: string;
  confluence_type: string;
  window_hours: number;
  distinct_sources_count: number;
  score_breakdown: Record<string, number>;
  reasoning: string;
  sources: ConfluenceEvidenceSourceItem[];
  detected_at: string;
}

// Phase 6 & 7 Intelligence & Parity Types
export interface ConfluenceAlertItem {
  confluence_id: string;
  development_id: string;
  development_title?: string;
  signal_count: number;
  confluence_type: string;
  created_at: string;
  score?: number;
  calculation_version?: string;
  independent_sources_count?: number;
  score_breakdown?: Record<string, number>;
  reasoning?: string;
  evidence_sources?: ConfluenceEvidenceSourceItem[];
  signals: Array<{
    signal_id: string;
    title: string;
    signal_type: string;
    source_id?: string;
    external_id?: string;
    canonical_url?: string;
    published_at?: string;
  }>;
}

export interface LifecycleTimelineItem {
  lifecycle_id: string;
  development_id: string;
  development_title: string;
  disease: string;
  asset_name?: string;
  stage: string;
  event_date: string;
  notes?: string;
}

export interface ContradictionItem {
  contradiction_id: string;
  claim_a_id: string;
  claim_b_id: string;
  rule_id: string;
  rule_name: string;
  severity: string;
  confidence: number;
  confidence_type?: string;
  description: string;
  detected_at: string;
  claim_a_excerpt?: string;
  claim_b_excerpt?: string;
  claim_a_evidence_id?: string;
  claim_b_evidence_id?: string;
  detection_rule?: string;
  resolution_status?: string;
}

export interface MissingSignalWatchItem {
  watch_id: string;
  development_id: string;
  development_title?: string;
  trigger_event: string;
  expected_event: string;
  monitoring_window_days: number;
  responsible_function: string;
  status: string;
  confidence: number;
  confidence_type?: string;
  overdue_heuristic_score?: number;
  days_overdue: number;
  created_at: string;
}

export interface DevelopmentSummary {
  development_id: string;
  title: string;
  disease: string;
  current_stage: string;
  asset_name?: string;
  company_name?: string;
  signal_count: number;
  created_at: string;
  updated_at: string;
}

export interface SourceRegistryItem {
  source_id: string;
  name: string;
  tier?: number;
  freshness_class: string;
  syndication_group?: string;
  status: string;
  quota_remaining?: number;
  last_success?: string | null;
  connector_status: string;
  last_attempted?: string | null;
  latency_ms?: number | null;
  duration_ms?: number | null;
  records_fetched: number;
  records_accepted: number;
  records_rejected: number;
  records_new?: number;
  records_updated?: number;
  records_duplicate?: number;
  upstream_data_timestamp?: string | null;
  next_scheduled_run?: string | null;
  consecutive_failures?: number;
  backoff_minutes?: number;
  http_status?: number | null;
  configuration_error_message?: string | null;
}

export interface SourceHealthLogItem {
  id: string;
  source_id: string;
  pipeline_run_id?: string | null;
  checked_at: string;
  connector_status: string;
  http_status?: number | null;
  latency_ms?: number | null;
  duration_ms?: number | null;
  records_fetched: number;
  records_accepted: number;
  records_rejected: number;
  records_new?: number;
  records_updated?: number;
  records_duplicate?: number;
  upstream_data_timestamp?: string | null;
  last_error?: string | null;
  error_code?: string | null;
}

export interface SchedulerJobStatus {
  connector_id: string;
  interval_minutes: number;
  next_run_at?: string | null;
  last_run_at?: string | null;
  last_status: string;
  consecutive_failures: number;
  current_backoff_minutes: number;
  records_fetched_last_run: number;
  records_new_last_run: number;
  last_error?: string | null;
}

export interface SchedulerStatusResponse {
  scheduler_enabled: boolean;
  scheduler_running: boolean;
  scheduler_started_at?: string | null;
  total_jobs: number;
  active_jobs: SchedulerJobStatus[];
  timestamp: string;
}

export interface ActivityLogItem {
  id: string;
  timestamp: string;
  level: string;
  service: string;
  component: string;
  event: string;
  status: string;
  duration_ms?: number;
  request_id?: string;
  pipeline_run_id?: string;
  message: string;
  details?: Record<string, any>;
}

export interface CacheClearResponse {
  status: string;
  flushed_at: string;
  keys_cleared: number;
}

export interface SignalFilterParams {
  severity?: string;
  entity?: string;
  date_from?: string;
  date_to?: string;
  signal_type?: string;
  source?: string;
  limit?: number;
  offset?: number;
  all_functions?: boolean;
}

export interface UserMe {
  user_id: string;
  email: string;
  display_name: string;
  role: string;
  is_active: boolean;
  created_at: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface DemoLoginRequest {
  role: string;
}

export interface CsrfResponse {
  csrf_token: string;
}

export interface LogoutResponse {
  status: string;
  message: string;
}

export interface FunctionStatsResponse {
  function_id: string;
  unreviewed_count: number;
  in_review_count: number;
  escalation_count: number;
  total_decisions: number;
  time_to_first_review_hours?: number | null;
  time_to_final_decision_hours?: number | null;
  recent_decisions: Signal[];
}

export interface FunctionCalibrationProfile {
  function_name: string;
  status: string;
  feedback_sample_count: number;
  min_required_samples: number;
  brier_score?: number | null;
  ece_score?: number | null;
  reliability_curve: Array<{ bin_center: number; observed_accuracy: number }>;
}

export interface CalibrationStatusResponse {
  profiles: FunctionCalibrationProfile[];
  total_feedback_samples: number;
  last_calibration_timestamp?: string | null;
}

export interface LeadershipSummaryResponse {
  pending_escalations: Signal[];
  critical_unreviewed: Signal[];
  per_function_counts: Record<string, { unreviewed: number; in_review: number; escalated: number }>;
  total_open_signals: number;
}
