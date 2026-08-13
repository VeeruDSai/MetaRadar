import type { DashboardOverview, Signal, SignalSource } from '@/types/api'

const sources: SignalSource[] = [
  { id: 'src-1', name: 'HEM-2026-041 trial registry', type: 'trial', credibility: 94 },
  { id: 'src-2', name: 'Lancet Haematology', type: 'publication', credibility: 97 },
  { id: 'src-3', name: 'Market access tracker', type: 'market', credibility: 88 },
  { id: 'src-4', name: 'Patent landscape scan', type: 'patent', credibility: 82 },
]

export const signals: Signal[] = [
  { id: 'SIG-2481', title: 'Subcutaneous factor VIII enters phase III', summary: 'A once-monthly formulation reports non-inferiority in an interim readout, compressing the convenience gap for prophylaxis.', severity: 'critical', status: 'new', score: 92, confidence: 91, detectedAt: '12 min ago', tags: ['prophylaxis', 'factor VIII', 'phase III'], sources: [sources[0], sources[1]], stakeholders: { Clinical: 93, Market: 82, Access: 74, Operations: 68 } },
  { id: 'SIG-2478', title: 'Payer pathway opens for gene therapy', summary: 'Two regional plans publish outcomes-based reimbursement language for eligible severe patients.', severity: 'high', status: 'reviewed', score: 84, confidence: 82, detectedAt: '48 min ago', tags: ['gene therapy', 'payer', 'access'], sources: [sources[2], sources[1]], stakeholders: { Clinical: 72, Market: 91, Access: 96, Operations: 77 } },
  { id: 'SIG-2473', title: 'Rare disease center expands home infusion', summary: 'A high-volume center adds a patient training pathway that may shift nurse support demand.', severity: 'medium', status: 'actioned', score: 71, confidence: 79, detectedAt: '2 hr ago', tags: ['care model', 'home infusion'], sources: [sources[2]], stakeholders: { Clinical: 68, Market: 61, Access: 79, Operations: 90 } },
  { id: 'SIG-2469', title: 'New inhibitor screening protocol published', summary: 'A standardized assay improves cross-site comparability for neutralizing antibody monitoring.', severity: 'low', status: 'reviewed', score: 58, confidence: 88, detectedAt: '5 hr ago', tags: ['diagnostics', 'inhibitors'], sources: [sources[1]], stakeholders: { Clinical: 81, Market: 42, Access: 55, Operations: 62 } },
]

export const overview: DashboardOverview = {
  signals,
  confluence: { score: 78, label: 'Strong alignment', drivers: ['Trial readout velocity', 'Payer language', 'Patient preference shift'], updatedAt: 'Updated 6 minutes ago' },
  lifecycle: [
    { id: 'life-1', name: 'Long-acting factor VIII', stage: 'validated', momentum: 86, confidence: 91, lastChanged: '3 days ago', signals: 18 },
    { id: 'life-2', name: 'Gene therapy reimbursement', stage: 'emerging', momentum: 78, confidence: 76, lastChanged: '1 day ago', signals: 11 },
    { id: 'life-3', name: 'Home infusion networks', stage: 'scaling', momentum: 64, confidence: 88, lastChanged: '5 days ago', signals: 24 },
    { id: 'life-4', name: 'Inhibitor diagnostics', stage: 'mature', momentum: 31, confidence: 94, lastChanged: '2 weeks ago', signals: 9 },
  ],
  trends: [
    { label: 'Jan', value: 42, baseline: 36 }, { label: 'Feb', value: 48, baseline: 38 }, { label: 'Mar', value: 45, baseline: 40 }, { label: 'Apr', value: 61, baseline: 43 }, { label: 'May', value: 58, baseline: 46 }, { label: 'Jun', value: 74, baseline: 48 }, { label: 'Jul', value: 78, baseline: 50 },
  ],
  health: { api: 'healthy', lastSync: '08:42:18 UTC', latencyMs: 142, sourceCount: 1264 },
}

export { sources }
