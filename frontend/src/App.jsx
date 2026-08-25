import { useMemo, useState } from 'react'
import { Activity, Crosshair, Radio, ShieldAlert, WalletCards } from 'lucide-react'
import ThreatMap from './components/ThreatMap'
import LiveTransactionFeed from './components/LiveTransactionFeed'
import ClusterDrilldown from './components/ClusterDrilldown'
import { useAlertStream } from './hooks/useAlertStream'

const formatCurrency = (value = 0) => new Intl.NumberFormat('en-IN', {
  style: 'currency', currency: 'INR', maximumFractionDigits: 0,
}).format(value)

function Metric({ icon: Icon, label, value, tone = 'cyan' }) {
  return (
    <div className="metric-card">
      <span className={`metric-icon ${tone}`}><Icon size={16} /></span>
      <div><small>{label}</small><strong>{value}</strong></div>
    </div>
  )
}

function App() {
  const { transactions, hotspots, status, metrics, actionHistory, latestAction } = useAlertStream()
  const [selected, setSelected] = useState(null)
  const selectedHotspot = hotspots.find((item) => item.h3_cell === selected) || null
  const totalRisk = useMemo(() => hotspots.reduce((sum, item) => sum + Number(item.total_amount || 0), 0), [hotspots])
  const highRisk = transactions.filter((item) => item.is_high_risk).length

  return (
    <main className="command-center">
      <header className="topbar">
        <div className="brand">
          <span className="brand-mark"><Crosshair size={22} /></span>
          <div><h1>GEO-CASHWATCH</h1><p>Predictive Cybercrime Command Center</p></div>
        </div>
        <div className="system-state">
          <span className={`connection ${status.toLowerCase()}`}><i /> {status}</span>
          <span className="clock">SIH 26184 · LIVE OPS</span>
        </div>
      </header>

      <section className="metrics-strip">
        <Metric icon={ShieldAlert} label="ACTIVE HOTSPOTS" value={hotspots.length} tone="red" />
        <Metric icon={WalletCards} label="FUNDS AT RISK" value={formatCurrency(totalRisk)} tone="orange" />
        <Metric icon={Activity} label="FLAGGED EVENTS" value={metrics.total_high_risk_flagged ?? highRisk} />
        <Metric icon={Radio} label="STREAM VOLUME" value={metrics.total_transactions_ingested ?? transactions.length} />
      </section>

      <section className="workspace">
        <aside className="left-rail panel">

          <div className="intel-block">
            <div className="section-heading"><span>THREAT LEGEND</span></div>
            <div className="legend-row"><i className="dot critical" /> Imminent cash-out <b>85%+</b></div>
            <div className="legend-row"><i className="dot warning" /> Elevated activity <b>65–84%</b></div>
            <div className="legend-row"><i className="dot watch" /> Under observation <b>&lt;65%</b></div>
          </div>
          <div className="intel-block graph-status">
            <div className="section-heading"><span>GRAPH INTELLIGENCE</span></div>
            <div className="legend-row">ST radius <b>1.0 KM</b></div>
            <div className="legend-row">Rolling window <b>30 MIN</b></div>
            <div className="legend-row">Patrol dispatches <b>{actionHistory.total_dispatches || 0}</b></div>
            <div className="legend-row">Liens placed <b>{actionHistory.total_liens || 0}</b></div>
          </div>
          <div className="coverage"><span>MONITORING REGION</span><strong>Delhi NCR</strong><small>28.6139° N · 77.2090° E</small></div>
        </aside>

        <div className="map-stage">
          <ThreatMap hotspots={hotspots} selected={selected} onSelect={setSelected} />
          <div className="map-label"><i /> PREDICTIVE COVERAGE ACTIVE</div>
        </div>

        <LiveTransactionFeed transactions={transactions} />
      </section>

      <footer className="statusbar">
        <span><i className="status-dot" /> AI MULE SCORER ONLINE</span>
        <span>H3 RESOLUTION 8</span>
        <span>WEBSOCKET: {status}</span>
        <span>LAST EVENT: {transactions[0]?.timestamp ? new Date(transactions[0].timestamp * 1000).toLocaleTimeString('en-IN') : '—'}</span>
      </footer>

      {latestAction && <div className="event-toast"><ShieldAlert size={15} /><span><b>{latestAction.type.replaceAll('_', ' ')}</b>{latestAction.dispatch?.message || latestAction.lien?.message || latestAction.complaint?.complaint_type || 'Operational state updated'}</span></div>}

      {selectedHotspot && <ClusterDrilldown hotspot={selectedHotspot} onClose={() => setSelected(null)} />}
    </main>
  )
}

export default App
