// Thin wrapper over the SlideKick Python API (src/slidekick/api_server.py),
// reached through the Vite /api proxy.

export type ApiResult<T> = { ok: boolean; status: number; body: T }

/** Rejects only when SlideKick can't be reached. */
export async function api<T>(path: string, method = 'GET', body?: unknown): Promise<ApiResult<T>> {
  const res = await fetch(`/api${path}`, {
    method,
    // The server requires JSON on every write; that also blocks cross-site requests.
    headers: method === 'GET' ? undefined : { 'Content-Type': 'application/json' },
    body: method === 'GET' ? undefined : JSON.stringify(body ?? {}),
  })
  return { ok: res.ok, status: res.status, body: (await res.json()) as T }
}
