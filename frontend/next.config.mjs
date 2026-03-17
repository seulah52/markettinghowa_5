// 더미데이터
/** @type {import('next').NextConfig} */
const nextConfig = {
  async rewrites() {
    const base = process.env.NEXT_PUBLIC_API_URL?.replace(/\/+$/, '') || 'http://localhost:8000';
    return [{ source: '/api/:path*', destination: `${base}/api/:path*` }];
  },
  images: {
    remotePatterns: [
      { protocol: 'https', hostname: 'images.unsplash.com' },
    ],
  },
};

export default nextConfig;
