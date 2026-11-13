import { useState } from 'react'
import { lookupContract } from '../api/hooks'

/** "Contract lookup" box (R31): digits, D and -; Enter looks the number up. */
export default function ContractLookup({ onFound }: { onFound: (id: number) => void }) {
  const [text, setText] = useState('')
  const [notFound, setNotFound] = useState<string | null>(null)

  const search = async () => {
    const typed = text.trim()
    if (!typed) return
    const id = await lookupContract(typed).catch(() => null)
    if (id === null) setNotFound(typed)
    else {
      setNotFound(null)
      setText('')
      onFound(id)
    }
  }

  return (
    <div className="tgroup lookup">
      <label htmlFor="f-lookup">Contract lookup</label>
      <input
        id="f-lookup"
        type="text"
        maxLength={10}
        className="field"
        placeholder="e.g. 24817"
        value={text}
        onChange={(e) => {
          setText(e.target.value.toUpperCase().replace(/[^0-9D-]/g, ''))
          setNotFound(null)
        }}
        onKeyDown={(e) => {
          if (e.key === 'Enter') search()
        }}
        onBlur={() => text.trim().length >= 5 && search()}
      />
      {notFound && <span className="notfound">No contract {notFound} found.</span>}
    </div>
  )
}
