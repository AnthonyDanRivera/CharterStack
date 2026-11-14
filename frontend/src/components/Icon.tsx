// CharterStack's few glyphs, drawn in the logo's style: solid shapes with
// rounded corners instead of stock line icons (docs/UI_GUIDE.md).
const PATHS = {
  // Filled carets with softened corners.
  left: <path d="M14.6 6.2a1 1 0 0 1 1.4.9v9.8a1 1 0 0 1-1.6.8l-6.1-4.9a1 1 0 0 1 0-1.6z" />,
  right: <path d="M9.4 6.2a1 1 0 0 0-1.4.9v9.8a1 1 0 0 0 1.6.8l6.1-4.9a1 1 0 0 0 0-1.6z" />,
  chevron: (
    <path d="M6.6 9h10.8a1 1 0 0 1 .8 1.6l-5.4 6.3a1 1 0 0 1-1.6 0l-5.4-6.3A1 1 0 0 1 6.6 9z" />
  ),
  // Three staggered bars, echoing the logo: "hold here to move".
  grip: (
    <>
      <rect x="5" y="6" width="14" height="3" rx="1.5" />
      <rect x="5" y="10.5" width="10" height="3" rx="1.5" />
      <rect x="5" y="15" width="12" height="3" rx="1.5" opacity="0.7" />
    </>
  ),
}

export type IconName = keyof typeof PATHS

export default function Icon({
  name,
  size,
  className,
}: {
  name: IconName
  size?: number
  className?: string
}) {
  return (
    <svg
      viewBox="0 0 24 24"
      width={size}
      height={size}
      className={className}
      fill="currentColor"
      aria-hidden="true"
    >
      {PATHS[name]}
    </svg>
  )
}
