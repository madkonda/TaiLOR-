// Default to Vercel proxy path to avoid mixed-content issues from HTTPS → HTTP
export const API_BASE = (process.env.NEXT_PUBLIC_API_BASE || '/api').replace(/\/$/, '');

export function absoluteBackendUrl(path: string) {
  if (!API_BASE) return path;
  if (path.startsWith('http')) return path;
  return `${API_BASE}${path.startsWith('/') ? path : `/${path}`}`;
}


