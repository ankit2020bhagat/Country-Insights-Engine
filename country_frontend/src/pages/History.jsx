// src/pages/History.jsx
import { HistoryPanel } from '../components/HistoryPanel'
import './History.css'

export function History() {
  return (
    <div className="history-page">
      <div className="history-page__inner">
        <div className="history-page__header">
          <h1 className="history-page__title">Query History</h1>
          <p className="history-page__sub">Every agent invocation, logged to PostgreSQL</p>
        </div>
        <div className="history-page__panel">
          <HistoryPanel />
        </div>
      </div>
    </div>
  )
}
