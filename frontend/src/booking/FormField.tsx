import type { ReactNode } from 'react'

/** A form field: label (with a red asterisk when required) above the control. */
export default function Field({
  id,
  label,
  required,
  full,
  children,
}: {
  id?: string
  label: string
  required?: boolean
  full?: boolean
  children: ReactNode
}) {
  return (
    <div className={`fld${full ? ' full' : ''}`}>
      <label htmlFor={id}>
        {label}
        {required && <span className="req"> *</span>}
      </label>
      {children}
    </div>
  )
}
