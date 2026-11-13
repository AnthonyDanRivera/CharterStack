import { useColorBlindPalette } from '../lib/palette'

/** Swaps red/green status colors for orange/blue (docs/UI_GUIDE.md). */
export default function PaletteToggle() {
  const [on, toggle] = useColorBlindPalette()
  return (
    <button
      type="button"
      className="tbtn st-palette"
      data-on={on}
      aria-pressed={on}
      onClick={toggle}
    >
      Color-blind palette
    </button>
  )
}
