import type { ReactNode } from 'react'

/** A small grey label above a light grey read-only box. */
export default function ReadOnlyField({
  label,
  children,
  full,
  mono,
  pre,
}: {
  label: string
  children: ReactNode
  full?: boolean
  mono?: boolean
  pre?: boolean
}) {
  return (
    <div className={`fld${full ? ' full' : ''}`}>
      <span className="rl">{label}</span>
      <div className={`ro${mono ? ' mono' : ''}${pre ? ' pre' : ''}`}>{children}</div>
    </div>
  )
}
