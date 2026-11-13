import type { ReactNode } from 'react'

/** A small grey title above a light grey box. */
export default function Box({ title, children }: { title: string; children: ReactNode }) {
  return (
    <div className="ibox-wrap">
      <div className="ibox-title">{title}</div>
      <div className="ibox">{children}</div>
    </div>
  )
}
