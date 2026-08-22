import { Shell, DashboardPage, LifecyclePage, GenericPage } from '@/components/metaradar'
import { SignalList } from '@/components/signals/SignalList'
import { ConfluenceWorkspace } from '@/components/confluence/ConfluenceWorkspace'
import { ContradictionWorkspace } from '@/components/contradictions/ContradictionWorkspace'
import { MissingSignalsWorkspace } from '@/components/missing-signals/MissingSignalsWorkspace'
import { DevelopmentsWorkspace } from '@/components/developments/DevelopmentsWorkspace'
import { AthenaWorkspace } from '@/components/intelligence/AthenaWorkspace'
import { FunctionsWorkspace } from '@/components/functions/FunctionsWorkspace'
import { CalibrationWorkspace } from '@/components/calibration/CalibrationWorkspace'
import { SourcesOperationsWorkspace } from '@/components/sources/SourcesOperationsWorkspace'
import { ActivityStreamWorkspace } from '@/components/observability/ActivityStreamWorkspace'
import { SettingsWorkspace } from '@/components/settings/SettingsWorkspace'

export default async function SectionPage({
  params,
}: {
  params: Promise<{ section: string }>
}) {
  const { section } = await params

  let page: React.ReactNode

  switch (section) {
    case 'dashboard':
      page = <DashboardPage />
      break
    case 'signals':
      page = <SignalList />
      break
    case 'confluence':
      page = <ConfluenceWorkspace />
      break
    case 'lifecycles':
      page = <LifecyclePage />
      break
    case 'red-team':
      page = <ContradictionWorkspace />
      break
    case 'missing-signals':
      page = <MissingSignalsWorkspace />
      break
    case 'developments':
      page = <DevelopmentsWorkspace />
      break
    case 'intelligence':
      page = <AthenaWorkspace />
      break
    case 'functions':
      page = <FunctionsWorkspace />
      break
    case 'calibrate':
      page = <CalibrationWorkspace />
      break
    case 'sources':
      page = <SourcesOperationsWorkspace />
      break
    case 'observability':
      page = <ActivityStreamWorkspace />
      break
    case 'settings':
      page = <SettingsWorkspace />
      break
    default:
      page = (
        <GenericPage
          title="Section"
          eyebrow="Workspace"
          description="Workspace area under active monitoring."
        />
      )
  }

  return <Shell>{page}</Shell>
}
