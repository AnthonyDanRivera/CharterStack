// Line icons copied from the prototype's inline SVGs.
const PATHS = {
  left: <path d="M15 6l-6 6 6 6" />,
  right: <path d="M9 6l6 6-6 6" />,
  chevron: <path d="M6 9l6 6 6-6" />,
  close: (
    <>
      <path d="M6 6l12 12" />
      <path d="M18 6L6 18" />
    </>
  ),
  grip: (
    <>
      <circle cx="9" cy="7" r="1.4" />
      <circle cx="15" cy="7" r="1.4" />
      <circle cx="9" cy="12" r="1.4" />
      <circle cx="15" cy="12" r="1.4" />
      <circle cx="9" cy="17" r="1.4" />
      <circle cx="15" cy="17" r="1.4" />
    </>
  ),
}

export type IconName = keyof typeof PATHS

export default function Icon({
  name,
  size,
  className,
  strokeWidth = 1.8,
}: {
  name: IconName
  size?: number
  className?: string
  strokeWidth?: number
}) {
  const filled = name === 'grip'
  return (
    <svg
      viewBox="0 0 24 24"
      width={size}
      height={size}
      className={className}
      fill={filled ? 'currentColor' : 'none'}
      stroke={filled ? 'none' : 'currentColor'}
      strokeWidth={strokeWidth}
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      {PATHS[name]}
    </svg>
  )
}
