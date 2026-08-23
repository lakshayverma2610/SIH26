import { Building2, Clock3, MapPin, ShieldCheck, Snowflake, X } from 'lucide-react'
import { useState } from 'react'
import { formatCashoutTime } from '../utils/normalize'

const api = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

export default function ClusterDrilldown({ hotspot, onClose }) {
  const [action, setAction] = useState('')
  const [busy, setBusy] = useState(false)
  const window = hotspot.predicted_cashout_window || {}
  const callAction = async (kind) => {
    setBusy(true); setAction('')
    const path = kind === 'dispatch' ? '/api/v1/actions/dispatch-patrol' : '/api/v1/actions/freeze-lien'
    const body = kind === 'dispatch'
      ? { h3_cell: hotspot.h3_cell, destination_lat: hotspot.lat, destination_lon: hotspot.lon, priority: 'CRITICAL' }
      : { account_number: hotspot.mule_accounts?.[0] || null, account_numbers: hotspot.mule_accounts || [], freeze_amount: hotspot.total_amount, reason: `High-risk hotspot ${hotspot.h3_cell}` }
    try {
      const response = await fetch(`${api}${path}`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) })
      if (!response.ok) throw new Error('Service unavailable')
      setAction(kind === 'dispatch' ? 'Patrol dispatch confirmed' : '1930 lien request confirmed')
    } catch { setAction('Demo action recorded — backend is offline') }
    finally { setBusy(false) }
  }
  return (
    <div className="modal-backdrop" onMouseDown={(event) => event.target === event.currentTarget && onClose()}>
      <section className="drilldown">
        <button className="close" onClick={onClose}><X size={18} /></button>
        <div className="alert-kicker"><ShieldCheck size={15} /> PREDICTED CASH-OUT CLUSTER</div>
        <h2>{hotspot.cluster_id || hotspot.h3_cell}</h2><p className="coordinates"><MapPin size={13} /> {Number(hotspot.lat).toFixed(4)}, {Number(hotspot.lon).toFixed(4)} · {hotspot.severity || 'PREDICTED'} · H3 R{hotspot.resolution || 8}</p>
        <div className="risk-grid"><div><small>RISK SCORE</small><strong>{Math.round(hotspot.risk_score*100)}%</strong></div><div><small>FUNDS AT RISK</small><strong>₹{Number(hotspot.total_amount).toLocaleString('en-IN')}</strong></div><div><small>MULE ACCOUNTS</small><strong>{hotspot.unique_mule_accounts || hotspot.event_count}</strong></div></div>
        <div className="cashout-window"><Clock3 size={20} /><div><small>ESTIMATED CASH-OUT WINDOW</small><strong>{formatCashoutTime(window.start_time, 'Soon')} – {formatCashoutTime(window.end_time, 'Unknown')}</strong></div><b>T−{window.eta_minutes ?? 25} MIN</b></div>
        {hotspot.h3_res9 && <p className="h3-detail">ATM STRIP CELL · <b>{hotspot.h3_res9}</b></p>}
        <h3>TARGET TERMINALS</h3>
        <div className="terminal-list">{hotspot.nearby_atms?.length ? hotspot.nearby_atms.map((atm) => <div key={atm.id}><Building2 size={16} /><span><b>{atm.bank}</b><small>{atm.id}{atm.distanceMeters != null ? ` · ${Math.round(atm.distanceMeters)} m` : ''}{atm.withdrawal_probability != null ? ` · ${Math.round(atm.withdrawal_probability * 100)}% target probability` : ''}</small>{atm.address && <small>{atm.address}</small>}</span></div>) : <p>No physical terminal match available.</p>}</div>
        <div className="action-row"><button disabled={busy} onClick={() => callAction('dispatch')}><MapPin size={15} /> Dispatch PCR Van</button><button disabled={busy} onClick={() => callAction('lien')}><Snowflake size={15} /> Trigger 1930 Lien</button></div>
        {action && <div className="action-result">{action}</div>}
      </section>
    </div>
  )
}
