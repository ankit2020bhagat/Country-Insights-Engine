// src/components/StatusBadge.jsx
import './StatusBadge.css'

const CONFIG = {
  success:       { label: 'success',       color: 'jade'  },
  partial:       { label: 'partial',       color: 'amber' },
  not_found:     { label: 'not found',     color: 'red'   },
  invalid_query: { label: 'invalid query', color: 'red'   },
  error:         { label: 'error',         color: 'red'   },
}

export function StatusBadge({ status, size = 'md' }) {
  const cfg = CONFIG[status] || { label: status, color: 'dim' }
  return (
    <span className={`status-badge status-badge--${cfg.color} status-badge--${size}`}>
      <span className="status-badge__dot" />
      {cfg.label}
    </span>
  )
}
