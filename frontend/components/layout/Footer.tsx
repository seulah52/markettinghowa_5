'use client';
import Link from 'next/link';

/**
 * Footer: 플랫폼 하단 정보 섹션
 * 밝은 Earthy 테마 가독성 보정 및 브랜드 일관성 강화 버전
 */
export default function Footer() {
  return (
    <footer className="relative py-20 pb-12 px-6 overflow-hidden" style={{ background: 'var(--ink)' }}>
      {/* 상단 경계선: Camel 톤으로 강조 */}
      <div className="absolute top-0 left-0 right-0 h-px bg-gold/20" />
      
      <div className="max-w-7xl mx-auto">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-12 mb-16">

          {/* 1. Brand Section: 로고 및 슬로건 */}
          <div className="md:col-span-2 space-y-6">
            <div className="flex items-center gap-4">
              <div className="relative w-10 h-10 flex items-center justify-center">
                <img
                  src="/images/markettinghowa_logo_icon.png"
                  alt="마케팅호와 로고"
                  className="w-full h-full object-contain transition-transform group-hover:scale-105"
                />
              </div>
              <div className="relative h-8 w-44">
                <img
                  src="/images/markettinghowa_logo_text.png"
                  alt="MARKETTINGHOWA"
                  className="w-full h-full object-contain object-left"
                />
              </div>
            </div>
            <p className="text-sm text-parchment/70 leading-relaxed max-w-sm font-cormorant font-medium">
              AI 기반 중국 시장 분석 플랫폼<br />
              데이터 드리븐 수출 전략의 새로운 기준을 제시합니다.
            </p>

            {/* 브랜드 포인트 라인 */}
            <div className="w-24 h-[2px] bg-gold/40" />
          </div>

          {/* 2. Service Links: Brandy 톤 적용 */}
          <div>
            <p className="section-tag mb-6 text-red-deep font-bold tracking-widest uppercase">서비스</p>
            <nav className="space-y-3">
              {['시장 분석', '브랜드 스토리', '홍보물 제작', '왕홍 매칭'].map((t) => (
                <div key={t}>
                  <Link 
                    href="#" 
                    className="text-sm text-parchment/60 hover:text-orange-deep transition-colors font-noto font-medium hover:translate-x-1 inline-block transform"
                  >
                    {t}
                  </Link>
                </div>
              ))}
            </nav>
          </div>

          {/* 3. Company Links */}
          <div>
            <p className="section-tag mb-6 text-orange-deep font-bold tracking-widest uppercase">회사</p>
            <nav className="space-y-3">
              {['서비스 소개', '이용 방법', '공지사항', '문의하기'].map((t) => (
                <div key={t}>
                  <Link 
                    href="#" 
                    className="text-sm text-parchment/60 hover:text-red-deep transition-colors font-noto font-medium hover:translate-x-1 inline-block transform"
                  >
                    {t}
                  </Link>
                </div>
              ))}
            </nav>
          </div>
        </div>

        {/* 하단 구분선 */}
        <div className="h-px bg-gold/10 mb-8 w-full" />

        {/* 4. Bottom Info: Copyright 및 법적 고지 */}
        <div className="flex flex-col md:flex-row justify-between items-center gap-6">
          <div className="flex flex-col items-center md:items-start gap-2">
            <p className="text-[11px] text-parchment/40 font-noto tracking-wider">
              © 2026 <span className="font-bold text-red-deep/50">MARKETTINGHOWA</span>. All rights reserved.
            </p>
          </div>
          
          <div className="flex gap-8 items-center">
            {['이용약관', '개인정보처리방침'].map((t) => (
              <Link 
                key={t} 
                href="#" 
                className="text-[11px] text-parchment/40 hover:text-orange-deep transition-colors font-noto font-bold tracking-tight border-b border-transparent hover:border-orange-deep/30 pb-0.5"
              >
                {t}
              </Link>
            ))}
          </div>
        </div>
      </div>
    </footer>
  );
}