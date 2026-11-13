import { useQuery } from '@tanstack/react-query'

type Health = { status: string }

async function fetchHealth(): Promise<Health> {
  const response = await fetch('/api/health/')
  if (!response.ok) throw new Error(`HTTP ${response.status}`)
  return response.json() as Promise<Health>
}

// Phase 0 placeholder. Replaced by the real app shell in Phase 5.
export default function App() {
  const health = useQuery({ queryKey: ['health'], queryFn: fetchHealth })

  let apiText = 'checking...'
  if (health.isError) apiText = 'unreachable'
  else if (health.data) apiText = health.data.status

  return (
    <main>
      <h1>CharterStack</h1>
      <p>API: {apiText}</p>
    </main>
  )
}
