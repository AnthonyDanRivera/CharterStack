/** Every 15 minutes, 00:00 to 23:45. */
export const TIME_LIST: string[] = Array.from({ length: 96 }, (_, i) => {
  const h = Math.floor(i / 4)
  const m = (i % 4) * 15
  return `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}`
})

export const ONE_WAY = 'One way'

/**
 * Instant-feedback copy of R02 so the field tidies up on blur. The server
 * parses the same forms and has the final say. Returns null for input it
 * can't read.
 */
export function normalizeTime(text: string, allowOneWay = false): string | null {
  let t = text.trim().toUpperCase().replace(/\./g, '').replace(/\s+/g, ' ')
  if (!t) return ''
  if (/^ONE ?WAY$/.test(t) || t === 'OW') return allowOneWay ? ONE_WAY : null
  let meridiem: string | null = null
  const m = t.match(/\s?(AM|PM|A|P)$/)
  if (m) {
    meridiem = m[1][0]
    t = t.slice(0, t.length - m[0].length).trim()
  }
  let h: number
  let min: number
  if (/^\d{1,2}:\d{1,2}$/.test(t)) {
    const [a, b] = t.split(':')
    h = Number(a)
    min = Number(b)
  } else if (/^\d{3,4}$/.test(t)) {
    h = Number(t.slice(0, -2))
    min = Number(t.slice(-2))
  } else if (/^\d{1,2}$/.test(t)) {
    h = Number(t)
    min = 0
  } else return null
  if (min > 59) return null
  if (meridiem) {
    if (h < 1 || h > 12) return null
    h = (h % 12) + (meridiem === 'P' ? 12 : 0)
  }
  if (h > 23) return null
  return `${String(h).padStart(2, '0')}:${String(min).padStart(2, '0')}`
}

/** Options whose digits start with what was typed (`7` → 07:00…, `73` → 07:30). */
export function matchTimes(typed: string, list: string[] = TIME_LIST): string[] {
  const digits = typed.replace(/\D/g, '')
  if (!digits) return list
  return list.filter((t) => {
    const d = t.replace(':', '')
    return d.startsWith(digits) || d.startsWith('0' + digits)
  })
}
