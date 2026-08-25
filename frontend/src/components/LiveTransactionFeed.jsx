import { Filter, Radio } from 'lucide-react'

const money = (value) => `₹${Number(value || 0).toLocaleString('en-IN')}`

export default function LiveTransactionFeed({ transactions }) {
  return (
    <aside className="feed panel">
      <div className="feed-header"><div><span className="live-pip" /><b>LIVE TRANSACTION FEED</b></div><Filter size={15} /></div>
      <div className="feed-summary"><Radio size={14} /><span>{transactions.length} events buffered</span></div>
      <div className="transaction-list">
        {transactions.length === 0 && <div className="empty-state">Waiting for transaction stream…</div>}
        {transactions.map((tx) => {
          const score = Number(tx.fraud_probability ?? tx.fraud_score ?? 0)
          const level = score >= .85 ? 'critical' : score >= .65 ? 'warning' : 'normal'
          return (
            <article className={`transaction ${level}`} key={`${tx.tx_id}-${tx.timestamp}`}>
              <div className="transaction-top"><span>{tx.tx_id}</span><b>{Math.round(score*100)}%</b></div>
              <div className="transaction-value">{money(tx.amount)} <small>{tx.channel}</small></div>
              <div className="accounts"><span>{tx.src_acc}</span><i>→</i><span>{tx.dest_acc}</span></div>
              {tx.reasons?.[0] && <p>{tx.reasons[0]}</p>}
              <time>{tx.timestamp ? new Date(tx.timestamp*1000).toLocaleTimeString('en-IN') : 'JUST NOW'}</time>
            </article>
          )
        })}
      </div>
    </aside>
  )
}
