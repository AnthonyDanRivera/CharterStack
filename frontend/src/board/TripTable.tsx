import type { BoardRow, SortDir } from '../api/types'
import { leafOrder, type LeafKey } from './columns'
import TableHeader from './TableHeader'
import TripRow from './TripRow'

type Props = {
  rows: BoardRow[]
  order: string[]
  widths: Record<LeafKey, number>
  sort: string | null
  dir: SortDir
  selectedId: number | null
  onSort: (key: LeafKey) => void
  onOrderChange: (order: string[]) => void
  onWidthChange: (key: LeafKey, width: number) => void
  onSelect: (id: number) => void
  onInitials: (id: number, initials: string) => void
}

/** The trip grid: sticky two-row header and one row per unit, scrolling sideways. */
export default function TripTable(props: Props) {
  const leafs = leafOrder(props.order)
  const template = leafs.map((l) => `${props.widths[l]}px`).join(' ')
  const minWidth = leafs.reduce((s, l) => s + props.widths[l], 0)

  return (
    <div className="tablewrap">
      <div style={{ minWidth }}>
        <div className="thead">
          <TableHeader
            order={props.order}
            widths={props.widths}
            sort={props.sort}
            dir={props.dir}
            onSort={props.onSort}
            onOrderChange={props.onOrderChange}
            onWidthChange={props.onWidthChange}
          />
        </div>
        {props.rows.map((row) => (
          <TripRow
            key={row.id}
            row={row}
            leafs={leafs}
            gridTemplate={template}
            selected={row.id === props.selectedId}
            onSelect={() => props.onSelect(row.id)}
            onInitials={(initials) => props.onInitials(row.id, initials)}
          />
        ))}
        {props.rows.length === 0 && <p className="state">No trips match these dates or search.</p>}
      </div>
    </div>
  )
}
