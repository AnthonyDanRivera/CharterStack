import { useState } from 'react'

/** R10: "Delete contract" → "Confirm delete?" → "Yes, permanently delete 24817". */
export default function DeleteContractButton({
  number,
  onDelete,
  disabled,
}: {
  number: number
  onDelete: () => void
  disabled?: boolean
}) {
  const [step, setStep] = useState(0)
  const labels = ['Delete contract', 'Confirm delete?', `Yes, permanently delete ${number}`]
  return (
    <button
      type="button"
      className="btn2"
      data-armed={step > 0 ? String(step) : undefined}
      disabled={disabled}
      onClick={() => {
        if (step < 2) setStep(step + 1)
        else {
          setStep(0)
          onDelete()
        }
      }}
      onBlur={() => setStep(0)}
    >
      {labels[step]}
    </button>
  )
}
