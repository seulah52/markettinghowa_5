'use client';
import { useRef, useEffect, useState } from 'react';
import Link from 'next/link';

const SERVICES = [
  {
    num: '01',
    tag: 'Market Research',
    title: '중국 시장 분석',
    desc: '댓글 감성 분석부터 검색 트랜드, 판매 순위까지. 실시간 데이터로 정확한 시장을 읽다',
    href: '/analysis',
    icon: (
      <svg className="w-8" fill="none" viewBox="0 0 32 32">
        <circle cx="16" cy="16" r="12" stroke="currentColor" strokeWidth="1" />
        <path d="M8 20 L13 14 L18 17 L24 10" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
        <circle cx="24" cy="10" r="2" fill="currentColor" />
      </svg>
    ),
    platforms: ['최신 트렌드', '수출동향', '경쟁사', '마케팅 분석'],
  },
  {
    num: '02',
    tag: 'Brand Story',
    title: '브랜드 스토리',
    desc: '중국 진출을 위한 기존 브랜드 리브랜딩 / 새로운 브랜드 스토리 제작',
    href: '/branding',
    icon: (
      <svg className="w-8 h-8" fill="none" viewBox="0 0 32 32">
        <path d="M6 26 C6 26 8 10 16 6 C24 2 28 14 24 20 C20 26 10 24 6 26Z" stroke="currentColor" strokeWidth="1" />
        <path d="M12 18 C14 14 18 12 20 14" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
      </svg>
    ),
    platforms: ['맞춤 리브랜딩', '신규 브랜딩'],
  },
  {
    num: '03',
    tag: 'Marketing',
    title: '홍보물 제작',
    desc: '플랫폼별 특성을 반영한 홍보 이미지 / 마케팅 문구 / 영상 스크립트 생성',
    href: '/marketing',
    icon: (
      <svg className="w-8 h-8" fill="none" viewBox="0 0 32 32">
        <rect x="4" y="8" width="24" height="16" rx="1" stroke="currentColor" strokeWidth="1" />
        <path d="M10 14 h12 M10 18 h8" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
        <path d="M4 12 h24" stroke="currentColor" strokeWidth="1" strokeDasharray="2 2" />
      </svg>
    ),
    platforms: ['홍보 문구', '이미지', '영상 스크립트'],
  },
  {
    num: '04',
    tag: 'Influencer',
    title: '왕홍 매칭',
    desc: '타겟 맞춤형 왕홍 리스트 자동 추출, 맞춤형 광고 제안서 자동 작성',
    href: '/wanghong',
    icon: (
      <svg className="w-8 h-8" fill="none" viewBox="0 0 32 32">
        <circle cx="12" cy="10" r="4" stroke="currentColor" strokeWidth="1" />
        <circle cx="22" cy="12" r="3" stroke="currentColor" strokeWidth="1" />
        <path d="M4 26 C4 20 8 18 12 18 C14 18 16 18.8 17.5 20" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
        <path d="M18 26 C18 22 20 20 22 20 C24 20 26 22 26 26" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
        <circle cx="22" cy="12" r="1" fill="currentColor" />
      </svg>
    ),
    platforms: ['왕홍 리스트', '광고 제안서'],
  },
];

function useIntersect(threshold = 0.2) {
  const ref = useRef<HTMLDivElement>(null);
  const [visible, setVisible] = useState(false);
  useEffect(() => {
    const obs = new IntersectionObserver(([e]) => { if (e.isIntersecting) setVisible(true); }, { threshold });
    if (ref.current) obs.observe(ref.current);
    return () => obs.disconnect();
  }, [threshold]);
  return { ref, visible };
}

export default function ServicesSection() {
  const { ref, visible } = useIntersect(0.1);

  return (
    <section id="how" ref={ref} className="relative h-screen w-full flex items-center overflow-hidden" style={{ background: 'var(--ink)' }}>
      {/* 배경 장식 최적화 */}
      <div className="absolute top-0 right-0 w-[300px] h-[300px] pointer-events-none opacity-50" style={{ background: 'radial-gradient(ellipse, rgba(196,147,109,0.12) 0%, transparent 70%)' }} />

      <div className="max-w-7xl mx-auto px-6 w-full flex flex-col justify-center h-full py-4">
        
        {/* 1. 헤더 영역: 마진을 vh 단위로 조절하여 높이 확보 */}
        <div className={`mb-[1vh] ${visible ? 'opacity-0 animate-fadeUp' : 'opacity-0'}`}>
          <p className="section-tag mb-10 font-bold text-orange-deep text-xs">Our Services</p>
          <h2 className="section-heading text-[clamp(24px,4.5vh,48px)] text-parchment mb-2 font-medium leading-tight">
            하나의 플랫폼으로<br />
            <span className="text-gold-gradient font-semibold">중국 수출 전략</span> 완성
          </h2>
          <div className="deco-line w-16 mt-2 bg-gold/40" />
        </div>

        {/* 2. 카드 그리드: gap을 줄이고(8 -> 4) 카드 높이가 유동적으로 변하게 설정 */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-2 lg:gap-4 w-full">
          {SERVICES.map((svc, i) => (
            <Link
              key={svc.num}
              href={svc.href}
              className={`glass-card group relative p-6 md:p-8 block transition-all duration-500 hover:shadow-xl ${visible ? `opacity-0 animate-fadeUp delay-${(i + 1) * 100}` : 'opacity-0'}`}
              style={{ background: 'white' }}
            >
              {/* 워터마크 숫자: 위치 및 크기 최적화 */}
              <div className="absolute top-4 right-6 font-cormorant text-6xl font-light text-gold/10 select-none group-hover:text-gold/20 transition-colors">
                {svc.num}
              </div>

              {/* 아이콘: 크기 소폭 축소 */}
              <div className="text-orange-deep/70 group-hover:text-orange mb-4 transition-colors">
                <div className="w-8 h-8">{svc.icon}</div>
              </div>

              {/* Tag */}
              <p className="section-tag mb-2 text-orange-deep font-bold text-[10px] tracking-widest">{svc.tag}</p>

              {/* Title */}
              <div className="flex items-baseline gap-2 mb-3">
                <h3 className="section-heading text-xl text-parchment font-semibold">{svc.title}</h3>
              </div>

              {/* Desc: 폰트 크기 및 줄 간격 최적화 (가장 중요한 부분) */}
              <p className="text-[13px] text-parchment/75 leading-snug font-noto font-medium mb-5 line-clamp-2 xl:line-clamp-none">
                {svc.desc}
              </p>

              {/* Platform chips: 상하 간격 축소 */}
              <div className="flex flex-wrap gap-2">
                {svc.platforms.map((p) => (
                  <span key={p} className="px-2.5 py-1 text-[9px] tracking-[.05em] border border-gold/30 text-gold font-bold font-notosc bg-gold/5 group-hover:bg-gold group-hover:text-white transition-all rounded-sm">
                    {p}
                  </span>
                ))}
              </div>

              {/* Arrow */}
              <div className="absolute bottom-6 right-6 text-orange-deep/40 group-hover:text-orange group-hover:translate-x-1 transition-all duration-300">
                <svg className="w-5 h-5" fill="none" viewBox="0 0 20 20">
                  <path d="M4 10h12M12 6l4 4-4 4" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                </svg>
              </div>
            </Link>
          ))}
        </div>
      </div>

      <style jsx>{`
        /* 서비스 섹션 내부의 개별 패딩 강제 제거 */
        #how { padding-top: 0 !important; padding-bottom: 0 !important; }
        .glass-card { min-height: unset !important; }
      `}</style>
    </section>
  );
}