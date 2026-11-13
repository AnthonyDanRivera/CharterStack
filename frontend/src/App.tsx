import { useSession } from './api/hooks'
import AppFrame from './components/AppFrame'
import Landing from './components/Landing'
import './styles/tokens.css'
import './styles/app.css'

/** Landing page without a session; the app with one. */
export default function App() {
  const session = useSession()
  if (session.isPending) return <p className="state">Loading…</p>
  if (session.isError)
    return (
      <p className="state error">
        Couldn&apos;t reach the server.
        <button type="button" className="linkbtn" onClick={() => session.refetch()}>
          Retry
        </button>
      </p>
    )
  return session.data ? <AppFrame session={session.data} /> : <Landing />
}
