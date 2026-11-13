import { keepPreviousData, useQuery } from '@tanstack/react-query'
import { fetchPricing } from '../api/hooks'
import { fmtMoney } from '../lib/dates'
import { useDebounced } from '../lib/useDebounced'

/**
 * Balance due and Payment status for the unsaved form values. The server
 * computes them (R11, R12) so the form and the saved contract always agree.
 */
export default function LivePricing(props: {
  status: string
  total_price: string
  deposit_required: string
  total_paid: string
}) {
  const values = useDebounced(props, 300)
  const pricing = useQuery({
    queryKey: ['pricing', values],
    queryFn: () => fetchPricing(values),
    placeholderData: keepPreviousData,
    retry: false,
  })
  const data = pricing.isError ? null : pricing.data
  return (
    <>
      <div className="fld">
        <span className="rl">Balance due</span>
        <div className="ro">{data ? fmtMoney(data.balance_due) : '—'}</div>
      </div>
      <div className="fld">
        <span className="rl">Payment status</span>
        <div className="ro">
          {data ? (
            <span className="pay" data-tone={data.payment_tone}>
              {data.payment_status}
            </span>
          ) : (
            '—'
          )}
        </div>
      </div>
    </>
  )
}
