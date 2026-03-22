// src/pages/Home.jsx
import { useState } from 'react'
import { SearchBar } from '../components/SearchBar'
import { ResultCard } from '../components/ResultCard'
import { useQuery } from '../hooks/useQuery'
import './Home.css'

const EXAMPLES = [
  { label: 'Population', q: 'What is the population of Germany?' },
  { label: 'Currency',   q: 'What currency does Japan use?' },
  { label: 'Capital',    q: 'What is the capital of France?' },
  { label: 'Languages',  q: 'What languages are spoken in Switzerland?' },
  { label: 'Region',     q: 'What region is South Korea in?' },
  { label: 'Overview',   q: 'Tell me about New Zealand' },
]

export function Home() {
  const { result, loading, error, ask } = useQuery()
  const [lastQuery, setLastQuery] = useState('')

  const handleSubmit = async (q) => {
    setLastQuery(q)
    await ask(q)
  }

  return (
    <div className="home">
      {/* Hero */}
      <div className="home__hero">
        <div className="home__hero-glow" />
        <div className="home__heading-wrap">
          <div className="home__eyebrow">
            <span className="home__eyebrow-dot" />
            country intelligence agent
          </div>
          <h1 className="home__heading">
            Ask anything about<br />
            <span className="home__heading-accent">any country</span>
          </h1>
          <p className="home__subheading">
            Powered by LangGraph + Claude · Live data from REST Countries API · PostgreSQL-cached
          </p>
        </div>

        <div className="home__search-wrap">
          <SearchBar onSubmit={handleSubmit} loading={loading} />
        </div>

        {/* Example chips */}
        <div className="home__examples">
          {EXAMPLES.map(ex => (
            <button
              key={ex.label}
              className="home__example-chip"
              onClick={() => handleSubmit(ex.q)}
              disabled={loading}
            >
              <span className="home__example-label">{ex.label}</span>
              <span className="home__example-q">{ex.q}</span>
            </button>
          ))}
        </div>
      </div>

      {/* Result */}
      <div className="home__result">
        {error && (
          <div className="home__api-error anim-fade-up">
            <span className="home__api-error-icon">⚠</span>
            {error}
          </div>
        )}
        {result && (
          <ResultCard result={result} query={lastQuery} />
        )}

        {!result && !error && !loading && (
          <div className="home__placeholder">
            <div className="home__placeholder-grid">
              {[...Array(6)].map((_, i) => (
                <div key={i} className="home__placeholder-cell" style={{ opacity: 0.06 + i * 0.03 }} />
              ))}
            </div>
            <p className="home__placeholder-text">your answer will appear here</p>
          </div>
        )}
      </div>
    </div>
  )
}
