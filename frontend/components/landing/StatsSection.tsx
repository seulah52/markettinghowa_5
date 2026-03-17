'use client';
import { useRef, useEffect, useState } from 'react';
import { motion, useSpring, useTransform, useInView, AnimatePresence } from 'framer-motion';

const STATS = [
  { target: 4, unit: '개', label: '연동 플랫폼', sub: '小红书 · 淘宝 · 百度 · 抖音' },
  { target: 98, unit: '%', label: '분석 정확도', sub: 'Gemini 1.5 Pro 기반' },
  { target: 5, unit: '분', label: '레포트 생성', sub: '크롤링부터 출력까지' },
  { target: 1200, unit: '+', label: '분석 키워드', sub: '월간 처리 건수' },
];

// 숫자가 올라가는 애니메이션 컴포넌트
function Counter({ value, isComma = false }: { value: number; isComma?: boolean }) {
  const ref = useRef(null);
  const isInView = useInView(ref, { once: true });
  const springValue = useSpring(0, {
    stiffness: 50, // 더 묵직하고 신뢰감 있는 상승을 위해 조정
    damping: 30,
  });

  const displayValue = useTransform(springValue, (latest) => {
    const num = Math.floor(latest);
    return isComma ? num.toLocaleString() : String(num);
  });

  useEffect(() => {
    if (isInView) {
      springValue.set(value);
    }
  }, [isInView, value, springValue]);

  return <motion.span ref={ref}>{displayValue}</motion.span>;
}

export default function StatsSection() {
  const containerRef = useRef(null);
  const isInView = useInView(containerRef, { once: true, margin: "-100px" });

  return (
    <section 
      ref={containerRef}
      className="relative py-10 px-3 overflow-hidden" 
      style={{ background: 'var(--ink)' }} 
    >
      {/* 배경 장식: 밝은 배경에 맞춰 Camel과 Brandy 톤의 은은한 혼합 적용 */}
      <div className="absolute inset-0" style={{ background: 'linear-gradient(135deg, rgba(196,147,109,0.08) 0%, transparent 50%, rgba(140,76,61,0.05) 100%)' }} />
      <div className="deco-line absolute top-0 left-0 right-0 opacity-30 bg-gold" />
      <div className="deco-line absolute bottom-0 left-0 right-0 opacity-30 bg-gold" />

      <div className="max-w-7xl mx-auto relative z-10">
        {/* 가독성을 위해 테두리(bg-gold/10)의 농도를 소폭 상향(20)하여 그리드 구분 명확화 */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-px bg-gold/30 shadow-soft">
          {STATS.map((s, i) => (
            <div
              key={s.label}
              className="relative bg-white p-1 md:p-5 text-center transition-colors duration-500 hover:bg-parchment/5"
            >
              <motion.div
                initial={{ opacity: 0, y: 30 }}
                animate={isInView ? { opacity: 1, y: 0 } : {}}
                transition={{ duration: 1, delay: i * 0.1, ease: "easeOut" }}
              >
                <div className="flex items-end justify-center gap-1 mb-4">
                  {/* 숫자: Brandy 색상을 적용하여 신뢰감과 무게감 부여 */}
                  <span className="stat-number text-[clamp(32px,5vw,56px)] leading-none text-red-deep font-semibold">
                    <Counter value={s.target} isComma={s.target >= 1000} />
                  </span>
                  {/* 단위: Camel 색상으로 포인트 유지 */}
                  <span className="font-cormorant text-2xl text-gold font-bold mb-1.5">
                    {s.unit}
                  </span>
                </div>
                
                {/* 라벨: 본문 텍스트 컬러(parchment)를 사용하고 굵기 상향 */}
                <p className="text-sm font-noto font-bold text-parchment tracking-widest mb-2 uppercase">
                  {s.label}
                </p>
                {/* 서브텍스트: 25% -> 50% 농도로 상향하여 가독성 확보 */}
                <p className="text-xs font-notosc text-parchment/50 font-medium">
                  {s.sub}
                </p>
              </motion.div>
              
              {/* 호버 시 Camel 색상의 아주 은은한 발광 효과 */}
              <div className="absolute inset-0 bg-gold/[0.03] opacity-0 group-hover:opacity-100 transition-opacity duration-500 pointer-events-none" />
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}