import { useCallback, useEffect, useState } from 'react'
import { DEFAULT_ORDER, DEFAULT_WIDTHS, MIN_WIDTH, type LeafKey } from './columns'

const STORAGE_KEY = 'charterstack.board.columns.v1'

type Layout = { order: string[]; widths: Record<LeafKey, number> }

function defaults(): Layout {
  return { order: [...DEFAULT_ORDER], widths: { ...DEFAULT_WIDTHS } }
}

/** Saved layout, ignoring anything stale (unknown keys, missing columns). */
export function loadLayout(): Layout {
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY)
    if (!raw) return defaults()
    const saved = JSON.parse(raw) as Partial<Layout>
    const order = Array.isArray(saved.order) ? saved.order : []
    const valid =
      order.length === DEFAULT_ORDER.length && DEFAULT_ORDER.every((k) => order.includes(k))
    const widths = { ...DEFAULT_WIDTHS }
    for (const key of Object.keys(DEFAULT_WIDTHS) as LeafKey[]) {
      const w = saved.widths?.[key]
      if (typeof w === 'number' && w >= MIN_WIDTH && w < 2000) widths[key] = Math.round(w)
    }
    return { order: valid ? order : [...DEFAULT_ORDER], widths }
  } catch {
    return defaults()
  }
}

/** Column order and widths, remembered per browser in localStorage. */
export function useColumnLayout() {
  const [layout, setLayout] = useState<Layout>(loadLayout)

  useEffect(() => {
    try {
      window.localStorage.setItem(STORAGE_KEY, JSON.stringify(layout))
    } catch {
      // Storage full or blocked: the layout still works for this page view.
    }
  }, [layout])

  const setOrder = useCallback((order: string[]) => setLayout((l) => ({ ...l, order })), [])
  const setWidth = useCallback(
    (key: LeafKey, width: number) =>
      setLayout((l) => ({ ...l, widths: { ...l.widths, [key]: Math.max(MIN_WIDTH, width) } })),
    [],
  )
  const reset = useCallback(() => setLayout(defaults()), [])

  return { ...layout, setOrder, setWidth, reset }
}
