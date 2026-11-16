import { useState } from 'react'
import { useSession } from './api/hooks'
import AppFrame from './components/AppFrame'
import Landing from './components/Landing'
import './styles/tokens.css'
import './styles/app.css'

/** Landing page without a session; the app with one, unless the visitor clicked the logo to go home. */
export default function App() {
  const session = useSession()
  const [home, setHome] = useState(false)
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
  if (session.data && !home)
    return (
      <AppFrame
        session={session.data}
        onHome={() => {
          setHome(true)
          window.scrollTo(0, 0)
        }}
      />
    )
  return <Landing hasSession={!!session.data} onResume={() => setHome(false)} />
}
