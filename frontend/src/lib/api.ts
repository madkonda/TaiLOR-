// Local-only: default to backend on localhost:8090
export const API_BASE = (process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8090').replace(/\/$/, '');

export function absoluteBackendUrl(path: string) {
  if (!API_BASE) return path;
  if (path.startsWith('http')) return path;
  return `${API_BASE}${path.startsWith('/') ? path : `/${path}`}`;
}


