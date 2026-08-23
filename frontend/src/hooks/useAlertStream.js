import { useCallback, useEffect, useRef, useState } from 'react'
import { createScenario, mockHotspots, mockTransactions } from '../data/mockData'
import { normalizeHotspot, normalizeTransaction } from '../utils/normalize'

const mockMode = import.meta.env.VITE_USE_MOCK_STREAM !== 'false'
const wsUrl = import.meta.env.VITE_WS_URL || 'ws://localhost:8000/ws/alerts'
const apiUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

export function useAlertStream() {
  const [transactions, setTransactions] = useState(mockMode ? mockTransactions.map(normalizeTransaction) : [])
  const [hotspots, setHotspots] = useState(mockMode ? mockHotspots.map(normalizeHotspot) : [])
  const [metrics, setMetrics] = useState({})
  const [actionHistory, setActionHistory] = useState({ total_dispatches: 0, total_liens: 0 })
  const [latestAction, setLatestAction] = useState(null)
  const [status, setStatus] = useState(mockMode ? 'DEMO' : 'CONNECTING')
  const retry = useRef(0)

  const consume = useCallback((payload) => {
    if (!payload || typeof payload !== 'object') return
    if (payload.type === 'INITIAL_STATE') {
      setTransactions([...(payload.recent_txs || [])].reverse().map(normalizeTransaction))
      setHotspots((payload.hotspots || []).map(normalizeHotspot))
      setMetrics(payload.system_metrics || {})
    }
    if (payload.transaction && ['NEW_TRANSACTION', 'NEW_ALERT'].includes(payload.type)) {
      setTransactions((items) => [normalizeTransaction({ ...payload.transaction, timestamp: payload.transaction.timestamp || payload.timestamp }), ...items].slice(0, 100))
    }
    if (payload.hotspots && ['NEW_ALERT', 'HOTSPOTS_UPDATED'].includes(payload.type)) setHotspots(payload.hotspots.map(normalizeHotspot))
    if (['COMPLAINT_REGISTERED', 'PATROL_DISPATCHED', 'LIEN_PLACED'].includes(payload.type)) setLatestAction(payload)
  }, [])

  useEffect(() => {
    if (mockMode) return undefined
    let socket
    let timer
    let stopped = false
    const connect = () => {
      setStatus('CONNECTING')
      socket = new WebSocket(wsUrl)
      socket.onopen = () => { retry.current = 0; setStatus('LIVE') }
      socket.onmessage = (event) => { try { consume(JSON.parse(event.data)) } catch { /* ignore invalid frames */ } }
      socket.onerror = () => socket.close()
      socket.onclose = () => {
        if (stopped) return
        setStatus('OFFLINE')
        const delay = Math.min(1000 * (2 ** retry.current++), 15000)
        timer = setTimeout(connect, delay)
      }
    }
    const fetchJson = (path) => fetch(`${apiUrl}${path}`).then((response) => response.ok ? response.json() : Promise.reject())
    const refreshRestState = () => Promise.allSettled([
      fetchJson('/api/v1/hotspots/active').then((data) => setHotspots((data.hotspots || []).map(normalizeHotspot))),
      fetchJson('/api/v1/transactions/recent?limit=50').then((data) => setTransactions([...(data.transactions || [])].reverse().map(normalizeTransaction))),
      fetchJson('/api/v1/system/status').then((data) => setMetrics(data.metrics || {})),
      fetchJson('/api/v1/actions/history').then(setActionHistory),
    ])
    refreshRestState()
    const refreshTimer = setInterval(refreshRestState, 15000)
    connect()
    return () => { stopped = true; clearTimeout(timer); clearInterval(refreshTimer); socket?.close() }
  }, [consume])

  const runScenario = (kind) => {
    const { transaction, hotspot } = createScenario(kind)
    setTransactions((items) => [normalizeTransaction(transaction), ...items].slice(0, 100))
    const normalized = normalizeHotspot(hotspot)
    setHotspots((items) => [normalized, ...items.filter((item) => item.h3_cell !== normalized.h3_cell)])
    setMetrics((value) => ({ ...value, total_transactions_ingested: (value.total_transactions_ingested || transactions.length) + 1, total_high_risk_flagged: (value.total_high_risk_flagged || transactions.filter((tx) => tx.is_high_risk).length) + 1 }))
  }

  const resetDemo = () => { setTransactions(mockTransactions.map(normalizeTransaction)); setHotspots(mockHotspots.map(normalizeHotspot)); setMetrics({}); setActionHistory({ total_dispatches: 0, total_liens: 0 }); setLatestAction(null) }
  return { transactions, hotspots, metrics, actionHistory, status, latestAction, runScenario, resetDemo }
}
