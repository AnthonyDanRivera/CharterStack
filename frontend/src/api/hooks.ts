import {
  keepPreviousData,
  useMutation,
  useQuery,
  useQueryClient,
  type QueryClient,
} from '@tanstack/react-query'
import { api, ApiError, type Query } from './client'
import type {
  Board,
  Contract,
  ContractFilter,
  ContractList,
  Pricing,
  Reference,
  SessionInfo,
  SortDir,
  TripView,
  UnitDetail,
  UnitPatch,
  ZipInfo,
} from './types'

// --- Session ---------------------------------------------------------------

/** The current demo session, or null when not logged in (401). */
export function useSession() {
  return useQuery({
    queryKey: ['session'],
    queryFn: async () => {
      try {
        return await api<SessionInfo>('/api/session/')
      } catch (error) {
        if (error instanceof ApiError && (error.status === 401 || error.status === 403)) return null
        throw error
      }
    },
    staleTime: Infinity,
  })
}

export function useDemoLogin() {
  const client = useQueryClient()
  return useMutation({
    mutationFn: async () => {
      // Make sure the CSRF cookie exists before the first POST.
      await api('/api/session/').catch(() => undefined)
      return api<SessionInfo>('/api/demo-login/', { method: 'POST' })
    },
    onSuccess: (session) => client.setQueryData(['session'], session),
  })
}

// --- Reference -------------------------------------------------------------

export function useReference() {
  return useQuery({
    queryKey: ['reference'],
    queryFn: () => api<Reference>('/api/reference/'),
    staleTime: Infinity,
  })
}

export function fetchZip(zip: string): Promise<ZipInfo | null> {
  return api<ZipInfo>(`/api/zip/${encodeURIComponent(zip)}/`).catch((error) => {
    if (error instanceof ApiError && error.status === 404) return null
    throw error
  })
}

// --- Board -----------------------------------------------------------------

export type BoardParams = {
  start: string
  end: string
  view: TripView
  terminals: string[] | null
  q: string
  sort: string | null
  dir: SortDir
}

export function boardQuery(p: BoardParams): Query {
  return {
    start: p.start,
    end: p.end,
    view: p.view,
    terminals: p.terminals === null ? undefined : p.terminals.join(','),
    q: p.q || undefined,
    sort: p.sort ?? undefined,
    dir: p.sort ? p.dir : undefined,
  }
}

export function useBoard(params: BoardParams) {
  return useQuery({
    queryKey: ['board', params],
    queryFn: () => api<Board>('/api/board/', { query: boardQuery(params) }),
    placeholderData: keepPreviousData,
  })
}

export function useUnit(id: number | null) {
  return useQuery({
    queryKey: ['unit', id],
    queryFn: () => api<UnitDetail>(`/api/units/${id}/`),
    enabled: id !== null,
  })
}

export function invalidateTrips(client: QueryClient) {
  client.invalidateQueries({ queryKey: ['board'] })
  client.invalidateQueries({ queryKey: ['unit'] })
  client.invalidateQueries({ queryKey: ['contracts'] })
  client.invalidateQueries({ queryKey: ['contract'] })
}

export function usePatchUnit() {
  const client = useQueryClient()
  return useMutation({
    mutationFn: ({ id, patch }: { id: number; patch: UnitPatch }) =>
      api<UnitDetail>(`/api/units/${id}/`, { method: 'PATCH', body: patch }),
    onSuccess: (unit) => {
      client.setQueryData(['unit', unit.id], unit)
      invalidateTrips(client)
    },
  })
}

export type UnitAction = 'reported' | 'on-location' | 'cancel' | 'duplicate'

export function useUnitAction() {
  const client = useQueryClient()
  return useMutation({
    mutationFn: ({ id, action, body }: { id: number; action: UnitAction; body?: unknown }) =>
      api<UnitDetail>(`/api/units/${id}/${action}/`, { method: 'POST', body: body ?? {} }),
    onSuccess: (unit) => {
      client.setQueryData(['unit', unit.id], unit)
      invalidateTrips(client)
    },
  })
}

export function useDeleteUnit() {
  const client = useQueryClient()
  return useMutation({
    mutationFn: (id: number) => api<void>(`/api/units/${id}/`, { method: 'DELETE' }),
    onSuccess: () => invalidateTrips(client),
  })
}

export function fetchBusWarnings(unitId: number, busId: number | null): Promise<string[]> {
  return api<{ warnings: string[] }>(`/api/units/${unitId}/check/`, {
    query: { bus: busId ?? undefined },
  }).then((r) => r.warnings)
}

// --- Contracts -------------------------------------------------------------

export type ContractParams = { start: string; end: string; status: ContractFilter; q: string }

export function useContracts(p: ContractParams) {
  return useQuery({
    queryKey: ['contracts', p],
    queryFn: () =>
      api<ContractList>('/api/contracts/', {
        query: { start: p.start, end: p.end, status: p.status, q: p.q || undefined },
      }),
    placeholderData: keepPreviousData,
  })
}

/** Every contract in the sandbox (no date or status filter), for keeping one open. */
export function useAllContracts() {
  return useQuery({
    queryKey: ['contracts', 'all'],
    queryFn: () => api<ContractList>('/api/contracts/'),
  })
}

export function useContract(id: number | null) {
  return useQuery({
    queryKey: ['contract', id],
    queryFn: () => api<Contract>(`/api/contracts/${id}/`),
    enabled: id !== null,
  })
}

export function useNextNumber(enabled: boolean) {
  return useQuery({
    queryKey: ['next-number'],
    queryFn: () => api<{ number: number }>('/api/contracts/next-number/'),
    enabled,
  })
}

export function lookupContract(number: string): Promise<number | null> {
  return api<{ id: number }>('/api/contracts/lookup/', { query: { number } })
    .then((r) => r.id)
    .catch((error) => {
      if (error instanceof ApiError && error.status === 404) return null
      throw error
    })
}

export function fetchPricing(values: {
  total_price: string
  deposit_required: string
  total_paid: string
  status: string
}): Promise<Pricing> {
  return api<Pricing>('/api/contracts/pricing/', { query: values })
}

export function useSaveContract() {
  const client = useQueryClient()
  return useMutation({
    mutationFn: ({ id, body }: { id: number | null; body: Record<string, unknown> }) =>
      id === null
        ? api<Contract>('/api/contracts/', { method: 'POST', body })
        : api<Contract>(`/api/contracts/${id}/`, { method: 'PATCH', body }),
    onSuccess: (contract) => {
      client.setQueryData(['contract', contract.id], contract)
      client.invalidateQueries({ queryKey: ['next-number'] })
      invalidateTrips(client)
    },
  })
}

export function useDeleteContract() {
  const client = useQueryClient()
  return useMutation({
    mutationFn: (id: number) => api<void>(`/api/contracts/${id}/`, { method: 'DELETE' }),
    onSuccess: () => {
      client.invalidateQueries({ queryKey: ['next-number'] })
      invalidateTrips(client)
    },
  })
}
