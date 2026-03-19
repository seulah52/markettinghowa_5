// NEXT_PUBLIC_API_URL 없을 때 프로덕션은 Render로 폴백 (client.ts의 baseUrl.ts와 동일)
const DEFAULT_PRODUCTION_API_URL = 'https://markettinghowa-5.onrender.com';

/** Vercel에 SUPABASE_URL / SUPABASE_KEY 만 넣은 경우 클라이언트 번들에 전달 */
const publicSupabaseUrl =
  process.env.NEXT_PUBLIC_SUPABASE_URL || process.env.SUPABASE_URL || '';
const publicSupabaseAnonKey =
  process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || process.env.SUPABASE_KEY || '';
const publicApiUrl =
  (process.env.NEXT_PUBLIC_API_URL || process.env.API_URL || '').trim();

/** @type {import('next').NextConfig} */
const nextConfig = {
  env: {
    NEXT_PUBLIC_SUPABASE_URL: publicSupabaseUrl,
    NEXT_PUBLIC_SUPABASE_ANON_KEY: publicSupabaseAnonKey,
    NEXT_PUBLIC_API_URL: publicApiUrl,
  },
  async rewrites() {
    const raw = publicApiUrl || undefined;
    const base = raw
      ? raw.replace(/\/+$/, '')
      : process.env.NODE_ENV === 'production'
        ? DEFAULT_PRODUCTION_API_URL
        : 'http://localhost:8000';
    return [{ source: '/api/:path*', destination: `${base}/api/:path*` }];
  },
  images: {
    remotePatterns: [
      { protocol: 'https', hostname: 'images.unsplash.com' },
    ],
  },
};

export default nextConfig;
