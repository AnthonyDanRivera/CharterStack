import { useState } from 'react'
import { buildUrl, errorMessages } from '../api/client'
import {
  boardQuery,
  useBoard,
  useDeleteUnit,
  usePatchUnit,
  useUnitAction,
  type BoardParams,
  type UnitAction,
} from '../api/hooks'
import type { SortDir, Terminal, TripView } from '../api/types'
import DateRangeControl, { type DateRange } from '../components/DateRangeControl'
import MenuButton from '../components/MenuButton'
import { fmtEntered } from '../lib/dates'
import ActionBar from './ActionBar'
import { leafOrder, type LeafKey } from './columns'
import TableGrip from './TableGrip'
import TerminalFilter from './TerminalFilter'
import TripDetail from './TripDetail'
import TripTable from './TripTable'
import { useColumnLayout } from './useColumnLayout'
import { useTableHeight } from './useTableHeight'
import './board.css'

const VIEWS: { value: TripView; label: string }[] = [
  { value: 'today', label: 'Today trips' },
  { value: 'away', label: 'Away trips' },
  { value: 'all', label: 'All trips' },
]

type Props = {
  range: DateRange
  onRangeChange: (range: DateRange) => void
  terminals: string[]
  allTerminals: Terminal[]
  onTerminalsChange: (codes: string[]) => void
  terminalLabel: string
  selectedId: number | null
  onSelect: (id: number | null) => void
}

export default function BoardTab(props: Props) {
  const [view, setView] = useState<TripView>('today')
  const [q, setQ] = useState('')
  const [sort, setSort] = useState<{ key: LeafKey | null; dir: SortDir }>({ key: null, dir: 'asc' })
  const layout = useColumnLayout()
  const [tableHeight, setTableHeight] = useTableHeight()

  const allSelected = props.terminals.length === props.allTerminals.length
  const params: BoardParams = {
    start: props.range.start,
    end: props.range.end,
    view,
    terminals: allSelected ? null : props.terminals,
    q,
    sort: sort.key,
    dir: sort.dir,
  }
  const board = useBoard(params)
  const action = useUnitAction()
  const patch = usePatchUnit()
  const remove = useDeleteUnit()

  const rows = board.data?.rows ?? []
  const selected = rows.find((r) => r.id === props.selectedId) ?? null
  const busy = action.isPending || remove.isPending
  const mutationError = action.error ?? patch.error ?? remove.error

  const run = (act: UnitAction, body?: unknown) => {
    if (!selected) return
    action.mutate(
      { id: selected.id, action: act, body },
      { onSuccess: (unit) => act === 'duplicate' && props.onSelect(unit.id) },
    )
  }
  const onSort = (key: LeafKey) =>
    setSort((s) =>
      s.key === key ? { key, dir: s.dir === 'asc' ? 'desc' : 'asc' } : { key, dir: 'asc' },
    )
  const exportExcel = () => {
    const leafs = leafOrder(layout.order)
    const url = buildUrl('/api/board/export.xlsx', {
      ...boardQuery(params),
      columns: leafs.join(','),
      widths: leafs.map((l) => layout.widths[l]).join(','),
    })
    window.location.assign(url)
  }

  return (
    <>
      <div className="surface board-surface" data-extended={tableHeight !== null}>
        <section aria-label="Toolbar" className="tbar">
          <DateRangeControl range={props.range} onChange={props.onRangeChange} />
          <span className="tsep" aria-hidden="true" />
          <div className="tgroup">
            <TerminalFilter
              terminals={props.allTerminals}
              selected={props.terminals}
              label={props.terminalLabel}
              onChange={props.onTerminalsChange}
            />
            <MenuButton value={view} options={VIEWS} onChange={setView} />
          </div>
          <span className="tnote">
            {board.data ? `Refreshed ${fmtEntered(board.data.refreshed_at)}` : ''}
          </span>
          <button type="button" className="tbtn tdrop" onClick={() => board.refetch()}>
            Refresh
          </button>
        </section>

        <div className="sbar" role="status">
          <span className="cnt">
            <b>{board.data?.counts.trips ?? 0}</b> trips
          </span>
          <span className="cnt">
            <b className="red">{board.data?.counts.need_driver_or_bus ?? 0}</b> need driver or bus
          </span>
          <span className="cnt">
            <b className="red">{board.data?.counts.pending_confirmation ?? 0}</b> pending
            confirmation
          </span>
          <label htmlFor="trip-search" className="sr">
            Search trips
          </label>
          <input
            id="trip-search"
            type="search"
            className="field search"
            placeholder="Search contract, org, group, driver…"
            value={q}
            onChange={(e) => setQ(e.target.value)}
          />
        </div>

        <section aria-label="Trips" className="trips-section">
          {board.isError && !board.data ? (
            <p className="state error">
              Couldn&apos;t load trips.
              <button type="button" className="linkbtn" onClick={() => board.refetch()}>
                Retry
              </button>
            </p>
          ) : board.isPending ? (
            <p className="state">Loading trips…</p>
          ) : (
            <>
              <TripTable
                height={tableHeight}
                rows={rows}
                order={layout.order}
                widths={layout.widths}
                sort={sort.key}
                dir={sort.dir}
                selectedId={props.selectedId}
                onSort={onSort}
                onOrderChange={layout.setOrder}
                onWidthChange={layout.setWidth}
                onSelect={props.onSelect}
                onInitials={(id, initials) =>
                  patch.mutate({ id, patch: { confirm_initials: initials } })
                }
              />
              <TableGrip onChange={setTableHeight} />
            </>
          )}
          {mutationError && (
            <p className="state error" role="alert">
              {errorMessages(mutationError).join(' ')}
            </p>
          )}
          <ActionBar
            selected={selected}
            busy={busy}
            onReported={() => run('reported')}
            onOnLocation={() => run('on-location')}
            onCancel={() => run('cancel')}
            onDuplicate={() => run('duplicate')}
            onDeleteDuplicate={() =>
              selected && remove.mutate(selected.id, { onSuccess: () => props.onSelect(null) })
            }
            onExport={exportExcel}
            onResetColumns={layout.reset}
          />
        </section>
      </div>
      {/* Its own card, so the dotted page background shows between board and details. */}
      <div className="surface detail-surface">
        <TripDetail unitId={selected ? selected.id : null} />
      </div>
    </>
  )
}
