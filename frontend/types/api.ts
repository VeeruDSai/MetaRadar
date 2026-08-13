export type SignalSeverity = 'critical' | 'high' | 'medium' | 'low'
export type SignalStatus = 'new' | 'reviewed' | 'actioned'
export type LifecycleStage = 'emerging' | 'validated' | 'scaling' | 'mature'

export interface SignalSource { id: string; name: string; type: 'trial' | 'publication' | 'market' | 'patent'; credibility: number }
export interface Signal { id: string; title: string; summary: string; severity: SignalSeverity; status: SignalStatus; score: number; confidence: number; detectedAt: string; tags: string[]; sources: SignalSource[]; stakeholders: Record<string, number> }
export interface Confluence { score: number; label: string; drivers: string[]; updatedAt: string }
export interface LifecycleItem { id: string; name: string; stage: LifecycleStage; momentum: number; confidence: number; lastChanged: string; signals: number }
export interface TrendPoint { label: string; value: number; baseline: number }
export interface HealthStatus { api: 'healthy' | 'degraded'; lastSync: string; latencyMs: number; sourceCount: number }
export interface AthenaResponse { answer: string; sources: SignalSource[]; confidence: number }
export interface DashboardOverview { signals: Signal[]; confluence: Confluence; lifecycle: LifecycleItem[]; trends: TrendPoint[]; health: HealthStatus }
export interface CalibrationReview { signalId: string; rating: number; notes: string }
