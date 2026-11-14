import { useState } from 'react'
import { errorMessages } from '../api/client'
import {
  useAllContracts,
  useContract,
  useContracts,
  useDeleteContract,
  useReference,
} from '../api/hooks'
import type { Contract, ContractFilter, ContractRow } from '../api/types'
import DateRangeControl, { type DateRange } from '../components/DateRangeControl'
import MenuButton from '../components/MenuButton'
import { fmtMoney } from '../lib/dates'
import ContractFormView from './ContractFormView'
import ContractLookup from './ContractLookup'
import ContractTable from './ContractTable'
import ContractView from './ContractView'
import './booking.css'

const FILTERS: { value: ContractFilter; label: string }[] = [
  { value: 'all', label: 'All contracts' },
  { value: 'active', label: 'Active contracts' },
  { value: 'booked', label: 'Booked' },
  { value: 'quote', label: 'Quotes' },
  { value: 'cancelled', label: 'Cancelled' },
]

type Mode = { kind: 'view' } | { kind: 'insert' } | { kind: 'edit' }

type Props = {
  range: DateRange
  onRangeChange: (range: DateRange) => void
  onOpenOnBoard: (unitId: number | null, date: string) => void
}

export default function BookingTab({ range, onRangeChange, onOpenOnBoard }: Props) {
  const [filter, setFilter] = useState<ContractFilter>('all')
  const [q, setQ] = useState('')
  const [currentId, setCurrentId] = useState<number | null>(null)
  const [mode, setMode] = useState<Mode>({ kind: 'view' })
  const [deleted, setDeleted] = useState<number[]>([])
  const list = useContracts({ start: range.start, end: range.end, status: filter, q })
  const all = useAllContracts()
  // A contract is always open: the one picked, else the first in the list, else the
  // lowest-numbered in the sandbox. Skip ones just deleted while the lists refetch.
  const live = (rows: ContractRow[] | undefined) => rows?.find((c) => !deleted.includes(c.id))
  const byNumber = [...(all.data?.results ?? [])].sort((a, b) => a.number - b.number)
  const openId = currentId ?? live(list.data?.results)?.id ?? live(byNumber)?.id ?? null
  const contract = useContract(openId)
  const reference = useReference()
  const remove = useDeleteContract()

  const open = (id: number) => {
    setCurrentId(id)
    setMode({ kind: 'view' })
  }
  const saved = (c: Contract) => open(c.id)
  const summary = list.data?.summary

  const surface = () => {
    if (!reference.data) return <p className="state">Loading…</p>
    if (mode.kind === 'insert')
      return (
        <ContractFormView
          key="insert"
          contract={null}
          reference={reference.data}
          onSaved={saved}
          onCancel={() => setMode({ kind: 'view' })}
        />
      )
    if (openId === null)
      return (
        <div className="ct-empty">
          <p>Pick a contract from the list, or look one up, to see it here.</p>
          <button type="button" className="btn2" onClick={() => setMode({ kind: 'insert' })}>
            Insert contract
          </button>
        </div>
      )
    if (contract.isError)
      return (
        <p className="state error">
          Couldn&apos;t load this contract.
          <button type="button" className="linkbtn" onClick={() => contract.refetch()}>
            Retry
          </button>
        </p>
      )
    if (!contract.data) return <p className="state">Loading…</p>
    if (mode.kind === 'edit')
      return (
        <ContractFormView
          key={`edit-${contract.data.id}`}
          contract={contract.data}
          reference={reference.data}
          onSaved={saved}
          onCancel={() => setMode({ kind: 'view' })}
        />
      )
    const c = contract.data
    return (
      <>
        <ContractView
          contract={c}
          reference={reference.data}
          deleting={remove.isPending}
          onInsert={() => setMode({ kind: 'insert' })}
          onEdit={() => setMode({ kind: 'edit' })}
          onDelete={() =>
            remove.mutate(c.id, {
              onSuccess: () => {
                setDeleted((d) => [...d, c.id])
                setCurrentId(nextByNumber(byNumber, c.number)?.id ?? null)
              },
            })
          }
          onOpenOnBoard={() => onOpenOnBoard(c.units[0]?.id ?? null, c.begin_date)}
          lookup={<ContractLookup onFound={open} />}
        />
        {remove.isError && <p className="state error">{errorMessages(remove.error).join(' ')}</p>}
      </>
    )
  }

  return (
    <>
      <div className="surface">
        <section aria-label="Toolbar" className="tbar">
          <DateRangeControl range={range} onChange={onRangeChange} />
          <span className="tsep" aria-hidden="true" />
          <MenuButton value={filter} options={FILTERS} onChange={setFilter} />
          <span className="tsep" aria-hidden="true" />
          <label htmlFor="ct-search" className="sr">
            Search contracts
          </label>
          <input
            id="ct-search"
            type="search"
            className="field ct-search"
            placeholder="Search contract, org, group, contact…"
            value={q}
            onChange={(e) => setQ(e.target.value)}
          />
        </section>
        {list.isError && !list.data ? (
          <p className="state error">
            Couldn&apos;t load contracts.
            <button type="button" className="linkbtn" onClick={() => list.refetch()}>
              Retry
            </button>
          </p>
        ) : list.data ? (
          <ContractTable data={list.data} currentId={openId} onOpen={open} />
        ) : (
          <p className="state">Loading contracts…</p>
        )}
        <div className="sbar booking-sbar" role="status">
          <span className="cnt">
            <b>{summary?.count ?? 0}</b> contracts
          </span>
          <span className="cnt">
            <b>{summary?.booked ?? 0}</b> booked
          </span>
          <span className="cnt">
            <b>{summary?.quotes ?? 0}</b> quotes
          </span>
          <span className="cnt">
            <b className="red">{summary?.cancelled ?? 0}</b> cancelled
          </span>
          <span className="cnt">
            <b className="red">{fmtMoney(summary?.balance_due ?? '0')}</b> balance due
          </span>
        </div>
      </div>
      <div className="surface ct-surface">{surface()}</div>
    </>
  )
}

/** After deleting `number`, open the next contract by number, or the previous if it was last. */
function nextByNumber(sorted: ContractRow[], number: number): ContractRow | undefined {
  const others = sorted.filter((c) => c.number !== number)
  return others.find((c) => c.number > number) ?? others[others.length - 1]
}
