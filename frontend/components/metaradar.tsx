'use client'

import { useEffect, useMemo, useState, useRef } from 'react'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { AnimatePresence, motion } from 'framer-motion'
import {
  Activity,
  AlertTriangle,
  Bell,
  BookOpen,
  BrainCircuit,
  CheckCircle2,
  ChevronRight,
  CircleHelp,
  Eye,
  FlaskConical,
  Gauge,
  LayoutDashboard,
  Menu,
  Moon,
  Network,
  RefreshCw,
  Search,
  Settings,
  ShieldCheck,
  Sliders,
  Sparkles,
  Star,
  Sun,
  Target,
  X,
} from 'lucide-react'
import { Area, AreaChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import {
  askAthena,
  confirmWatchItem,
  getHealthModels,
  getHealthReady,
  getOverview,
  mapSearchResult,
  recalibrateRole,
  searchSignals,
  submitFeedback,
} from '@/lib/api'
import { useLiveData } from '@/lib/hooks'
import type {
  AthenaResponse,
  BeforeAfterComparison,
  DashboardOverview,
  HealthModelsResponse,
  HealthReadyResponse,
  RecalibrateResponse,
  Signal,
  SignalSearchResult,
  WatchRuleSuggestion,
} from '@/types/api'

const nav = [
  { href: '/dashboard', label: 'Overview', icon: LayoutDashboard },
  { href: '/signals', label: 'Signals', icon: Activity },
  { href: '/developments', label: 'Developments', icon: FlaskConical },
  { href: '/intelligence', label: 'Intelligence', icon: BrainCircuit },
  { href: '/functions', label: 'Functions', icon: Network },
  { href: '/calibrate', label: 'Calibrate', icon: Gauge },
]
const secondary = [
  { href: '/sources', label: 'Sources', icon: BookOpen },
  { href: '/settings', label: 'Settings', icon: Settings },
]

export function Badge({
  children,
  tone = 'neutral',
}: {
  children: React.ReactNode
  tone?: 'critical' | 'high' | 'medium' | 'low' | 'neutral'
}) {
  return <span className={`badge badge-${tone}`}>{children}</span>
}

export function Card({
  children,
  className = '',
}: {
  children: React.ReactNode
  className?: string
}) {
  return <section className={`panel ${className}`}>{children}</section>
}

export function SectionTitle({
  eyebrow,
  title,
  detail,
}: {
  eyebrow: string
  title: string
  detail?: string
}) {
  return (
    <div className="section-title">
      <div>
        <p className="eyebrow">{eyebrow}</p>
        <h1>{title}</h1>
      </div>
      {detail && <p className="muted max-w-xs text-right text-sm">{detail}</p>}
    </div>
  )
}

export function Shell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname()
  const [open, setOpen] = useState(false)
  const [dark, setDark] = useState(true)
  const [searchOpen, setSearchOpen] = useState(false)
  const [selectedSignal, setSelectedSignal] = useState<Signal | null>(null)

  // Live health status polling (60s cadence)
  const { data: healthReady } = useLiveData<HealthReadyResponse>(getHealthReady, 60000)
  const { data: healthModels } = useLiveData<HealthModelsResponse>(getHealthModels, 60000)

  useEffect(() => {
    document.documentElement.classList.toggle('dark', dark)
  }, [dark])

  // Global ⌘K / Ctrl+K keyboard shortcut
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'k') {
        e.preventDefault()
        setSearchOpen((prev) => !prev)
      } else if (e.key === 'Escape') {
        setSearchOpen(false)
      }
    }
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [])

  const links = [...nav, ...secondary]
  const isDegraded = healthReady?.status === 'degraded'

  return (
    <div className="app-shell">
      <aside className={`sidebar ${open ? 'sidebar-open' : ''}`}>
        <div className="brand">
          <div className="brand-mark">
            <Target size={18} />
          </div>
          <div>
            <strong>MetaRadar</strong>
            <span>Decision intelligence</span>
          </div>
          <button
            className="icon-button sidebar-close"
            onClick={() => setOpen(false)}
            aria-label="Close navigation"
          >
            <X size={18} />
          </button>
        </div>
        <div className="workspace">
          <span className="status-dot" /> Haemophilia / Global <ChevronRight size={14} />
        </div>
        <nav className="nav-list" aria-label="Primary navigation">
          {links.map(({ href, label, icon: Icon }) => (
            <Link
              key={href}
              href={href}
              onClick={() => setOpen(false)}
              className={`nav-item ${pathname === href ? 'active' : ''}`}
            >
              <Icon size={17} />
              <span>{label}</span>
            </Link>
          ))}
        </nav>
        <div className="sidebar-note">
          <Sparkles size={17} />
          <div>
            <strong>Live Intelligence</strong>
            <span>
              {healthModels
                ? `${healthModels.llm_provider.toUpperCase()} · ${healthModels.embedding_model}`
                : 'Connecting to pipeline...'}
            </span>
          </div>
        </div>
        <div className="profile">
          <div className="avatar">SL</div>
          <div>
            <strong>Strategic lead</strong>
            <span>Workspace role</span>
          </div>
          <ChevronRight size={15} />
        </div>
      </aside>

      <div className="main-column">
        {isDegraded && (
          <div className="degraded-banner" role="alert">
            <AlertTriangle size={15} />
            <span>
              System Notice: Running in degraded mode ({healthReady?.redis_warning || 'Cache unavailable'}). Core intelligence and reasoning remain operational.
            </span>
          </div>
        )}

        <header className="topbar">
          <button
            className="icon-button menu-button"
            onClick={() => setOpen(true)}
            aria-label="Open navigation"
          >
            <Menu size={20} />
          </button>
          <div className="breadcrumbs">
            <span>Workspace</span>
            <ChevronRight size={14} />
            <strong>
              {nav.find((item) => item.href === pathname)?.label ??
                secondary.find((item) => item.href === pathname)?.label ??
                'Overview'}
            </strong>
          </div>
          <div className="top-actions">
            <button
              className="search-button"
              onClick={() => setSearchOpen(true)}
              aria-label="Search signals"
            >
              <Search size={16} />
              <span>Search signals</span>
              <kbd>⌘ K</kbd>
            </button>
            <button className="icon-button notification" aria-label="Notifications">
              <Bell size={17} />
              <i />
            </button>
            <button
              className="theme-toggle"
              onClick={() => setDark(!dark)}
              aria-label="Toggle theme"
            >
              {dark ? <Moon size={16} /> : <Sun size={16} />}
            </button>
          </div>
        </header>

        <main className="content">{children}</main>

        <footer className="health-footer">
          <span>
            <ShieldCheck
              size={15}
              className={isDegraded ? 'text-warning' : 'text-emerald'}
            />
            {healthReady
              ? `Backend ${healthReady.status.toUpperCase()} · DB ${healthReady.database ? 'Connected' : 'Offline'}`
              : 'Checking status...'}
          </span>
          <span>
            Provider: {healthModels?.llm_provider || 'Local'} ({healthModels?.embedding_dimension || 384}-dim vector)
          </span>
          <span className="footer-source">
            MetaRadar v5.1 · Live Workspace
          </span>
        </footer>
      </div>

      {searchOpen && (
        <SearchModal
          onClose={() => setSearchOpen(false)}
          onSelectSignal={(signal) => {
            setSearchOpen(false)
            setSelectedSignal(signal)
          }}
        />
      )}

      {selectedSignal && (
        <SignalDrawer
          signal={selectedSignal}
          onClose={() => setSelectedSignal(null)}
        />
      )}
    </div>
  )
}

function SearchModal({
  onClose,
  onSelectSignal,
}: {
  onClose: () => void
  onSelectSignal: (signal: Signal) => void
}) {
  const [query, setQuery] = useState('')
  const [results, setResults] = useState<SignalSearchResult[]>([])
  const [loading, setLoading] = useState(false)
  const [searchError, setSearchError] = useState<string | null>(null)
  const inputRef = useRef<HTMLInputElement>(null)
  const abortControllerRef = useRef<AbortController | null>(null)

  useEffect(() => {
    inputRef.current?.focus()
    return () => {
      if (abortControllerRef.current) abortControllerRef.current.abort()
    }
  }, [])

  useEffect(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort()
    }

    if (!query.trim()) {
      setResults([])
      setSearchError(null)
      return
    }

    const controller = new AbortController()
    abortControllerRef.current = controller

    const timer = setTimeout(async () => {
      setLoading(true)
      setSearchError(null)
      try {
        const res = await searchSignals(query, 10, controller.signal)
        if (!controller.signal.aborted) {
          setResults(res.results || [])
        }
      } catch (err: any) {
        if (!controller.signal.aborted) {
          setResults([])
          setSearchError(err instanceof Error ? err.message : 'Search request failed')
        }
      } finally {
        if (!controller.signal.aborted) {
          setLoading(false)
        }
      }
    }, 280)

    return () => {
      clearTimeout(timer)
      controller.abort()
    }
  }, [query])

  return (
    <div className="search-modal-backdrop" onClick={onClose}>
      <div className="search-modal" onClick={(e) => e.stopPropagation()}>
        <div className="search-header">
          <Search size={18} />
          <input
            ref={inputRef}
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search signals by concept, drug, mechanism..."
          />
          <kbd>ESC</kbd>
        </div>
        <div className="search-results">
          {loading && (
            <div className="search-empty">
              <Activity size={18} className="animate-spin text-signal" />
              <p>Searching 384-dim semantic index...</p>
            </div>
          )}
          {searchError && (
            <div className="search-empty text-warning">
              <p>Search unavailable: {searchError}</p>
            </div>
          )}
          {!loading && !searchError && results.length > 0 && (
            results.map((r) => {
              const scorePct = Math.round(r.similarity_score * 100)
              return (
                <button
                  key={r.signal_id}
                  className="search-item"
                  onClick={() => onSelectSignal(mapSearchResult(r))}
                >
                  <div className="search-item-top">
                    <strong>{r.title}</strong>
                    <Badge tone={scorePct >= 80 ? 'high' : 'neutral'}>
                      {scorePct}% match
                    </Badge>
                  </div>
                  <p>{r.content}</p>
                  <div className="search-item-meta">
                    <span>{r.disease}</span>
                    <span>·</span>
                    <span>{r.signal_type}</span>
                  </div>
                </button>
              )
            })
          )}
          {!loading && !searchError && query.trim() && results.length === 0 && (
            <div className="search-empty">
              <p>No matching signals found for &ldquo;{query}&rdquo;</p>
            </div>
          )}
          {!query.trim() && (
            <div className="search-empty">
              <p>Type keywords to perform semantic vector search across all ingested signals.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

function KPI({
  label,
  value,
  change,
  accent,
}: {
  label: string
  value: string | number
  change: string
  accent?: string
}) {
  return (
    <Card className="kpi">
      <p className="eyebrow">{label}</p>
      <div className="kpi-value">
        <strong>{value}</strong>
        <span className={accent ?? 'positive'}>{change}</span>
      </div>
      <div className="micro-bars">
        <i />
        <i />
        <i />
        <i />
        <i />
      </div>
    </Card>
  )
}

function Radar({ score }: { score: number }) {
  return (
    <div className="radar">
      <div className="radar-ring ring-one" />
      <div className="radar-ring ring-two" />
      <div className="radar-ring ring-three" />
      <div className="radar-sweep" />
      <div className="radar-core">
        <strong>{Math.round(score)}</strong>
        <span>confluence</span>
      </div>
    </div>
  )
}

function SignalRow({
  signal,
  onSelect,
}: {
  signal: Signal
  onSelect: (signal: Signal) => void
}) {
  return (
    <button className="signal-row" onClick={() => onSelect(signal)}>
      <span className={`severity-dot ${signal.severity}`} />
      <div className="signal-copy">
        <div>
          <strong>{signal.title}</strong>
          <Badge tone={signal.severity}>{signal.severity}</Badge>
        </div>
        <span>{signal.summary}</span>
        <small>
          {signal.detectedAt} · {signal.sources.length} sources
        </small>
      </div>
      <div className="signal-score">
        <strong>{signal.score}</strong>
        <span>priority score</span>
      </div>
      <ChevronRight size={17} className="muted" />
    </button>
  )
}

function TrendChart({ data }: { data: DashboardOverview['trends'] }) {
  return (
    <div className="chart-wrap">
      <ResponsiveContainer width="100%" height={220}>
        <AreaChart
          data={data}
          margin={{ left: -22, right: 8, top: 10, bottom: 0 }}
        >
          <defs>
            <linearGradient id="trend" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="var(--signal)" stopOpacity={0.35} />
              <stop offset="100%" stopColor="var(--signal)" stopOpacity={0} />
            </linearGradient>
          </defs>
          <XAxis
            dataKey="label"
            axisLine={false}
            tickLine={false}
            tick={{ fill: 'var(--muted-foreground)', fontSize: 11 }}
          />
          <YAxis hide domain={[0, 100]} />
          <Tooltip
            contentStyle={{
              background: 'var(--panel)',
              border: '1px solid var(--border)',
              borderRadius: 10,
              color: 'var(--foreground)',
            }}
          />
          <Area
            type="monotone"
            dataKey="baseline"
            stroke="var(--muted-foreground)"
            strokeDasharray="4 4"
            fill="none"
            strokeWidth={1.5}
          />
          <Area
            type="monotone"
            dataKey="value"
            stroke="var(--signal)"
            fill="url(#trend)"
            strokeWidth={2.5}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  )
}

export function DashboardPage() {
  const { data, loading, error, isRefreshing, refetch } = useLiveData(getOverview)
  const [selected, setSelected] = useState<Signal | null>(null)

  if (loading && !data) return <Loading />

  if (error && !data) {
    return (
      <div className="error-card">
        <h3>Backend Service Offline</h3>
        <p>Could not connect to FastAPI backend at {process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1'}.</p>
        <button className="retry-button" onClick={() => refetch()}>
          <RefreshCw size={14} /> Retry Connection
        </button>
      </div>
    )
  }

  const overviewData = data || {
    active_signals: 0,
    monitored_assets: 0,
    confluences_detected: 0,
    signals: [],
    confluence: { score: 0, label: 'No alignment', drivers: [], updatedAt: 'Just now' },
    lifecycle: [],
    trends: [],
    health: { api: 'offline', lastSync: 'Never', latencyMs: 0, sourceCount: 0 },
  }

  const hasSignals = overviewData.signals.length > 0

  return (
    <>
      <SectionTitle
        eyebrow="Portfolio pulse"
        title="Live Workspace"
        detail={isRefreshing ? 'Refreshing live signals...' : `Last sync: ${overviewData.health.lastSync}`}
      />

      <div className="kpi-grid">
        <KPI
          label="Active signals"
          value={overviewData.active_signals ?? 0}
          change={overviewData.weekly_change ?? ((overviewData.active_signals ?? 0) > 0 ? '+0.0%' : '—')}
        />
        <KPI
          label="Monitored assets"
          value={overviewData.monitored_assets ?? 0}
          change={(overviewData.monitored_assets ?? 0) > 0 ? 'active' : '—'}
        />
        <KPI
          label="Confluence index"
          value={Math.round(overviewData.confluence.score)}
          change={overviewData.confluence.score > 0 ? overviewData.confluence.label : '—'}
        />
        <KPI
          label="Source feeds"
          value={overviewData.health.sourceCount}
          change={overviewData.health.sourceCount > 0 ? 'online' : '—'}
        />
      </div>

      <div className="bento-grid">
        <Card className="signals-panel priority-intelligence">
          <div className="card-heading">
            <div>
              <p className="eyebrow">Priority intelligence</p>
              <h2>Signals requiring attention</h2>
              <p className="muted panel-subtitle">
                Independent evidence converging on the next decision.
              </p>
            </div>
            <Link href="/signals" className="text-link">
              View all <ChevronRight size={15} />
            </Link>
          </div>
          {hasSignals ? (
            <div className="signal-list">
              {overviewData.signals.slice(0, 3).map((signal) => (
                <SignalRow
                  key={signal.id}
                  signal={signal}
                  onSelect={setSelected}
                />
              ))}
            </div>
          ) : (
            <div className="empty-state">
              <Activity size={24} />
              <p>No signals detected yet</p>
              <span>Ingest signals via backend connectors or trigger the LangGraph pipeline.</span>
            </div>
          )}
        </Card>

        <Card className="radar-panel">
          <div className="card-heading">
            <div>
              <p className="eyebrow">Cross-source alignment</p>
              <h2>Confluence index</h2>
              <p className="muted confluence-explainer">
                Independent signals pointing to the same development.
              </p>
            </div>
            <CircleHelp size={16} className="muted" />
          </div>
          <Radar score={overviewData.confluence.score} />
          <div className="driver-list">
            {overviewData.confluence.drivers.length > 0 ? (
              overviewData.confluence.drivers.map((driver, index) => {
                const categoryMap: Record<string, string> = {
                  'Clinical trial readouts': 'TRIAL READOUT',
                  'Payer & regulatory filings': 'REGULATORY SIGNAL',
                  'Trial readout velocity': 'TRIAL READOUT',
                  'Payer language': 'PAYER / ACCESS',
                  'Regulatory pathway': 'REGULATORY SIGNAL',
                }
                const category = categoryMap[driver] || 'INTELLIGENCE'
                return (
                  <div key={driver}>
                    <span className="driver-number">0{index + 1}</span>
                    <span>{category}</span>
                    <span className="driver-line" />
                    <small>{driver}</small>
                  </div>
                )
              })
            ) : (
              <p className="muted text-center text-xs py-4">No active confluence drivers detected.</p>
            )}
          </div>
        </Card>

        <Card className="trend-panel">
          <div className="card-heading">
            <div>
              <p className="eyebrow">Signal velocity</p>
              <h2>Portfolio momentum</h2>
            </div>
            <Badge tone="high">Live</Badge>
          </div>
          <TrendChart data={overviewData.trends} />
        </Card>

        <Card className="questions-panel">
          <div className="card-heading">
            <div>
              <p className="eyebrow">Decision frame</p>
              <h2>Four questions</h2>
            </div>
            <Link href="/intelligence" className="icon-link">
              <ChevronRight size={17} />
            </Link>
          </div>
          {[
            'What changed?',
            'Why does it matter?',
            'Who is affected?',
            'What should we do?',
          ].map((q, i) => (
            <Link href="/intelligence" className="question-row" key={q}>
              <span>Q{i + 1}</span>
              <strong>{q}</strong>
              <ChevronRight size={15} />
            </Link>
          ))}
        </Card>
      </div>

      {selected && (
        <SignalDrawer signal={selected} onClose={() => setSelected(null)} />
      )}
    </>
  )
}

export function SignalsPage() {
  const { data, loading, error, isRefreshing, refetch } = useLiveData(getOverview)
  const [filter, setFilter] = useState('all')
  const [selected, setSelected] = useState<Signal | null>(null)

  const signalsList = data?.signals || []
  const filtered = useMemo(
    () =>
      signalsList.filter(
        (s) => filter === 'all' || s.severity === filter
      ),
    [signalsList, filter]
  )

  if (loading && !data) return <Loading />

  if (error && !data) {
    return (
      <div className="error-card">
        <h3>Backend Service Offline</h3>
        <p>Could not connect to FastAPI backend to fetch signals.</p>
        <button className="retry-button" onClick={() => refetch()}>
          <RefreshCw size={14} /> Retry
        </button>
      </div>
    )
  }

  return (
    <>
      <SectionTitle
        eyebrow="Live intelligence stream"
        title="Signals"
        detail={isRefreshing ? 'Refreshing signals...' : 'A ranked view of meaningful change across the haemophilia landscape.'}
      />
      <div className="signals-toolbar">
        <div className="filter-bar">
          {['all', 'critical', 'high', 'medium', 'low'].map((item) => (
            <button
              key={item}
              className={filter === item ? 'filter-active' : ''}
              onClick={() => setFilter(item)}
            >
              {item === 'all' ? 'All signals' : item}
            </button>
          ))}
        </div>
        <Card className="filtered-view">
          <p className="eyebrow">Filtered view</p>
          <div className="filtered-stats">
            <strong>
              {filtered.length}
              <span>visible</span>
            </strong>
            <strong>
              {
                filtered.filter(
                  (signal) =>
                    signal.severity === 'high' || signal.severity === 'critical'
                ).length
              }
              <span>high priority</span>
            </strong>
            <strong>
              {filtered.reduce((total, signal) => total + signal.sources.length, 0)}
              <span>sources</span>
            </strong>
            <strong>
              {data?.health.lastSync || 'Live'}
              <span>last sync</span>
            </strong>
          </div>
          <p className="muted">
            Active filter: {filter === 'all' ? 'All signals' : filter}
          </p>
        </Card>
      </div>

      <Card>
        {filtered.length > 0 ? (
          <div className="signal-list">
            {filtered.map((signal) => (
              <SignalRow
                key={signal.id}
                signal={signal}
                onSelect={setSelected}
              />
            ))}
          </div>
        ) : (
          <div className="empty-state">
            <Activity size={24} />
            <p>
              {signalsList.length === 0
                ? 'No signals detected in database yet.'
                : `No signals matching the '${filter}' severity filter.`}
            </p>
            <span>
              {signalsList.length === 0
                ? 'Run the ingestion pipeline to populate live intelligence records.'
                : 'Try selecting a different filter.'}
            </span>
          </div>
        )}
      </Card>

      {selected && (
        <SignalDrawer signal={selected} onClose={() => setSelected(null)} />
      )}
    </>
  )
}

export function IntelligencePage() {
  const [prompt, setPrompt] = useState('')
  const [answer, setAnswer] = useState<AthenaResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const prompts = [
    'What changed in durability data for gene therapies?',
    'Which signals have the strongest confluence across clinical trials and payer language?',
    'What action should Medical Affairs prioritize this week?',
  ]

  async function submit(value = prompt) {
    const trimmed = value.trim()
    if (!trimmed) return
    setPrompt(trimmed)
    setLoading(true)
    setError(null)
    setAnswer(null)

    try {
      const res = await askAthena(trimmed)
      setAnswer(res)
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : 'Failed to synthesize intelligence from Athena.'
      )
    } finally {
      setLoading(false)
    }
  }

  return (
    <>
      <SectionTitle
        eyebrow="Strategic synthesis"
        title="Ask Athena"
        detail="Ask Athena to connect multi-source signals into a decision-ready point of view."
      />
      <div className="intelligence-grid">
        <Card className="athena-card">
          <div className="athena-orbit">
            <BrainCircuit size={30} />
          </div>
          <p className="eyebrow">Athena synthesis layer</p>
          <h2>Make the next signal useful.</h2>
          <p className="muted">
            Explore the evidence behind the pulse, then turn a pattern into a clear next step.
          </p>
          <div className="prompt-list">
            {prompts.map((item) => (
              <button key={item} onClick={() => submit(item)}>
                {item}
                <ChevronRight size={15} />
              </button>
            ))}
          </div>
          <div className="ask-row">
            <input
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter') submit()
              }}
              placeholder="Ask a strategic question..."
            />
            <button onClick={() => submit()} disabled={loading}>
              <Sparkles size={16} /> {loading ? 'Thinking' : 'Ask Athena'}
            </button>
          </div>
        </Card>

        <Card className="answer-card">
          <p className="eyebrow">Response</p>
          {loading ? (
            <div className="thinking">
              <i />
              <i />
              <i />
            </div>
          ) : error ? (
            <div className="error-card my-4">
              <h3>Synthesis Error</h3>
              <p>{error}</p>
              <button
                className="retry-button"
                onClick={() => submit(prompt)}
              >
                <RefreshCw size={14} /> Retry Query
              </button>
            </div>
          ) : answer ? (
            <>
              <h2>Here&apos;s the read.</h2>
              <p>{answer.answer}</p>
              <div className="confidence">
                <span>Confidence Score</span>
                <strong>{Math.round(answer.confidence)}%</strong>
              </div>
            </>
          ) : (
            <div className="empty-state">
              <BrainCircuit size={24} />
              <p>Select a prompt or ask a question to begin a synthesis.</p>
              <span>
                Athena connects evidence across trial readouts, regulatory filings, and market access patterns.
              </span>
            </div>
          )}
        </Card>
      </div>
    </>
  )
}

export function SignalDrawer({
  signal,
  onClose,
}: {
  signal: Signal
  onClose: () => void
}) {
  const [selectedRole, setSelectedRole] = useState<string>('REGULATORY')
  const [relevanceRating, setRelevanceRating] = useState<number>(5)
  const [urgencyRating, setUrgencyRating] = useState<number>(4)
  const [actionAppropriate, setActionAppropriate] = useState<boolean>(true)
  const [comments, setComments] = useState<string>('')
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false)
  const [isRecalibrating, setIsRecalibrating] = useState<boolean>(false)
  const [feedbackSuccess, setFeedbackSuccess] = useState<string | null>(null)
  const [recalResult, setRecalResult] = useState<RecalibrateResponse | null>(null)
  const [confirmedWatchId, setConfirmedWatchId] = useState<string | null>(null)

  const roles = [
    'REGULATORY',
    'MEDICAL_AFFAIRS',
    'SAFETY',
    'MARKET_ACCESS',
    'COMMUNICATIONS',
    'LEADERSHIP',
  ]

  const isValidUuid = (val?: string): boolean =>
    typeof val === 'string' &&
    /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(val)

  const handleFeedbackSubmit = async () => {
    setIsSubmitting(true)
    setFeedbackSuccess(null)
    try {
      const sigId = isValidUuid(signal.signal_id)
        ? signal.signal_id!
        : isValidUuid(signal.id)
        ? signal.id
        : '00000000-0000-0000-0000-000000000000'

      const res = await submitFeedback({
        signal_id: sigId,
        stakeholder_function: selectedRole,
        relevance_rating: relevanceRating,
        urgency_rating: urgencyRating,
        action_appropriate: actionAppropriate,
        comments: comments.trim() || undefined,
        user_id: 'enterprise_reviewer',
      })
      setFeedbackSuccess(
        `Feedback recorded for ${selectedRole}. (${res.unapplied_count} unapplied items queued)`
      )
    } catch (err) {
      setFeedbackSuccess('Failed to record feedback. Please check backend connection.')
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleRecalibrate = async () => {
    setIsRecalibrating(true)
    try {
      const res = await recalibrateRole(selectedRole)
      setRecalResult(res)
    } catch (err) {
      setFeedbackSuccess('Recalibration failed. Please check backend connection.')
    } finally {
      setIsRecalibrating(false)
    }
  }

  const handleConfirmWatch = async (sug: WatchRuleSuggestion) => {
    try {
      const devId = isValidUuid(sug.development_id)
        ? sug.development_id!
        : isValidUuid(signal.development_id)
        ? signal.development_id!
        : '00000000-0000-0000-0000-000000000000'

      const res = await confirmWatchItem({
        development_id: devId,
        trigger_event: sug.trigger_event,
        expected_event: sug.expected_event,
        monitoring_window_days: sug.monitoring_window_days,
        responsible_function: sug.responsible_function,
      })
      setConfirmedWatchId(res.watch_id)
    } catch (err) {
      console.error('Failed to confirm watch item', err)
    }
  }

  return (
    <div className="drawer-backdrop" onClick={onClose}>
      <motion.aside
        initial={{ x: 30, opacity: 0 }}
        animate={{ x: 0, opacity: 1 }}
        className="signal-drawer"
        onClick={(event) => event.stopPropagation()}
      >
        <div className="drawer-top">
          <Badge tone={signal.severity}>{signal.severity} signal</Badge>
          <button
            className="icon-button"
            onClick={onClose}
            aria-label="Close signal"
          >
            <X size={18} />
          </button>
        </div>
        <p className="eyebrow">
          {signal.id} · {signal.detectedAt}
        </p>
        <h2>{signal.title}</h2>
        <div className="drawer-sections">
          <div>
            <h3>What changed?</h3>
            <p>{signal.summary}</p>
          </div>
          <div>
            <h3>Why does it matter?</h3>
            <p>
              {signal.interpretation ||
                'This signal may change the current development outlook and deserves cross-functional review.'}
            </p>
          </div>
          <div>
            <h3>Who should review?</h3>
            <p>
              {Object.keys(signal.stakeholders).length > 0
                ? Object.keys(signal.stakeholders).join(' · ')
                : 'Medical Affairs · Regulatory · Leadership'}
            </p>
          </div>
          <div>
            <h3>What action may be required?</h3>
            <p>
              Validate the evidence, compare related signals, and route to the accountable function.
            </p>
          </div>
        </div>
        <div className="drawer-score">
          <strong>{signal.score}</strong>
          <span>priority score</span>
          <strong>{signal.confidence}%</strong>
          <span>relevance confidence</span>
        </div>

        {/* Stakeholder Calibration Loop & Rating Widget (REQ-P5-1, REQ-P5-2) */}
        <div className="calibration-widget-card">
          <div className="widget-header">
            <Sliders size={16} className="text-accent" />
            <h3>Stakeholder Calibration & Feedback</h3>
          </div>
          <p className="muted widget-intro">
            Rate routing relevance and trigger batch weight calibration with versioned history.
          </p>

          <div className="role-selector-bar">
            {roles.map((role) => (
              <button
                key={role}
                className={`role-pill ${selectedRole === role ? 'role-pill-active' : ''}`}
                onClick={() => setSelectedRole(role)}
              >
                {role.replace('_', ' ')}
              </button>
            ))}
          </div>

          <div className="rating-rows">
            <div className="rating-row">
              <span>Relevance Rating:</span>
              <div className="star-group">
                {[1, 2, 3, 4, 5].map((star) => (
                  <button
                    key={star}
                    type="button"
                    className={`star-btn ${relevanceRating >= star ? 'star-active' : ''}`}
                    onClick={() => setRelevanceRating(star)}
                    aria-label={`Rate relevance ${star} stars`}
                  >
                    <Star size={16} />
                  </button>
                ))}
              </div>
            </div>

            <div className="rating-row">
              <span>Urgency Rating:</span>
              <div className="star-group">
                {[1, 2, 3, 4, 5].map((star) => (
                  <button
                    key={star}
                    type="button"
                    className={`star-btn ${urgencyRating >= star ? 'star-active' : ''}`}
                    onClick={() => setUrgencyRating(star)}
                    aria-label={`Rate urgency ${star} stars`}
                  >
                    <Star size={16} />
                  </button>
                ))}
              </div>
            </div>

            <label className="checkbox-row">
              <input
                type="checkbox"
                checked={actionAppropriate}
                onChange={(e) => setActionAppropriate(e.target.checked)}
              />
              <span>Action and routing are appropriate</span>
            </label>

            <textarea
              className="feedback-comment-input"
              rows={2}
              placeholder="e.g. Critical durability data; watch upcoming ASH 2026 congress abstracts..."
              value={comments}
              onChange={(e) => setComments(e.target.value)}
            />

            <div className="widget-actions">
              <button
                className="submit-feedback-btn"
                onClick={handleFeedbackSubmit}
                disabled={isSubmitting}
              >
                {isSubmitting ? (
                  <>
                    <RefreshCw size={14} className="spin" /> Submitting...
                  </>
                ) : (
                  <>
                    <CheckCircle2 size={14} /> Submit Feedback
                  </>
                )}
              </button>

              <button
                className="recalibrate-btn"
                onClick={handleRecalibrate}
                disabled={isRecalibrating}
              >
                {isRecalibrating ? (
                  <>
                    <RefreshCw size={14} className="spin" /> Recalibrating...
                  </>
                ) : (
                  <>
                    <Gauge size={14} /> Recalibrate Role
                  </>
                )}
              </button>
            </div>

            {feedbackSuccess && (
              <div className="feedback-toast">
                <CheckCircle2 size={15} />
                <span>{feedbackSuccess}</span>
              </div>
            )}
          </div>

          {/* BEFORE vs AFTER Calibration Comparison Readout (D-12, AC-14) */}
          {recalResult && (
            <div className="before-after-panel">
              <div className="before-after-header">
                <Sparkles size={16} />
                <strong>Calibrated Routing (Version {recalResult.calibration_version})</strong>
              </div>

              {recalResult.comparisons.map((comp, idx) => (
                <div className="comparison-card" key={idx}>
                  <div className="comparison-grid">
                    <div className="comparison-col before-col">
                      <span className="col-label">BASELINE ROUTING</span>
                      <div className="score-val">{Math.round(comp.baseline_relevance_score * 100)}%</div>
                      <Badge tone="medium">Priority: {comp.baseline_priority}</Badge>
                    </div>

                    <div className="comparison-divider">→</div>

                    <div className="comparison-col after-col">
                      <span className="col-label">CALIBRATED ROUTING</span>
                      <div className="score-val highlight">{Math.round(comp.calibrated_relevance_score * 100)}%</div>
                      <Badge tone="critical">Priority: {comp.calibrated_priority}</Badge>
                    </div>
                  </div>

                  {comp.confidence_uplift_pct > 0 && (
                    <div className="uplift-banner">
                      <Sparkles size={13} />
                      <span>{comp.stakeholder_function} confidence uplift: +{comp.confidence_uplift_pct}% after feedback</span>
                    </div>
                  )}

                  <p className="calibrated-action-text">
                    {comp.calibrated_suggested_action}
                  </p>
                </div>
              ))}

              {/* Parsed Watch Rule Suggestions (D-08, D-09) */}
              {recalResult.watch_rule_suggestions.length > 0 && (
                <div className="watch-suggestions-box">
                  <h4>
                    <Eye size={15} /> Suggested Watch Rule
                  </h4>
                  {recalResult.watch_rule_suggestions.map((sug) => (
                    <div className="watch-suggestion-card" key={sug.suggestion_id}>
                      <p>
                        <strong>Expected:</strong> {sug.expected_event}
                      </p>
                      <p className="muted text-xs">
                        Monitoring window: {sug.monitoring_window_days} days · Function: {sug.responsible_function}
                      </p>
                      {confirmedWatchId ? (
                        <div className="watch-confirmed-badge">
                          <CheckCircle2 size={13} /> Active Watch Rule Confirmed
                        </div>
                      ) : (
                        <button
                          className="confirm-watch-btn"
                          onClick={() => handleConfirmWatch(sug)}
                        >
                          Confirm & Activate Watch Rule
                        </button>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>

        <h3>Evidence & provenance</h3>
        <p className="muted evidence-note">
          Source material supporting this intelligence.
        </p>
        {signal.sources.length > 0 ? (
          signal.sources.map((source) => (
            <div className="source-line" key={source.id}>
              <BookOpen size={15} />
              <span>
                <strong>{source.name}</strong>
                <small>{source.type}</small>
              </span>
              <Badge>{source.credibility}%</Badge>
            </div>
          ))
        ) : (
          <p className="muted text-xs">Direct public signal ingestion feed.</p>
        )}
      </motion.aside>
    </div>
  )
}

export function GenericPage({
  title,
  eyebrow,
  description,
  children,
}: {
  title: string
  eyebrow: string
  description: string
  children?: React.ReactNode
}) {
  return (
    <>
      <SectionTitle eyebrow={eyebrow} title={title} detail={description} />
      <div className="generic-grid">
        <Card>
          <div className="placeholder-visual">
            <Network size={26} />
            <strong>Signal architecture</strong>
            <span>Connected evidence will appear here.</span>
          </div>
        </Card>
        <Card>
          <p className="eyebrow">System note</p>
          <h2>Build from the evidence.</h2>
          <p className="muted">
            This workspace is ready for review workflows, provenance, and role-specific decisions.
          </p>
          {children}
        </Card>
      </div>
    </>
  )
}

function Loading() {
  return (
    <div className="loading-screen">
      <div className="loading-mark">
        <Activity size={22} />
      </div>
      <p>Loading signal landscape...</p>
    </div>
  )
}
