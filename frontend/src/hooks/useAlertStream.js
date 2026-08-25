import { useCallback, useEffect, useRef, useState } from 'react'
import { normalizeHotspot, normalizeTransaction } from '../utils/normalize'

const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
const defaultHost = window.location.hostname ? `${window.location.hostname}:8000` : 'localhost:8000'
const wsUrl = import.meta.env.VITE_WS_URL || `${wsProtocol}//${defaultHost}/ws/alerts`
const apiUrl = import.meta.env.VITE_API_BASE_URL || `http://${defaultHost}`

export function useAlertStream() {
  const [transactions, setTransactions] = useState([])
  const [hotspots, setHotspots] = useState([])
  const [metrics, setMetrics] = useState({})
  const [actionHistory, setActionHistory] = useState({ total_dispatches: 0, total_liens: 0 })
  const [latestAction, setLatestAction] = useState(null)
  const [status, setStatus] = useState('CONNECTING')
  const retry = useRef(0)
  
  // Buffers for high-throughput batching to prevent React freeze
  const txBuffer = useRef([])
  const hotspotBuffer = useRef(null)

  const consume = useCallback((payload) => {
    if (!payload || typeof payload !== 'object') return
    if (payload.type === 'INITIAL_STATE') {
      setTransactions([...(payload.recent_txs || [])].reverse().map(normalizeTransaction))
      setHotspots((payload.hotspots || []).map(normalizeHotspot))
      setMetrics(payload.system_metrics || {})
    }
    if (payload.transaction && ['NEW_TRANSACTION', 'NEW_ALERT'].includes(payload.type)) {
      txBuffer.current.push(normalizeTransaction({ ...payload.transaction, timestamp: payload.transaction.timestamp || payload.timestamp }))
    }
    if (payload.hotspots && ['NEW_ALERT', 'HOTSPOTS_UPDATED'].includes(payload.type)) {
      hotspotBuffer.current = payload.hotspots.map(normalizeHotspot)
    }
    if (['COMPLAINT_REGISTERED', 'PATROL_DISPATCHED', 'LIEN_PLACED'].includes(payload.type)) setLatestAction(payload)
  }, [])

  useEffect(() => {
    let socket
    let timer
    let stopped = false
    
    // Batch flush interval for extremely high TPS
    const flushTimer = setInterval(() => {
      if (txBuffer.current.length > 0) {
        const batch = txBuffer.current
        txBuffer.current = []
        setTransactions((items) => [...batch.reverse(), ...items].slice(0, 100))
      }
      if (hotspotBuffer.current !== null) {
        setHotspots(hotspotBuffer.current)
        hotspotBuffer.current = null
      }
    }, 100) // 10 FPS batching is butter smooth
    
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
    return () => { stopped = true; clearTimeout(timer); clearInterval(refreshTimer); clearInterval(flushTimer); socket?.close() }
  }, [consume])

  return { transactions, hotspots, metrics, actionHistory, status, latestAction }
}
