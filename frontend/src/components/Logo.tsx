/**
 * CharterStack logo: a blue rounded square with three staggered bars, like
 * rows on a dispatch board (and a stack). Same mark as public/favicon.svg.
 */
export default function Logo({
  size = 22,
  wordmark = true,
}: {
  size?: number
  wordmark?: boolean
}) {
  return (
    <span className="logo">
      <svg width={size} height={size} viewBox="0 0 32 32" aria-hidden="true">
        <rect width="32" height="32" rx="7" fill="#2F6BC0" />
        <rect x="7" y="8" width="18" height="4" rx="2" fill="#fff" />
        <rect x="7" y="14" width="13" height="4" rx="2" fill="#fff" />
        <rect x="7" y="20" width="16" height="4" rx="2" fill="#fff" opacity="0.7" />
      </svg>
      {wordmark && <span className="logo-word">CharterStack</span>}
    </span>
  )
}
