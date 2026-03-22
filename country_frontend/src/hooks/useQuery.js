// src/hooks/useQuery.js
import { useState, useCallback } from 'react'
import { api } from '../lib/api'

export function useQuery() {
  const [state, setState] = useState({
    result: null,
    loading: false,
    error: null,
    history: [],
  })

  const ask = useCallback(async (query) => {
    setState(s => ({ ...s, loading: true, error: null, result: null }))
    try {
      const result = await api.query(query)
      setState(s => ({
        ...s,
        result,
        loading: false,
        history: [{ query, result, ts: Date.now() }, ...s.history].slice(0, 20),
      }))
      return result
    } catch (err) {
      setState(s => ({ ...s, loading: false, error: err.message }))
      return null
    }
  }, [])

  const clear = useCallback(() => {
    setState(s => ({ ...s, result: null, error: null }))
  }, [])

  return { ...state, ask, clear }
}

export function useHistory() {
  const [state, setState] = useState({ items: [], loading: false, error: null, total: 0 })

  const fetch = useCallback(async (params) => {
    setState(s => ({ ...s, loading: true, error: null }))
    try {
      const items = await api.history(params)
      setState({ items, loading: false, error: null, total: items.length })
    } catch (err) {
      setState(s => ({ ...s, loading: false, error: err.message }))
    }
  }, [])

  return { ...state, fetch }
}

export function useHealth() {
  const [state, setState] = useState({ data: null, loading: false })

  const check = useCallback(async () => {
    setState({ data: null, loading: true })
    try {
      const data = await api.health()
      setState({ data, loading: false })
    } catch {
      setState({ data: { status: 'error', db: 'error' }, loading: false })
    }
  }, [])

  return { ...state, check }
}
