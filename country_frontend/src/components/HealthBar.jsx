// src/components/HealthBar.jsx
import { useEffect } from 'react'
import { useHealth } from '../hooks/useQuery'
import './HealthBar.css'

export function HealthBar() {
  const { data, loading, check } = useHealth()

  useEffect(() => {
    check()
    const id = setInterval(check, 30_000)
    return () => clearInterval(id)
  }, [check])

  const ok = data?.status === 'ok' && data?.db === 'ok'

  return (
    <div className={`health-bar ${data ? (ok ? 'health-bar--ok' : 'health-bar--err') : ''}`}>
      <span className="health-bar__dot" />
      <span className="health-bar__label">
        {loading && !data ? 'connecting…' : ok ? 'API online' : 'API offline'}
      </span>
      {data && (
        <>
          <span className="health-bar__sep">·</span>
          <span className={`health-bar__db ${data.db === 'ok' ? 'health-bar__db--ok' : 'health-bar__db--err'}`}>
            db {data.db}
          </span>
          {data.version && (
            <>
              <span className="health-bar__sep">·</span>
              <span className="health-bar__version">v{data.version}</span>
            </>
          )}
          {data.environment && (
            <>
              <span className="health-bar__sep">·</span>
              <span className="health-bar__env">{data.environment}</span>
            </>
          )}
        </>
      )}
      <button className="health-bar__refresh" onClick={check} title="Refresh health">
        ↻
      </button>
    </div>
  )
}
