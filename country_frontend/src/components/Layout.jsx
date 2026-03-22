// src/components/Layout.jsx
import { NavLink, Outlet } from 'react-router-dom'
import { HealthBar } from './HealthBar'
import './Layout.css'

const NAV = [
  { to: '/',        label: 'Ask',     icon: <GlobeIcon /> },
  { to: '/history', label: 'History', icon: <HistoryIcon /> },
]

export function Layout() {
  return (
    <div className="layout">
      {/* Sidebar */}
      <aside className="layout__sidebar">
        <div className="layout__logo">
          <span className="layout__logo-mark">CIA</span>
          <span className="layout__logo-text">country<br />intelligence<br />agent</span>
        </div>

        <nav className="layout__nav">
          {NAV.map(({ to, label, icon }) => (
            <NavLink
              key={to}
              to={to}
              end={to === '/'}
              className={({ isActive }) =>
                `layout__nav-item ${isActive ? 'layout__nav-item--active' : ''}`
              }
            >
              <span className="layout__nav-icon">{icon}</span>
              <span className="layout__nav-label">{label}</span>
            </NavLink>
          ))}
        </nav>

        <div className="layout__sidebar-footer">
          <a
            href="/docs"
            target="_blank"
            rel="noopener"
            className="layout__docs-link"
          >
            <DocsIcon />
            API docs
          </a>
          <div className="layout__stack">
            <span className="layout__stack-pill">LangGraph</span>
            <span className="layout__stack-pill">FastAPI</span>
            <span className="layout__stack-pill">PostgreSQL</span>
          </div>
        </div>
      </aside>

      {/* Main */}
      <div className="layout__main">
        <HealthBar />
        <main className="layout__content">
          <Outlet />
        </main>
      </div>
    </div>
  )
}

function GlobeIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="12" cy="12" r="10"/>
      <line x1="2" y1="12" x2="22" y2="12"/>
      <path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/>
    </svg>
  )
}

function HistoryIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      <polyline points="12 8 12 12 14 14"/>
      <path d="M3.05 11a9 9 0 1 0 .5-4"/>
      <polyline points="3 7 3 11 7 11"/>
    </svg>
  )
}

function DocsIcon() {
  return (
    <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
      <polyline points="14 2 14 8 20 8"/>
      <line x1="16" y1="13" x2="8" y2="13"/>
      <line x1="16" y1="17" x2="8" y2="17"/>
      <polyline points="10 9 9 9 8 9"/>
    </svg>
  )
}
