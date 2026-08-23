import { useCallback, useEffect, useRef, useState } from 'react'
import { createScenario, mockHotspots, mockTransactions } from '../data/mockData'

const mockMode = import.meta.env.VITE_USE_MOCK_STREAM !== 'false'
const wsUrl = import.meta.env.VITE_WS_URL || 'ws://localhost:8000/ws/alerts'

export function useAlertStream() {
  const [transactions, setTransactions] = useState(mockMode ? mockTransactions : [])
  const [hotspots, setHotspots] = useState(mockMode ? mockHotspots : [])
  const [metrics, setMetrics] = useState({})
  const [status, setStatus] = useState(mockMode ? 'DEMO' : 'CONNECTING')
  const retry = useRef(0)

  const consume = useCallback((payload) => {
    if (!payload || typeof payload !== 'object') return
    if (payload.type === 'INITIAL_STATE') {
      setTransactions((payload.recent_txs || []).reverse())
      setHotspots(payload.hotspots || [])
      setMetrics(payload.system_metrics || {})
    }
    if (payload.transaction && ['NEW_TRANSACTION', 'NEW_ALERT'].includes(payload.type)) {
      setTransactions((items) => [{ ...payload.transaction, timestamp: payload.transaction.timestamp || payload.timestamp }, ...items].slice(0, 100))
    }
    if (payload.hotspots && ['NEW_ALERT', 'HOTSPOTS_UPDATED'].includes(payload.type)) setHotspots(payload.hotspots)
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
    connect()
    return () => { stopped = true; clearTimeout(timer); socket?.close() }
  }, [consume])

  const runScenario = (kind) => {
    const { transaction, hotspot } = createScenario(kind)
    setTransactions((items) => [transaction, ...items].slice(0, 100))
    setHotspots((items) => [hotspot, ...items.filter((item) => item.h3_cell !== hotspot.h3_cell)])
    setMetrics((value) => ({ ...value, total_transactions_ingested: (value.total_transactions_ingested || transactions.length) + 1, total_high_risk_flagged: (value.total_high_risk_flagged || transactions.filter((tx) => tx.is_high_risk).length) + 1 }))
  }

  const resetDemo = () => { setTransactions(mockTransactions); setHotspots(mockHotspots); setMetrics({}) }
  return { transactions, hotspots, metrics, status, runScenario, resetDemo }
}
