/**
 * Thin fetch wrapper for the Django API.
 *
 * - Session cookie auth: the browser sends the cookie; we add the CSRF token
 *   (read from the `csrftoken` cookie Django sets) on every unsafe request.
 * - `X-Timezone` tells the server which local date/time to use for "today"
 *   and for the Reported / On location stamps.
 */

export class ApiError extends Error {
  status: number
  body: unknown

  constructor(status: number, body: unknown) {
    super(`HTTP ${status}`)
    this.status = status
    this.body = body
  }
}

export function visitorTimeZone(): string {
  try {
    return Intl.DateTimeFormat().resolvedOptions().timeZone || 'America/New_York'
  } catch {
    return 'America/New_York'
  }
}

function csrfToken(): string {
  const match = document.cookie.match(/(?:^|;\s*)csrftoken=([^;]+)/)
  return match ? decodeURIComponent(match[1]) : ''
}

export type Query = Record<string, string | number | null | undefined>

export function buildUrl(path: string, query?: Query): string {
  const params = new URLSearchParams()
  for (const [key, value] of Object.entries(query ?? {})) {
    if (value !== undefined && value !== null) params.set(key, String(value))
  }
  const qs = params.toString()
  return qs ? `${path}?${qs}` : path
}

export async function api<T>(
  path: string,
  options: { method?: string; body?: unknown; query?: Query } = {},
): Promise<T> {
  const method = options.method ?? 'GET'
  const headers: Record<string, string> = {
    Accept: 'application/json',
    'X-Timezone': visitorTimeZone(),
  }
  if (method !== 'GET') headers['X-CSRFToken'] = csrfToken()
  if (options.body !== undefined) headers['Content-Type'] = 'application/json'

  const response = await fetch(buildUrl(path, options.query), {
    method,
    headers,
    credentials: 'same-origin',
    body: options.body === undefined ? undefined : JSON.stringify(options.body),
  })
  if (response.status === 204) return undefined as T
  const text = await response.text()
  let data: unknown = null
  if (text) {
    try {
      data = JSON.parse(text)
    } catch {
      data = text
    }
  }
  if (!response.ok) throw new ApiError(response.status, data)
  return data as T
}

/**
 * Flatten a DRF validation error body into a list of messages, keeping the
 * server's wording (nested location errors included). Duplicates are dropped.
 */
export function errorMessages(error: unknown): string[] {
  if (!(error instanceof ApiError)) return ['Something went wrong. Try again.']
  const out: string[] = []
  const walk = (value: unknown) => {
    if (typeof value === 'string') out.push(value)
    else if (Array.isArray(value)) value.forEach(walk)
    else if (value && typeof value === 'object') Object.values(value).forEach(walk)
  }
  walk(error.body)
  if (out.length === 0) out.push(`Request failed (${error.status}).`)
  return [...new Set(out)]
}
