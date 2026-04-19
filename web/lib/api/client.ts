import { enqueueOperation } from "@/lib/offline/queue";
import { getAuthHeaders, refreshAccessToken } from "@/lib/api/session-headers";

const BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export { getAuthHeaders } from "@/lib/api/session-headers";

function inferQueryKeysForPath(path: string): string[][] {
  try {
    const u = new URL(path, BASE_URL);
    const p = u.pathname;
    const m = p.match(/^\/api\/v1\/lists\/([^/]+)\/items(?:\/([^/]+))?$/);
    if (m) {
      return [["items", m[1]], ["lists"]];
    }
  } catch {
    /* ignore */
  }
  return [];
}

async function request<T>(
  method: string,
  path: string,
  body?: unknown,
  retry = true
): Promise<T> {
  const headers = await getAuthHeaders();

  let response: Response;
  try {
    response = await fetch(`${BASE_URL}${path}`, {
      method,
      headers,
      body: body !== undefined ? JSON.stringify(body) : undefined,
    });
  } catch {
    await enqueueOperation({
      method: method as "POST" | "PATCH" | "DELETE",
      url: `${BASE_URL}${path}`,
      body,
      queryKeys: inferQueryKeysForPath(path),
    });
    throw new Error("Network error — operation queued");
  }

  if (response.status === 401 && retry) {
    const refreshed = await refreshAccessToken();
    if (refreshed) {
      return request<T>(method, path, body, false);
    }
  }

  if (!response.ok) {
    const detail = await response.text().catch(() => "Unknown error");
    throw new Error(`HTTP ${response.status}: ${detail}`);
  }

  if (response.status === 204) return undefined as T;
  return response.json() as Promise<T>;
}

export const get = <T>(path: string) => request<T>("GET", path);
export const post = <T>(path: string, body?: unknown) => request<T>("POST", path, body);
export const patch = <T>(path: string, body?: unknown) => request<T>("PATCH", path, body);
export const del = <T>(path: string) => request<T>("DELETE", path);
