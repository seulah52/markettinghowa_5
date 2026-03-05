'use client';
import { useRef, useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

const STEPS = [
  {
    step: 'STEP.01',
    title: '실시간 데이터 분석',
    desc: '입력한 키워드 기반 중국 주요 플랫폼에서 실시간 데이터를 수집',
    video: '/videos/process1.mp4'
  },
  {
    step: 'STEP.02',
    title: '시장 분석 레포트 생성',
    desc: '트렌드, 경쟁사 분석, 소비자 인사이트까지 한눈에',
    video: '/videos/process2.mp4'
  },
  {
    step: 'STEP.03',
    title: '홍보물 제작',
    desc: '플랫폼별 최적화된 홍보 이미지와 마케팅 문구를 자동으로 생성',
    video: '/videos/process3.mp4'
  },
  {
    step: 'STEP.04',
    title: '맞춤 인플루언서 추천',
    desc: '타겟 시장과 제품에 최적화된 왕홍 리스트와 상세정보 제공',
    video: '/videos/process4.mp4'
  },
];

export default function ProcessSection() {
  const [activeStep, setActiveStep] = useState(0);
  const autoPlayRef = useRef<NodeJS.Timeout | null>(null);

  const startAutoPlay = () => {
    stopAutoPlay();
    autoPlayRef.current = setInterval(() => {
      setActiveStep((prev) => (prev + 1) % STEPS.length);
    }, 4200); 
  };

  const stopAutoPlay = () => {
    if (autoPlayRef.current) clearInterval(autoPlayRef.current);
  };

  useEffect(() => {
    startAutoPlay();
    return () => stopAutoPlay();
  }, []);

  const handleStepClick = (index: number) => {
    setActiveStep(index);
    startAutoPlay(); 
  };

  return (
    <section className="relative py-20 px-6 overflow-hidden" style={{ background: 'var(--ink)' }}>
      {/* 배경 장식 */}
      <div className="absolute inset-0 pointer-events-none" style={{ background: 'radial-gradient(ellipse at 50% 0%, rgba(255, 255, 255, 0.1) 0%, transparent 60%)' }} />
      <div className="deco-line absolute top-0 left-0 right-0 bg-gold/20" />

      <div className="max-w-7xl mx-auto relative z-10">
        {/* 상단 헤더 */}
        <div className="mb-10">
          <p className="section-tag mb-3 opacity-0 animate-fadeIn delay-100 uppercase tracking-[.3em] font-bold text-red-deep">How It Works</p>
          <h2 className="section-heading text-[clamp(24px,4.5vh,48px)] text-parchment mb-0 font-medium leading-tight">
            마케띵호와만의 AI 엔진으로<br />
            <span className="text-gold-gradient font-semibold">맞춤형 가이드</span> 제공
          </h2>
        </div>

        <div className="flex flex-col md:flex-row gap-12 items-center">
          {/* 왼쪽 수직 스텝 리스트 */}
          <div className="w-full md:w-[450px] flex flex-col gap-0 relative">
            <div className="absolute left-[23px] top-6 bottom-6 w-px bg-red-deep/10" />

            {STEPS.map((s, i) => (
              <div
                key={s.step}
                className="group relative flex items-start gap-6 py-4 cursor-pointer"
                onClick={() => handleStepClick(i)}
              >
                <div className={`relative z-10 w-12 h-12 flex items-center justify-center rounded-full border-2 transition-all duration-500 font-cormorant flex-shrink-0 ${
                    activeStep === i ? 'bg-red border-red-deep text-white shadow-brand scale-110' : 'bg-white border-gold/20 text-white opacity-60'
                  }`}>
                  <span className="text-amber-500 font-bold">{i + 1}</span>
                </div>

                <div className={`transition-all duration-500 ${activeStep === i ? 'opacity-100 translate-x-2' : 'opacity-20'}`}>
                  <p className="section-tag text-[10px] mb-1 text-red-deep font-bold tracking-widest">{s.step}</p>
                  <h3 className="font-cormorant font-bold text-lg text-parchment mb-2 tracking-tight">{s.title}</h3>
                  <AnimatePresence>
                    {activeStep === i && (
                      <motion.p 
                        initial={{ opacity: 0, height: 0 }}
                        animate={{ opacity: 1, height: 'auto' }}
                        exit={{ opacity: 0, height: 0 }}
                        className="text-sm text-parchment/80 leading-relaxed font-noto font-medium overflow-hidden max-w-sm"
                      >
                        {s.desc}
                      </motion.p>
                    )}
                  </AnimatePresence>
                </div>
              </div>
            ))}
          </div>

          {/* 오른쪽 영상 슬라이더: 프레임 제거 및 그림자/명암 강화 */}
          <div className="relative flex-1 w-full h-[480px] rounded-2xl overflow-hidden bg-white shadow-[0_20px_50px_rgba(0,0,0,0)]">
            <video
              key={activeStep}
              autoPlay
              muted
              loop
              playsInline
              className="absolute inset-0 w-full h-full object-cover"
            >
              <source src={STEPS[activeStep].video} type="video/mp4" />
            </video>

            {/* 하단 정보 캡션 */}
            <div className="absolute bottom-8 left-8 right-8 flex justify-between items-center border-t border-white/10 pt-4 z-10">
              <span className="text-[10px] text-white/40 tracking-[.3em] font-bold font-noto uppercase tracking-widest">
                Step {activeStep + 1} Visual Guide
              </span>
              <div className="flex gap-1.5">
                {STEPS.map((_, dotIdx) => (
                  <div 
                    key={dotIdx} 
                    className={`h-1.5 rounded-full transition-all duration-500 ${
                      activeStep === dotIdx ? 'bg-red w-4' : 'bg-white/20 w-1.5'
                    }`} 
                  />
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}