// src/components/SearchBar.jsx
import { useState, useRef, useEffect } from 'react'
import './SearchBar.css'

const SUGGESTIONS = [
  'What is the population of Germany?',
  'What currency does Japan use?',
  'Capital and population of Brazil?',
  'What languages are spoken in Switzerland?',
  'Tell me about New Zealand',
  'What region is South Korea in?',
  'What is the area of Russia?',
  'Timezones in the United States?',
]

export function SearchBar({ onSubmit, loading }) {
  const [value, setValue] = useState('')
  const [focused, setFocused] = useState(false)
  const [suggIdx, setSuggIdx] = useState(0)
  const inputRef = useRef(null)

  // cycle placeholder suggestions
  useEffect(() => {
    const id = setInterval(() => setSuggIdx(i => (i + 1) % SUGGESTIONS.length), 3000)
    return () => clearInterval(id)
  }, [])

  const handleSubmit = (e) => {
    e.preventDefault()
    if (value.trim().length >= 3 && !loading) onSubmit(value.trim())
  }

  const handleKey = (e) => {
    if (e.key === 'Escape') { setValue(''); inputRef.current?.blur() }
  }

  return (
    <form className={`search-bar ${focused ? 'search-bar--focused' : ''} ${loading ? 'search-bar--loading' : ''}`} onSubmit={handleSubmit}>
      <div className="search-bar__icon">
        {loading
          ? <span className="search-bar__spinner" />
          : <GlobeIcon />
        }
      </div>

      <input
        ref={inputRef}
        className="search-bar__input"
        value={value}
        onChange={e => setValue(e.target.value)}
        onFocus={() => setFocused(true)}
        onBlur={() => setFocused(false)}
        onKeyDown={handleKey}
        placeholder={SUGGESTIONS[suggIdx]}
        disabled={loading}
        autoComplete="off"
        spellCheck="false"
      />

      {value && (
        <button
          type="button"
          className="search-bar__clear"
          onClick={() => { setValue(''); inputRef.current?.focus() }}
          tabIndex={-1}
        >
          ✕
        </button>
      )}

      <button
        type="submit"
        className="search-bar__submit"
        disabled={value.trim().length < 3 || loading}
      >
        {loading ? 'thinking…' : 'ask'}
      </button>
    </form>
  )
}

function GlobeIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="12" cy="12" r="10"/>
      <line x1="2" y1="12" x2="22" y2="12"/>
      <path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/>
    </svg>
  )
}
