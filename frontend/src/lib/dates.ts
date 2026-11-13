// Date display helpers. Dates travel as ISO `YYYY-MM-DD` strings; all math is
// done in UTC so a local DST change can never shift a day.

const WEEKDAYS = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']
const MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
export const MONTH_NAMES = [
  'January',
  'February',
  'March',
  'April',
  'May',
  'June',
  'July',
  'August',
  'September',
  'October',
  'November',
  'December',
]

const pad = (n: number) => String(n).padStart(2, '0')

export function toDate(iso: string): Date {
  const [y, m, d] = iso.slice(0, 10).split('-').map(Number)
  return new Date(Date.UTC(y, m - 1, d))
}

export function toIso(date: Date): string {
  return `${date.getUTCFullYear()}-${pad(date.getUTCMonth() + 1)}-${pad(date.getUTCDate())}`
}

/** Today in the browser's local time zone. */
export function todayIso(now: Date = new Date()): string {
  return `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())}`
}

export function addDays(iso: string, days: number): string {
  const d = toDate(iso)
  d.setUTCDate(d.getUTCDate() + days)
  return toIso(d)
}

export function daysBetween(a: string, b: string): number {
  return Math.round((toDate(b).getTime() - toDate(a).getTime()) / 86400000)
}

/** Previous / next shift the range by its own length (R24). */
export function shiftRange(start: string, end: string, direction: 1 | -1) {
  const length = daysBetween(start, end) + 1
  return { start: addDays(start, direction * length), end: addDays(end, direction * length) }
}

/** `Mon, Nov 9, 2026` */
export function fmtLong(iso: string): string {
  const d = toDate(iso)
  return `${WEEKDAYS[d.getUTCDay()]}, ${MONTHS[d.getUTCMonth()]} ${d.getUTCDate()}, ${d.getUTCFullYear()}`
}

/** `11/09/2026` (board dates, no weekday) */
export function fmtUS(iso: string): string {
  const d = toDate(iso)
  return `${pad(d.getUTCMonth() + 1)}/${pad(d.getUTCDate())}/${d.getUTCFullYear()}`
}

/** `Mon 11/09` */
export function fmtWeekdayShort(iso: string): string {
  const d = toDate(iso)
  return `${WEEKDAYS[d.getUTCDay()]} ${pad(d.getUTCMonth() + 1)}/${pad(d.getUTCDate())}`
}

/** `MM/DD HH:MM` from an ISO datetime the server already put in the visitor's zone. */
export function fmtEntered(isoDateTime: string | null): string {
  if (!isoDateTime) return ''
  return `${isoDateTime.slice(5, 7)}/${isoDateTime.slice(8, 10)} ${isoDateTime.slice(11, 16)}`
}

/** `HH:MM` from a full ISO datetime in the visitor's zone. */
export function fmtClock(isoDateTime: string): string {
  return isoDateTime.slice(11, 16)
}

/** Session strip date: `Thu 11/12/2026` */
export function fmtStripDate(now: Date): string {
  return `${WEEKDAYS[now.getDay()]} ${pad(now.getMonth() + 1)}/${pad(now.getDate())}/${now.getFullYear()}`
}

export function fmtStripTime(now: Date): string {
  return `${pad(now.getHours())}:${pad(now.getMinutes())}:${pad(now.getSeconds())}`
}

export function fmtDuration(ms: number): string {
  const total = Math.max(0, Math.floor(ms / 1000))
  return `${pad(Math.floor(total / 3600))}:${pad(Math.floor((total % 3600) / 60))}:${pad(total % 60)}`
}

/** `$1,200.00` from a server decimal string (R13 display). */
export function fmtMoney(value: string | null | undefined): string {
  if (value === null || value === undefined || value === '') return '—'
  const n = Number(value)
  if (!Number.isFinite(n)) return '—'
  return '$' + n.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}
