import { errorMessages } from '../api/client'
import { useDemoLogin } from '../api/hooks'
import Icon from './Icon'

export default function Landing() {
  const login = useDemoLogin()
  return (
    <div className="app">
      <header className="app-header">
        <Icon name="bus" size={20} />
        <h1>CharterStack</h1>
      </header>
      <main className="landing">
        <h2>CharterStack</h2>
        <p>
          A dispatch board and booking system for a motorcoach charter company. Sales books charter
          contracts; dispatch assigns drivers and buses, stamps report and on-location times, and
          confirms each trip.
        </p>
        <img src="/dispatch-board.jpg" alt="The dispatch board with today's trips" />
        <button
          type="button"
          className="btn"
          onClick={() => login.mutate()}
          disabled={login.isPending}
        >
          {login.isPending ? 'Starting…' : 'Try the demo'}
        </button>
        <p className="small">
          No sign-up. You get a private copy of the sample data that resets after 24 hours.
        </p>
        {login.isError && <p className="state error">{errorMessages(login.error).join(' ')}</p>}
      </main>
    </div>
  )
}
