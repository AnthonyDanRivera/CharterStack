import { errorMessages } from '../api/client'
import { useDemoLogin } from '../api/hooks'
import Logo from './Logo'
import './landing.css'

const SITE = 'https://anthonydanrivera.com'

const FEATURES: { title: string; text: string }[] = [
  {
    title: 'Booking',
    text: 'Book charter contracts: group, schedule, pickup and destination, buses and pricing. Balance due and payment status update as you type.',
  },
  {
    title: 'Dispatch board',
    text: 'One row per bus. Assign drivers, buses and report times, stamp Reported and On location, confirm with initials, and export the day to Excel.',
  },
  {
    title: 'Private sandbox',
    text: 'Every visitor gets their own copy of the sample data, dated today. Nobody sees anyone else’s changes, and it resets after 24 hours.',
  },
]

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

/** The page before login: what CharterStack is, how it's built, and who made it. */
export default function Landing() {
  const login = useDemoLogin()
  const start = () => login.mutate()
  const starting = login.isPending

  return (
    <div className="lp">
      <nav className="lp-nav" aria-label="Page">
        <div className="lp-nav-inner">
          <Logo />
          <div className="lp-nav-links">
            <a href="#stack">How it&rsquo;s built</a>
            <a href="#made-by">Made by</a>
            <button type="button" className="lp-btn lp-btn-sm" onClick={start} disabled={starting}>
              Try the demo
            </button>
          </div>
        </div>
      </nav>

      <header className="lp-hero">
        <h1>
          A <span className="lp-accent">TMS</span> for charter bus companies.
        </h1>
        <p className="lp-lead">
          Book a trip and it lands on the dispatch board, one row per bus. Assign drivers and buses,
          stamp report times, and export the day to Excel.
        </p>
        <div className="lp-actions">
          <button type="button" className="lp-btn" onClick={start} disabled={starting}>
            {starting ? 'Starting…' : 'Try the demo'}
          </button>
          <a className="lp-btn lp-btn-ghost" href="#stack">
            How it&rsquo;s built
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
      </header>

      <div className="lp-shot">
        <img src="/dispatch-board.jpg" alt="The dispatch board with today's trips" />
      </div>

      <section className="lp-section lp-section-first" aria-labelledby="features-title">
        <h2 id="features-title">What it does</h2>
        <div className="lp-grid lp-grid-3">
          {FEATURES.map((item) => (
            <div key={item.title} className="lp-card">
              <h3>{item.title}</h3>
              <p>{item.text}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="lp-section" id="stack" aria-labelledby="stack-title">
        <h2 id="stack-title">How it&rsquo;s built</h2>
        <div className="lp-grid">
          {STACK.map((item) => (
            <div key={item.title} className="lp-card">
              <h3>{item.title}</h3>
              <p>{item.text}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="lp-section" id="made-by" aria-labelledby="made-by-name">
        <p className="lp-eyebrow">Made by</p>
        <div className="lp-made">
          <span className="lp-avatar" aria-hidden="true">
            AR
          </span>
          <div>
            <h2 id="made-by-name">Anthony Rivera</h2>
            <p className="lp-made-tagline">Freelance web developer.</p>
            <p className="lp-made-text">
              Hi, I&rsquo;m Anthony. I&rsquo;m a freelance web developer who started as a dispatcher
              and now also works as a logistics planner in the charter bus business.
            </p>
            <a
              className="lp-btn lp-btn-ghost lp-btn-sm"
              href={SITE}
              target="_blank"
              rel="noopener noreferrer"
            >
              Visit my portfolio
            </a>
          </div>
        </div>
      </section>

      <footer className="lp-foot">
        <Logo size={18} />
        <span>Django REST Framework · React · TypeScript · PostgreSQL</span>
      </footer>
    </div>
  )
}
