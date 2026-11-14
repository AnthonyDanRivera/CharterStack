import { useEffect, useState } from 'react'

const STORAGE_KEY = 'charterstack.board.tableHeight.v1'
export const MIN_TABLE_HEIGHT = 200
const MAX_TABLE_HEIGHT = 4000

export function clampHeight(h: number): number {
  return Math.round(Math.min(MAX_TABLE_HEIGHT, Math.max(MIN_TABLE_HEIGHT, h)))
}

function load(): number | null {
  try {
    const n = Number(window.localStorage.getItem(STORAGE_KEY))
    return Number.isFinite(n) && n >= MIN_TABLE_HEIGHT ? clampHeight(n) : null
  } catch {
    return null
  }
}

/** Trip table height set with the grab bar; null means it fits the window. */
export function useTableHeight() {
  const [height, setHeight] = useState<number | null>(load)

  useEffect(() => {
    try {
      if (height === null) window.localStorage.removeItem(STORAGE_KEY)
      else window.localStorage.setItem(STORAGE_KEY, String(height))
    } catch {
      // Storage blocked: the height still applies for this page view.
    }
  }, [height])

  return [height, setHeight] as const
}
