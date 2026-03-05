'use client';
import { useEffect, useState } from 'react';

const ROTATING_WORDS = ['小红书', '淘宝', '百度', '抖音', '天猫'];

export default function HeroSection() {
  const [wordIdx, setWordIdx] = useState(0);
  const [fade, setFade] = useState(true);

  useEffect(() => {
    const interval = setInterval(() => {
      setFade(false);
      setTimeout(() => {
        setWordIdx((i) => (i + 1) % ROTATING_WORDS.length);
        setFade(true);
      }, 300);
    }, 2200);
    return () => clearInterval(interval);
  }, []);

  return (
    <section className="relative min-h-screen flex items-center justify-center overflow-hidden" style={{ background: 'var(--ink)' }}>
      
      {/* 1. 배경 비주얼 레이어 */}
      <div className="absolute inset-0 z-0">
        {/* 중앙 집중형 그라데이션으로 변경하여 시선 집중 */}
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_center,transparent_0%,var(--ink)_80%)] z-10" />
        
        {/* 발광 효과를 중앙 상단으로 이동 */}
        <div className="absolute top-[-10%] left-1/2 -translate-x-1/2 w-[1000px] h-[600px] opacity-10" 
             style={{ background: 'radial-gradient(circle, var(--gold) 0%, transparent 70%)' }} />
        
        {/* 데이터 시각화 형상을 배경 중앙으로 배치 (은은하게) */}
        <div className="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 w-[70vw] h-[70vw] opacity-[0.05]">
          <svg viewBox="0 0 700 700" fill="none" xmlns="http://www.w3.org/2000/svg" className="w-full h-full animate-spin-slow">
            <circle cx="350" cy="350" r="340" stroke="var(--gold)" strokeWidth="1" strokeDasharray="15 30" />
            <circle cx="350" cy="350" r="260" stroke="var(--orange)" strokeWidth="1.5" strokeDasharray="5 20" />
          </svg>
        </div>

        {/* 배경 한자: 중앙 정렬에 맞춰 좌우 대칭 분산 배치 */}
        <div className="absolute inset-0 flex justify-between items-center px-20 pointer-events-none opacity-[0.03]">
          <span className="text-9xl font-bold text-parchment font-notosc">进</span>
          <span className="text-9xl font-bold text-parchment font-notosc">贸</span>
        </div>
      </div>

      {/* 2. 메인 컨텐츠: 중앙 정렬 */}
      <div className="relative z-20 w-full max-w-5xl mx-auto px-6 text-center">
        
        {/* 상단 태그라인 */}
        <div className="opacity-0 animate-fadeIn delay-100 mb-6 flex justify-center">
          <span className="section-tag tracking-[0.3em] text-orange-deep/90 border-x-2 border-orange px-6 uppercase text-xs font-bold">
            China Market Intelligence Platform
          </span>
        </div>

        {/* 메인 타이틀 */}
        <h1 className="font-cormorant leading-[1.2] mb-10 text-parchment">
          <span className="opacity-0 animate-fadeUp delay-200 block text-[clamp(40px,8vw,96px)] font-medium">
            중국 시장,
          </span>
          <span className="opacity-0 animate-fadeUp delay-300 block text-[clamp(40px,8vw,96px)] font-semibold mt-2">
            <span className="text-gold-gradient italic mr-4">AI</span>
            <span className="text-parchment">로 읽다</span>
          </span>
        </h1>

        {/* 플랫폼 순환 텍스트: 중앙 배치 최적화 */}
        <div className="opacity-0 animate-fadeIn delay-500 flex flex-col md:flex-row items-center justify-center gap-4 mb-12 h-auto md:h-12">
          <span className="text-xl text-parchment/60 font-noto font-medium tracking-tight">실시간 데이터 수집 </span>
          <div className="w-40 h-12 flex items-center justify-center overflow-hidden border-b border-gold/30">
            <span
              className="font-notosc text-4xl font-bold transition-all duration-300 text-red-deep"
              style={{ opacity: fade ? 1 : 0, transform: fade ? 'translateY(0)' : 'translateY(15px)' }}
            >
              {ROTATING_WORDS[wordIdx]}
            </span>
          </div>
          <span className="text-xl text-parchment/60 font-noto font-medium tracking-tight">분석 엔진 가동 중</span>
        </div>

        {/* 서브 설명 */}
        <p className="opacity-0 animate-fadeUp delay-600 text-lg md:text-xl text-parchment/70 leading-relaxed font-noto max-w-3xl mx-auto mb-0 font-large">
          중국 수출의 모든 과정을 마케띵호와 하나로!<br className="hidden md:block" />
        </p>

      </div>

    </section>
  );
}