import { Shell, DashboardPage, GenericPage, IntelligencePage, SignalsPage } from '@/components/metaradar'

const pages: Record<string, { title: string; eyebrow: string; description: string }> = {
  developments: { title: 'Developments', eyebrow: 'Landscape evolution', description: 'Track the technologies and market forces moving through their lifecycle.' },
  functions: { title: 'Functions', eyebrow: 'Role intelligence', description: 'Translate the signal landscape into function-specific implications.' },
  calibrate: { title: 'Calibrate', eyebrow: 'Human-in-the-loop review', description: 'Tune confidence and capture expert judgment without losing provenance.' },
  sources: { title: 'Sources', eyebrow: 'Evidence graph', description: 'Inspect the provenance, freshness, and credibility behind every signal.' },
  settings: { title: 'Settings', eyebrow: 'Workspace controls', description: 'Configure the workspace, notification rules, and presentation preferences.' },
}

export default async function SectionPage({ params }: { params: Promise<{ section: string }> }) {
  const { section } = await params
  let page: React.ReactNode
  if (section === 'dashboard') page = <DashboardPage />
  else if (section === 'signals') page = <SignalsPage />
  else if (section === 'intelligence') page = <IntelligencePage />
  else page = <GenericPage {...(pages[section] ?? pages.developments)} />
  return <Shell>{page}</Shell>
}
