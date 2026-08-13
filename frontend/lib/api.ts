import { overview, signals, sources } from '@/lib/mock-data'
import type { AthenaResponse, DashboardOverview, HealthStatus, Signal, TrendPoint } from '@/types/api'

const delay = <T,>(value: T, ms = 360) => new Promise<T>((resolve) => setTimeout(() => resolve(value), ms))
export const getOverview = (): Promise<DashboardOverview> => delay(overview)
export const getSignals = (): Promise<Signal[]> => delay(signals)
export const getTrends = (): Promise<TrendPoint[]> => delay(overview.trends)
export const getHealth = (): Promise<HealthStatus> => delay(overview.health, 180)
export const getSources = () => delay(sources)
export const askAthena = async (prompt: string): Promise<AthenaResponse> => delay({ answer: `The strongest current read is a convergence between ${prompt.toLowerCase()} and the phase III long-acting factor VIII signal. I would prioritize a focused evidence review before changing the forecast.`, sources: [sources[0], sources[1]], confidence: 87 }, 700)
