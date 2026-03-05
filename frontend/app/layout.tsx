// 더미데이터
import type { Metadata } from 'next';
import '../styles/globals.css';

export const metadata: Metadata = {
  title: 'Chai-Na | 중국 시장 AI 분석 플랫폼',
  description: 'AI로 분석하는 중국 수출 전략 플랫폼 — 시장조사, 브랜딩, 왕홍 매칭',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ko">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
      </head>
      <body>{children}</body>
    </html>
  );
}
