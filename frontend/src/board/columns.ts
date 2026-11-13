// Board columns (docs/UI_GUIDE.md). A "unit" is what moves when a column is
// dragged: a single column or a pair that shares a group label.

export type LeafKey =
  | 'contract'
  | 'day'
  | 'terminal'
  | 'beginDate'
  | 'startTime'
  | 'reportTime'
  | 'actualReport'
  | 'spotTime'
  | 'onLocAt'
  | 'org'
  | 'pickup'
  | 'dest'
  | 'group'
  | 'driver'
  | 'busNum'
  | 'sizeReq'
  | 'returnDate'
  | 'returnTime'
  | 'confInit'
  | 'confAt'
  | 'driverPhone'
  | 'hasNotes'
  | 'notesText'

export type ColumnUnit = { key: string; label?: string; cols: LeafKey[] }

export const UNITS: ColumnUnit[] = [
  { key: 'contract', cols: ['contract'] },
  { key: 'day', cols: ['day'] },
  { key: 'terminal', cols: ['terminal'] },
  { key: 'begin', label: 'Begin date / start time', cols: ['beginDate', 'startTime'] },
  { key: 'reportTime', cols: ['reportTime'] },
  { key: 'actualReport', cols: ['actualReport'] },
  { key: 'spotTime', cols: ['spotTime'] },
  { key: 'onLocAt', cols: ['onLocAt'] },
  { key: 'org', cols: ['org'] },
  { key: 'pudest', label: 'Pickup / Destination', cols: ['pickup', 'dest'] },
  { key: 'group', cols: ['group'] },
  { key: 'driver', cols: ['driver'] },
  { key: 'bus', label: 'Bus # / Size req.', cols: ['busNum', 'sizeReq'] },
  { key: 'ret', label: 'Return date / time', cols: ['returnDate', 'returnTime'] },
  { key: 'conf', label: 'Confirmation', cols: ['confInit', 'confAt'] },
  { key: 'driverPhone', cols: ['driverPhone'] },
  { key: 'hasNotes', cols: ['hasNotes'] },
  { key: 'notesText', cols: ['notesText'] },
]

export const DEFAULT_ORDER = UNITS.map((u) => u.key)
export const UNIT_BY_KEY = Object.fromEntries(UNITS.map((u) => [u.key, u])) as Record<
  string,
  ColumnUnit
>

export const LABELS: Record<LeafKey, string> = {
  contract: 'Contract #',
  day: 'Day',
  terminal: 'Terminal',
  beginDate: 'Begin date',
  startTime: 'Start time',
  reportTime: 'Report time',
  actualReport: 'Actual report',
  spotTime: 'Spot',
  onLocAt: 'On location',
  org: 'Organization',
  pickup: 'Pickup',
  dest: 'Destination',
  group: 'Group name',
  driver: 'Driver',
  busNum: 'Bus #',
  sizeReq: 'Size req.',
  returnDate: 'Return date',
  returnTime: 'Return time',
  confInit: 'Initials',
  confAt: 'Entered',
  driverPhone: 'Driver phone',
  hasNotes: 'Notes',
  notesText: 'Dispatch notes',
}

export const DEFAULT_WIDTHS: Record<LeafKey, number> = {
  contract: 96,
  day: 58,
  terminal: 86,
  beginDate: 86,
  startTime: 68,
  reportTime: 78,
  actualReport: 78,
  spotTime: 60,
  onLocAt: 84,
  org: 108,
  pickup: 122,
  dest: 122,
  group: 96,
  driver: 98,
  busNum: 66,
  sizeReq: 84,
  returnDate: 86,
  returnTime: 68,
  confInit: 70,
  confAt: 80,
  driverPhone: 104,
  hasNotes: 56,
  notesText: 200,
}

export const MIN_WIDTH = 44

export function leafOrder(order: string[]): LeafKey[] {
  return order.flatMap((k) => UNIT_BY_KEY[k]?.cols ?? [])
}
