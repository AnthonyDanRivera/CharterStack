import { errorMessages } from '../api/client'
import { useDemoLogin } from '../api/hooks'
import Icon, { type IconName } from './Icon'
import './landing.css'

const SITE = 'https://anthonydanrivera.com'

const FEATURES: { icon: IconName; title: string; text: string }[] = [
  {
    icon: 'plus',
    title: 'Booking',
    text: 'Sales books charter contracts: group, schedule, pickup and destination, buses and pricing. Balance due and payment status are worked out by the server.',
  },
  {
    icon: 'board',
    title: 'Dispatch board',
    text: 'One row per bus. Assign drivers, buses and report times, stamp Reported and On location, confirm with initials, and export the day to Excel.',
  },
  {
    icon: 'bus',
    title: 'Private sandbox',
    text: 'Every visitor gets their own copy of the sample data, dated today. Nobody sees anyone else’s changes, and it resets after 24 hours.',
  },
]

/** The page before login: what CharterStack is, who built it, and Try the demo. */
export default function Landing() {
  const login = useDemoLogin()
  const start = () => login.mutate()

  return (
    <div className="lp">
      <header className="lp-bar">
        <span className="lp-brand">
          <Icon name="bus" size={20} />
          CharterStack
        </span>
        <a className="lp-bar-link" href={SITE} target="_blank" rel="noopener noreferrer">
          Built by Anthony Rivera
        </a>
      </header>

      <section className="lp-hero">
        <div className="lp-hero-inner">
          <p className="lp-kicker">Motorcoach charter TMS</p>
          <h1>A dispatch board, built by a dispatcher.</h1>
          <p className="lp-lead">
            CharterStack is a booking and dispatch system for a charter bus company. Sales books the
            contracts; dispatch works each day’s trips: drivers, buses, report times and
            confirmations.
          </p>
          <div className="lp-actions">
            <button type="button" className="lp-cta" onClick={start} disabled={login.isPending}>
              {login.isPending ? 'Starting…' : 'Try the demo'}
            </button>
            <a className="lp-ghost" href={SITE} target="_blank" rel="noopener noreferrer">
              About me
            </a>
          </div>
          <p className="lp-note">
            No sign-up. You get a private copy of the sample data that resets after 24 hours.
          </p>
          {login.isError && (
            <p className="lp-error" role="alert">
              {errorMessages(login.error).join(' ')}
            </p>
          )}
        </div>
      </section>

      <div className="lp-shot">
        <div className="lp-frame">
          <div className="lp-frame-bar" aria-hidden="true">
            <span />
            <span />
            <span />
          </div>
          <img src="/dispatch-board.jpg" alt="The dispatch board with today's trips" />
        </div>
      </div>

      <section className="lp-features" aria-label="What it does">
        {FEATURES.map((f) => (
          <div key={f.title} className="lp-feature">
            <span className="lp-icon">
              <Icon name={f.icon} size={18} />
            </span>
            <h2>{f.title}</h2>
            <p>{f.text}</p>
          </div>
        ))}
      </section>

      <section className="lp-about" aria-label="About the builder">
        <div className="lp-about-inner">
          <h2>Built by Anthony Rivera</h2>
          <p>
            I worked as a dispatcher and operations planner in the motorcoach charter business.
            Every day ran on a dispatch board: which trips go out, who is driving, which bus, when
            the driver reports, whether the trip is confirmed. CharterStack is my version of that
            tool, built to show how I turn real operations into software.
          </p>
          <div className="lp-actions">
            <a className="lp-link-btn" href={SITE} target="_blank" rel="noopener noreferrer">
              Visit anthonydanrivera.com
            </a>
            <button
              type="button"
              className="lp-text-btn"
              onClick={start}
              disabled={login.isPending}
            >
              Or try the demo
            </button>
          </div>
        </div>
      </section>

      <footer className="lp-foot">
        <span>Django REST Framework · React · TypeScript · PostgreSQL</span>
        <a href={SITE} target="_blank" rel="noopener noreferrer">
          anthonydanrivera.com
        </a>
      </footer>
    </div>
  )
}
