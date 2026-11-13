import type { ContractList } from '../api/types'
import { fmtMoney, fmtUS } from '../lib/dates'

const STATUS_LABEL = { booked: 'Booked', quote: 'Quote', cancelled: 'Cancelled' } as const

type Props = {
  data: ContractList
  currentId: number | null
  onOpen: (id: number) => void
}

/** Contract list: one row per contract, plain contract number (R15). */
export default function ContractTable({ data, currentId, onOpen }: Props) {
  return (
    <div className="ctwrap">
      <table className="ctable">
        <thead>
          <tr>
            <th>Contract #</th>
            <th>Status</th>
            <th>Begin</th>
            <th>Organization</th>
            <th>Group</th>
            <th>Route</th>
            <th>Buses</th>
            <th className="num">Total</th>
            <th className="num">Balance</th>
            <th>Payment</th>
          </tr>
        </thead>
        <tbody>
          {data.results.map((c) => (
            <tr
              key={c.id}
              data-current={c.id === currentId}
              data-cs={c.status}
              onClick={() => onOpen(c.id)}
            >
              <td>
                <button
                  type="button"
                  className="ctlink"
                  onClick={(e) => {
                    e.stopPropagation()
                    onOpen(c.id)
                  }}
                >
                  {c.number}
                </button>
              </td>
              <td>
                <span className="cst" data-cs={c.status}>
                  {STATUS_LABEL[c.status]}
                </span>
              </td>
              <td>
                {fmtUS(c.begin_date)} {c.start_time}
              </td>
              <td>{c.organization}</td>
              <td>{c.group_name}</td>
              <td>
                {c.pickup_city || '—'} → {c.dest_city || '—'}
              </td>
              <td>{c.bus_count}</td>
              <td className="num">{fmtMoney(c.total_price)}</td>
              <td className="num">{fmtMoney(c.balance_due)}</td>
              <td>
                <span className="pay" data-tone={c.payment_tone}>
                  {c.payment_status}
                </span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      {data.results.length === 0 && (
        <p className="state">No contracts match these dates, filter or search.</p>
      )}
    </div>
  )
}
