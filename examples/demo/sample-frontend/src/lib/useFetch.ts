import { useCallback, useEffect, useRef, useState } from 'react'

interface Result<T> { key: string; tick: number; data: T | null; error: string | null }

/**
 * Load data on mount and whenever `deps` change; `reload()` refetches after a mutation.
 * Previous data stays visible while a reload for the same `deps` is in flight.
 */
export function useFetch<T>(fn: () => Promise<T>, deps: unknown[] = []) {
  const key = JSON.stringify(deps)
  const [tick, setTick] = useState(0)
  const [result, setResult] = useState<Result<T> | null>(null)
  const fnRef = useRef(fn)
  useEffect(() => {
    fnRef.current = fn
  })
  useEffect(() => {
    let cancelled = false
    fnRef.current().then(
      (data) => {
        if (!cancelled) setResult({ key, tick, data, error: null })
      },
      (e: unknown) => {
        if (!cancelled) setResult({ key, tick, data: null, error: e instanceof Error ? e.message : String(e) })
      },
    )
    return () => {
      cancelled = true
    }
  }, [key, tick])
  const reload = useCallback(() => setTick((t) => t + 1), [])
  const fresh = result !== null && result.key === key && result.tick === tick
  return {
    data: result !== null && result.key === key ? result.data : null,
    error: fresh ? result.error : null,
    loading: !fresh,
    reload,
  }
}
