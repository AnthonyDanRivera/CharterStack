import { errorMessages } from '../api/client'
import { useDemoLogin } from '../api/hooks'
import Logo from './Logo'
import './landing.css'

const SITE = 'https://anthonydanrivera.com'

const STACK: { title: string; text: string }[] = [
  {
    title: 'Django REST Framework',
    text: 'The API owns every business rule: payment status, balance due, unit numbers, day labels, counts and capacity warnings. One base viewset scopes every query to the visitor, so another sandbox’s IDs return 404.',
  },
  {
    title: 'React and TypeScript',
    text: 'Built with Vite and TanStack Query, no UI library. The board has sortable, resizable and draggable columns saved per browser, and the form takes loose times like 730 or 7p.',
  },
  {
    title: 'PostgreSQL',
    text: 'A contract has one trip unit per bus, so a two-bus job is two rows on the board. Each demo copies the sample data with its dates moved to today, and a daily job deletes it after 24 hours.',
  },
  {
    title: 'Tests and CI',
    text: 'Every business rule has a pytest test named after its rule ID, plus tests that try each endpoint against another visitor’s data. GitHub Actions runs lint, tests and a Docker build on every push.',
  },
  {
    title: 'Deployment',
    text: 'One Docker image. Django serves the built React app through WhiteNoise behind gunicorn, so the site and API share an origin. Excel export is generated server-side with openpyxl.',
  },
]

/** The page before login: what CharterStack is, how it's built, and Try the demo. */
export default function Landing() {
  const login = useDemoLogin()

  return (
    <div className="lp">
      <header className="lp-bar">
        <Logo />
      </header>

      <section className="lp-hero">
        <div className="lp-hero-inner">
          <h1>Booking and dispatch for a charter bus company.</h1>
          <p className="lp-lead">
            Book a trip and it shows up on the dispatch board, one row per bus. Assign drivers and
            buses, stamp report and on-location times, and export the day to Excel.
          </p>
          <button
            type="button"
            className="lp-cta"
            onClick={() => login.mutate()}
            disabled={login.isPending}
          >
            {login.isPending ? 'Starting…' : 'Try the demo'}
          </button>
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
        <img src="/dispatch-board.jpg" alt="The dispatch board with today's trips" />
      </div>

      <section className="lp-stack" aria-labelledby="lp-stack-title">
        <h2 id="lp-stack-title">How it&rsquo;s built</h2>
        <div className="lp-grid">
          {STACK.map((item) => (
            <div key={item.title} className="lp-item">
              <h3>{item.title}</h3>
              <p>{item.text}</p>
            </div>
          ))}
        </div>
      </section>

      <footer className="lp-foot">
        <span>Built by Anthony Rivera, a former charter dispatcher.</span>
        <a href={SITE} target="_blank" rel="noopener noreferrer">
          anthonydanrivera.com
        </a>
      </footer>
    </div>
  )
}
