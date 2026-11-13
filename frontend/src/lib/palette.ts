import { useState } from 'react'

const STORAGE_KEY = 'charterstack.palette'

/** Whether the color-blind palette is saved for this browser. */
export function readColorBlind(): boolean {
  try {
    return window.localStorage.getItem(STORAGE_KEY) === 'cb'
  } catch {
    return false
  }
}

/** Switch the whole app's palette (tokens.css reads :root[data-palette]). */
export function applyColorBlind(on: boolean): void {
  if (on) document.documentElement.dataset.palette = 'cb'
  else delete document.documentElement.dataset.palette
}

/** The color-blind palette setting, applied to the page and remembered per browser. */
export function useColorBlindPalette(): [boolean, () => void] {
  const [on, setOn] = useState(readColorBlind)
  const toggle = () => {
    const next = !on
    setOn(next)
    applyColorBlind(next)
    try {
      if (next) window.localStorage.setItem(STORAGE_KEY, 'cb')
      else window.localStorage.removeItem(STORAGE_KEY)
    } catch {
      // Storage blocked: the palette still applies for this page view.
    }
  }
  return [on, toggle]
}
