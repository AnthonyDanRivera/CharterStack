import type { SessionInfo } from '../api/types'
import { fmtDuration, fmtStripDate, fmtStripTime } from '../lib/dates'
import { useNow } from '../lib/useNow'

/** Bottom strip: live local date and time, demo user, terminal filter, session. */
export default function SessionStrip({
  session,
  terminalLabel,
}: {
  session: SessionInfo
  terminalLabel: string
}) {
  const now = useNow()
  const started = new Date(session.started_at).getTime()
  const items: [string, string][] = [
    ['Date', fmtStripDate(now)],
    ['Time', fmtStripTime(now)],
    ['User', session.user],
    ['Terminal', terminalLabel],
    ['Session', session.session_id],
    ['Session time', fmtDuration(now.getTime() - started)],
    ['Server', session.server],
  ]
  return (
    <footer className="sfoot" aria-label="Session information">
      {items.map(([label, value]) => (
        <span key={label}>
          <span className="sk">{label}</span> {value}
        </span>
      ))}
    </footer>
  )
}
