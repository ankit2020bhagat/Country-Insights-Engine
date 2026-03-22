// src/components/HistoryPanel.jsx
import { useEffect, useState } from 'react'
import { useHistory } from '../hooks/useQuery'
import { StatusBadge } from './StatusBadge'
import './HistoryPanel.css'

const STATUS_OPTS = ['', 'success', 'partial', 'not_found', 'invalid_query', 'error']

export function HistoryPanel() {
  const { items, loading, error, fetch } = useHistory()
  const [statusFilter, setStatusFilter] = useState('')
  const [countryFilter, setCountryFilter] = useState('')
  const [page, setPage] = useState(0)
  const LIMIT = 10

  useEffect(() => {
    fetch({ limit: LIMIT, offset: page * LIMIT, status: statusFilter || undefined, country: countryFilter || undefined })
  }, [statusFilter, countryFilter, page, fetch])

  return (
    <div className="history-panel">
      <div className="history-panel__toolbar">
        <h2 className="history-panel__title">Query History</h2>
        <div className="history-panel__filters">
          <input
            className="history-filter-input"
            placeholder="country…"
            value={countryFilter}
            onChange={e => { setCountryFilter(e.target.value); setPage(0) }}
          />
          <select
            className="history-filter-select"
            value={statusFilter}
            onChange={e => { setStatusFilter(e.target.value); setPage(0) }}
          >
            {STATUS_OPTS.map(s => (
              <option key={s} value={s}>{s || 'all statuses'}</option>
            ))}
          </select>
        </div>
      </div>

      {loading && (
        <div className="history-panel__loading">
          <span className="history-spinner" />
          loading…
        </div>
      )}

      {error && (
        <div className="history-panel__error">Failed to load history: {error}</div>
      )}

      {!loading && items.length === 0 && (
        <div className="history-panel__empty">No queries yet</div>
      )}

      <div className="history-list">
        {items.map((item, i) => (
          <div key={item.query_id} className="history-item" style={{ animationDelay: `${i * 30}ms` }}>
            <div className="history-item__top">
              <StatusBadge status={item.status} size="sm" />
              {item.country_name && (
                <span className="history-item__country">{item.country_name}</span>
              )}
              <span className="history-item__time">{formatTime(item.created_at)}</span>
              {item.duration_ms && (
                <span className="history-item__ms">{item.duration_ms}ms</span>
              )}
            </div>
            <p className="history-item__query">{item.user_query}</p>
            {item.answer && (
              <p className="history-item__answer">{truncate(item.answer, 120)}</p>
            )}
          </div>
        ))}
      </div>

      {items.length > 0 && (
        <div className="history-panel__pagination">
          <button
            className="history-page-btn"
            onClick={() => setPage(p => Math.max(0, p - 1))}
            disabled={page === 0}
          >← prev</button>
          <span className="history-page-num">page {page + 1}</span>
          <button
            className="history-page-btn"
            onClick={() => setPage(p => p + 1)}
            disabled={items.length < LIMIT}
          >next →</button>
        </div>
      )}
    </div>
  )
}

function formatTime(iso) {
  if (!iso) return ''
  return new Date(iso).toLocaleString(undefined, {
    month: 'short', day: 'numeric',
    hour: '2-digit', minute: '2-digit',
  })
}

function truncate(str, n) {
  return str.length > n ? str.slice(0, n) + '…' : str
}
