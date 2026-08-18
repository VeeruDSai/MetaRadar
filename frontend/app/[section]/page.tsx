import {
  Shell,
  DashboardPage,
  SignalsPage,
  ConfluencePage,
  LifecyclePage,
  RedTeamPage,
  MissingSignalsPage,
  DevelopmentsPage,
  IntelligencePage,
  FunctionsPage,
  SourcesPage,
  SettingsPage,
  GenericPage,
} from '@/components/metaradar'

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
      page = <SignalsPage />
      break
    case 'confluence':
      page = <ConfluencePage />
      break
    case 'lifecycles':
      page = <LifecyclePage />
      break
    case 'red-team':
      page = <RedTeamPage />
      break
    case 'missing-signals':
      page = <MissingSignalsPage />
      break
    case 'developments':
      page = <DevelopmentsPage />
      break
    case 'intelligence':
      page = <IntelligencePage />
      break
    case 'functions':
    case 'calibrate':
      page = <FunctionsPage />
      break
    case 'sources':
      page = <SourcesPage />
      break
    case 'settings':
      page = <SettingsPage />
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
