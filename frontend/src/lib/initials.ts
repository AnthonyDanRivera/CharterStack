/** Instant-feedback copy of R22's normalization; the server stores the real value. */
export function normalizeInitials(text: string): string {
  return text
    .toUpperCase()
    .replace(/[^A-Z]/g, '')
    .slice(0, 4)
}
