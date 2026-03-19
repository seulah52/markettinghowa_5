/**
 * NEXT_PUBLIC_API_URL이 없을 때 프로덕션에서 사용할 Render 백엔드 기본 주소
 * (Vercel 환경 변수 누락 시에도 배포 사이트가 백엔드에 연결되도록 함)
 */
export const DEFAULT_PRODUCTION_API_URL = 'https://markettinghowa-5.onrender.com';

/** API 베이스 URL: NEXT_PUBLIC_API_URL (next.config에서 API_URL도 여기로 합침), 없으면 production→Render */
export function getApiBase(): string {
  const fromEnv = process.env.NEXT_PUBLIC_API_URL?.trim().replace(/\/+$/, '') || '';
  if (fromEnv) return fromEnv;
  if (process.env.NODE_ENV === 'production') return DEFAULT_PRODUCTION_API_URL;
  return 'http://localhost:8000';
}
