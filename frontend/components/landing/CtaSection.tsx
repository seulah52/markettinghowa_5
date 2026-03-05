'use client';
import { useRef, useEffect, useState } from 'react';
import Link from 'next/link';

function useIntersect() {
  const ref = useRef<HTMLDivElement>(null);
  const [visible, setVisible] = useState(false);
  useEffect(() => {
    const obs = new IntersectionObserver(([e]) => { if (e.isIntersecting) setVisible(true); }, { threshold: 0.2 });
    if (ref.current) obs.observe(ref.current);
    return () => obs.disconnect();
  }, []);
  return { ref, visible };
}

export default function CtaSection() {
  const { ref, visible } = useIntersect();
  
  return (
    <section 
      ref={ref} 
      className="relative py-32 px-6 overflow-hidden" 
      style={{ background: 'var(--ink)' }} // 전체 배경과 통일 (Parchment Beige)
    >
      {/* 1. Big BG text: 밝은 배경에 맞춰 투명도를 극도로 낮춰(0.03) 은은한 각인 효과 부여 */}
      <div className="absolute inset-0 flex items-center justify-center pointer-events-none select-none overflow-hidden">
        <span className="font-cormorant text-[22vw] font-bold text-gold/[0.04] whitespace-nowrap tracking-tighter">
          中国市场
        </span>
      </div>

      {/* 2. 배경 그라데이션: Brandy(#8C4C3D) 색상을 활용한 따뜻한 중앙 집중 광원 */}
      <div 
        className="absolute inset-0" 
        style={{ background: 'radial-gradient(circle at 50% 50%, rgba(140, 76, 61, 0.08) 0%, transparent 70%)' }} 
      />

      <div className="relative z-10 max-w-4xl mx-auto text-center">
        {/* 상단 태그: Brandy 색상으로 강조 */}
        <p className={`section-tag mb-6 font-bold text-orange-deep tracking-[0.4em] ${visible ? 'animate-fadeIn opacity-100' : 'opacity-0'}`}>
          GET STARTED
        </p>

        {/* 메인 카피: 가독성을 위해 font-medium 상향 및 자간 조절 */}
        <h2 className={`section-heading text-[clamp(32px,5vw,60px)] text-parchment mb-8 leading-[1.2] ${visible ? 'animate-fadeUp delay-200 opacity-100' : 'opacity-0'}`}>
          지금 바로<br />
          <span className="text-gold-gradient font-semibold">중국 시장을 분석</span>해보세요
        </h2>

        {/* 서브 텍스트: 폰트 굵기를 500으로 상향하여 밝은 배경에서의 가독성 해결 */}
        <p className={`text-lg text-parchment/70 leading-relaxed font-noto font-medium mb-12 max-w-2xl mx-auto ${visible ? 'animate-fadeUp delay-300 opacity-100' : 'opacity-0'}`}>
          키워드 하나면 충분합니다. 수출가능성 분석부터 인플루언서 매칭까지<br />
          당신의 중국 진출 첫 발걸음을 <span className="text-red-deep font-bold italic">MARKETTINGHOWA</span>가 함께합니다.
        </p>

        {/* CTA 버튼: Burnt Umber(#B82E26) 컬러와 강력한 Shadow 적용 */}
        <div className={`flex items-center justify-center gap-6 flex-wrap ${visible ? 'animate-fadeUp delay-400 opacity-100' : 'opacity-0'}`}>
          <Link href="/analysis" className="btn-primary text-base px-12 py-5 shadow-brand rounded-sm flex items-center gap-3">
            <span className="font-bold">무료로 시작하기</span>
            <svg className="w-5 h-5 transition-transform group-hover:translate-x-1" fill="none" viewBox="0 0 16 16">
              <path d="M3 8h10M9 4l4 4-4 4" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
          </Link>
          
          {/* 보조 버튼 (선택사항): 브랜딩 일관성을 위한 Outline 스타일 */}
          <Link href="/contact" className="btn-outline text-base px-12 py-5 font-bold">
            문의하기
          </Link>
        </div>
      </div>

      {/* 하단 데코 라인 */}
      <div className="absolute bottom-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-gold/30 to-transparent" />
    </section>
  );
}