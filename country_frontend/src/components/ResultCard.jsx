// src/components/ResultCard.jsx
import { StatusBadge } from './StatusBadge'
import './ResultCard.css'

export function ResultCard({ result, query }) {
  if (!result) return null

  const isError = ['not_found', 'invalid_query', 'error'].includes(result.status)

  return (
    <div className={`result-card result-card--${result.status} anim-fade-up`}>
      {/* Header */}
      <div className="result-card__header">
        <div className="result-card__meta">
          <StatusBadge status={result.status} size="sm" />
          {result.country && (
            <span className="result-card__country">{result.country}</span>
          )}
        </div>
        <div className="result-card__stats">
          {result.cache_hit && (
            <span className="result-card__cache-badge">
              <CacheIcon /> cached
            </span>
          )}
          <span className="result-card__duration">{result.duration_ms}ms</span>
        </div>
      </div>

      {/* Answer */}
      <div className={`result-card__answer ${isError ? 'result-card__answer--error' : ''}`}>
        {result.answer}
      </div>

      {/* Fields row */}
      {result.requested_fields?.length > 0 && (
        <div className="result-card__fields">
          {result.requested_fields.map(f => (
            <span
              key={f}
              className={`result-card__field ${result.missing_fields?.includes(f) ? 'result-card__field--missing' : ''}`}
            >
              {f}
              {result.missing_fields?.includes(f) && ' ✕'}
            </span>
          ))}
        </div>
      )}

      {/* Query echo */}
      <div className="result-card__query">
        <span className="result-card__query-label">q</span>
        <span className="result-card__query-text">{query}</span>
      </div>

      {/* Query ID */}
      <div className="result-card__id">
        <span className="result-card__id-label">id</span>
        <span className="result-card__id-value">{result.query_id}</span>
      </div>
    </div>
  )
}

function CacheIcon() {
  return (
    <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <polyline points="23 4 23 10 17 10"/><path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"/>
    </svg>
  )
}
