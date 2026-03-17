/** 배포 도메인 접속 시 env 미설정이어도 백엔드 연결되도록 런타임 fallback (다른 페이지에서도 사용) */
export function getApiBase(): string {
  const envUrl = process.env.NEXT_PUBLIC_API_URL?.replace(/\/+$/, '');
  if (envUrl && !envUrl.includes('localhost')) return envUrl;
  if (typeof window !== 'undefined') {
    const host = window.location.hostname;
    if (host === 'markettinghowa-5.vercel.app' || host.endsWith('.vercel.app')) return 'https://markettinghowa-5.onrender.com';
  }
  return 'http://localhost:8000';
}

export class ApiError extends Error {
  status: number;
  payload: unknown;
  constructor(status: number, payload: unknown, message: string) {
    super(message);
    this.status = status;
    this.payload = payload;
  }
}

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const base = getApiBase();
  const res = await fetch(`${base}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });
  if (!res.ok) {
    const text = await res.text();
    let payload: any = null;
    try { payload = text ? JSON.parse(text) : null; } catch { payload = null; }
    const detail = payload?.detail ?? payload?.message ?? text;
    const msg =
      typeof detail === 'string'
        ? detail
        : (detail?.code ? `${detail.code}: ${detail.message ?? ''}` : `API error: ${res.status}`);
    throw new ApiError(res.status, payload, msg);
  }
  return res.json();
}

export const apiClient = {
  analysis: {
    run:       (payload: { keyword: string }) => request<any>('/api/v1/analysis/run', { method: 'POST', body: JSON.stringify(payload) }),
    start:     (payload: unknown) => request<{ job_id: string }>('/api/v1/analysis/start', { method: 'POST', body: JSON.stringify(payload) }),
    getReport: (jobId: string)    => request<any>(`/api/v1/analysis/report/${jobId}`),
  },
  branding: {
    generate: (payload: unknown) => request<any>('/api/v1/branding/generate', { method: 'POST', body: JSON.stringify(payload) }),
  },
  marketing: {
    createAsset: (payload: unknown) => request<any>('/api/v1/marketing/asset', { method: 'POST', body: JSON.stringify(payload) }),
  },
  wanghong: {
    crawl:    ()                 => request<any>('/api/v1/wanghong/crawl'),
    recommend: (payload: unknown) => request<any>('/api/v1/wanghong/recommend', { method: 'POST', body: JSON.stringify(payload) }),
    detail:   (id: string, name: string) => `${getApiBase()}/api/v1/wanghong/detail?anchor_id=${id}&name=${encodeURIComponent(name)}`,
    oneClick: (payload: { keyword: string; recommend_count?: number; use_previous?: boolean }) =>
      request<any>('/api/v1/wanghong/one-click', { method: 'POST', body: JSON.stringify(payload) }),
    detailJson: (id: string) =>
      request<any>(`/api/v1/wanghong/detail-json?anchor_id=${encodeURIComponent(id)}`),
    loginStart: () =>
      request<any>('/api/v1/wanghong/login', { method: 'POST' }),
    previousData: () =>
      request<any>('/api/v1/wanghong/previous-data'),
  },
};
