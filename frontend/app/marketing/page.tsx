'use client';
import { useState, useEffect } from 'react';
import Header from '@/components/layout/Header';
import Footer from '@/components/layout/Footer';
import ChatbotButton from '@/components/chatbot/ChatbotButton';
import { getApiBase } from '@/lib/api/client';

const FONTS = [
  { id: 'JianZhengLiHei',        label: 'JianZheng LiHei (정석 리헤이)' },
  { id: 'XingQiuHei',            label: 'XingQiu Hei (행성 헤이)' },
  { id: 'XinRui',                label: 'XinRui (신예)' },
  { id: 'ZhengQingKeShuaiHeiTi', label: 'ZhengQing KeShuai (정청 코슈아이)' },
];

const IMAGE_THEMES = [
  { id: 'warm_living', name_kr: '☀️ 자연채광 웜톤 거실 컷' },
  { id: 'minimal',     name_kr: '🛋️ 모던 미니멀리즘 컷' },
  { id: 'cinematic',   name_kr: '🌃 무드 시네마틱 라운지 컷' },
  { id: 'planteria',   name_kr: '🌿 식물테리어(플랜테리어) 컷' },
];

// 볼드(**text**) 마크다운을 JSX로 렌더
function renderBold(text: string) {
  const parts = text.split(/(\\*\\*[^*]+\\*\\*)/g);
  return parts.map((p, i) =>
    p.startsWith('**') && p.endsWith('**')
      ? <strong key={i} className="text-parchment font-bold">{p.slice(2, -2)}</strong>
      : <span key={i}>{p}</span>
  );
}

export default function MarketingPage() {
  const [activeStep, setActiveStep]   = useState(1);
  const [loading, setLoading]         = useState<{[k: number]: boolean}>({ 2: false, 3: false, 4: false, 5: false });
  const [selectedThemes, setSelectedThemes] = useState<string[]>([]);

  // --- DATA STATES ---
  // 이전 데이터 불러오기 / 직접 입력 모드
  const [inputMode, setInputMode] = useState<'manual' | 'loaded'>('manual');
  const [loadingPrev, setLoadingPrev] = useState(false);

  // 제품명 번역 상태
  const [productTranslation, setProductTranslation] = useState<{kr: string; en: string; cn: string}>({ kr: '', en: '', cn: '' });
  const [translatingProduct, setTranslatingProduct] = useState(false);

  const [step1, setStep1] = useState({
    platform:  'xiaohongshu',
    brand:     '',
    product:   '',
    category:  '',
    price:     '',
    features:  '',
    promo:     '',
    image:     null as string | null,
    imageSize: '1024x1792',
  });

  const [step2, setStep2] = useState({
    themes:      [] as any[],
    overlays:    [] as string[],
    selectedBase: null as string | null,
    final:        null as string | null,
  });

  // 브랜드명, 가격 오버레이 개별 설정
  const [design, setDesign] = useState({
    text: '', font: 'JianZhengLiHei', color: '#FFFFFF', size: 0.08,
    x: 0.5, y: 0.8, rotation: 0,
    shadow: true, outline: false, outColor: '#000000',
    bg: false, bgColor: '#000000', bgOpacity: 0.5,
    // 브랜드명 오버레이 - 개별 설정
    showBrand: false, brandText: '', brandFont: 'JianZhengLiHei',
    brandColor: '#FFFFFF', brandSize: 0.08, brandX: 0.5, brandY: 0.7,
    brandShadow: false, brandOutline: false, brandOutColor: '#000000',
    brandBg: false, brandBgColor: '#000000', brandBgOpacity: 0.5,
    // 가격 오버레이 - 개별 설정
    showPrice: false, priceText: '', priceFont: 'JianZhengLiHei',
    priceColor: '#FFFFFF', priceSize: 0.08, priceX: 0.5, priceY: 0.6,
    priceShadow: false, priceOutline: false, priceOutColor: '#000000',
    priceBg: false, priceBgColor: '#000000', priceBgOpacity: 0.5,
  });

  // STEP3 언어 토글
  const [step3Lang, setStep3Lang] = useState<'cn' | 'kr'>('cn');

  const [step3In, setStep3In] = useState({ target: '', concept: '' });
  const [step3Result, setStep3Result] = useState({
    title: '', body: '', title_kr: '', body_kr: '',
    hashtags: [] as string[],
    realHashtags: [] as { tag: string; kr: string }[],
  });
  const [step4Result, setStep4Result] = useState({ memo: '', banned: {} as {[k: string]: string} });
  const [step5Result, setStep5Result] = useState({
    storyboard: [] as any[],
    subtitles: { cn: [] as string[], kr: [] as string[] },
  });

  // 이전 데이터 불러오기
  const loadPreviousData = async () => {
    setLoadingPrev(true);
    try {
      const res = await fetch(`${getApiBase()}/api/v1/marketing/previous-data`);
      const data = await res.json();
      if (data.status === 'ok') {
        setStep1(prev => ({
          ...prev,
          product:  data.keyword  || prev.product,
          category: data.category || prev.category,
        }));
        setInputMode('loaded');
        // 불러온 제품명이 있으면 즉시 번역 시작
        if (data.keyword) translateProduct(data.keyword);
      }
    } catch (e) { console.error(e); }
    finally { setLoadingPrev(false); }
  };

  // 제품명 번역 (한 → 영 → 중)
  const translateProduct = async (productKr: string) => {
    if (!productKr.trim()) return;
    setTranslatingProduct(true);
    try {
      const res = await fetch(`${getApiBase()}/api/v1/marketing/translate-product`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ product_kr: productKr }),
      });
      const data = await res.json();
      if (data.status === 'ok') {
        setProductTranslation({ kr: data.kr, en: data.en, cn: data.cn });
      }
    } catch (e) { console.error(e); }
    finally { setTranslatingProduct(false); }
  };

  // 직접 입력 모드로 초기화
  const resetToManual = () => {
    setInputMode('manual');
    setStep1(prev => ({ ...prev, product: '', category: '' }));
    setProductTranslation({ kr: '', en: '', cn: '' });
  };

  // --- LOGIC ---
  const runStep2 = async () => {
    if (!step1.image || !step1.product) return;
    setLoading(p => ({ ...p, 2: true }));
    try {
      const res = await fetch(`${getApiBase()}/api/v1/marketing/step2-init`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          image_b64:       step1.image,
          brand:           step1.brand,
          product:         step1.product,
          features:        step1.features,
          category:        step1.category,
          price:           step1.price,
          promo:           step1.promo,
          image_size:      step1.imageSize,
          selected_themes: selectedThemes.length > 0
            ? selectedThemes.map(id => IMAGE_THEMES.find(t => t.id === id)?.name_kr).filter(Boolean)
            : [],
        }),
      });
      const data = await res.json();
      const themes   = Array.isArray(data.themes)   ? data.themes   : [];
      const overlays = Array.isArray(data.overlays) ? data.overlays : [];
      setStep2(prev => ({
        ...prev, themes, overlays,
        selectedBase: themes[0]?.image_b64 || prev.selectedBase || null,
      }));
      setDesign(prev => ({ ...prev, text: overlays[0] || prev.text || '' }));
      setActiveStep(2);
    } catch (e) { console.error(e); }
    finally { setLoading(p => ({ ...p, 2: false })); }
  };

  useEffect(() => {
    if (step2.selectedBase) {
      const t = setTimeout(() => applyOverlay(), 300);
      return () => clearTimeout(t);
    }
  }, [design, step2.selectedBase]);

  const applyOverlay = async () => {
    try {
      const res = await fetch(`${getApiBase()}/api/v1/marketing/overlay`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          image_b64:    step2.selectedBase,
          text:         design.text,
          font_name:    design.font,
          color:        design.color,
          size_ratio:   design.size,
          pos_x:        design.x,
          pos_y:        design.y,
          rotation:     design.rotation,
          shadow:       design.shadow,
          outline:      design.outline,
          outline_color: design.outColor,
          bg_enabled:   design.bg,
          bg_color:     design.bgColor,
          bg_opacity:   design.bgOpacity,
          // 브랜드명 오버레이 - 개별 설정
          brand_text:   design.showBrand ? (design.brandText || step1.brand) : '',
          brand_font:   design.brandFont,
          brand_color:  design.brandColor,
          brand_size:   design.brandSize,
          brand_x:      design.brandX,
          brand_y:      design.brandY,
          brand_shadow: design.brandShadow,
          brand_outline: design.brandOutline,
          brand_out_color: design.brandOutColor,
          brand_bg:     design.brandBg,
          brand_bg_color: design.brandBgColor,
          brand_bg_opacity: design.brandBgOpacity,
          // 가격 오버레이 - 개별 설정
          price_text:   design.showPrice ? (design.priceText || (step1.price ? `¥${step1.price}` : '')) : '',
          price_font:   design.priceFont,
          price_color:  design.priceColor,
          price_size:   design.priceSize,
          price_x:      design.priceX,
          price_y:      design.priceY,
          price_shadow: design.priceShadow,
          price_outline: design.priceOutline,
          price_out_color: design.priceOutColor,
          price_bg:     design.priceBg,
          price_bg_color: design.priceBgColor,
          price_bg_opacity: design.priceBgOpacity,
        }),
      });
      const data = await res.json();
      if (data.status === 'ok') setStep2(p => ({ ...p, final: data.image_b64 }));
    } catch (e) { console.error(e); }
  };

  const runStep3 = async () => {
    setLoading(p => ({ ...p, 3: true }));
    try {
      const res = await fetch(`${getApiBase()}/api/v1/marketing/step3-generate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          target:     step3In.target,
          features:   step1.features,
          brand:      step1.brand,
          product:    step1.product,
          product_en: productTranslation.en,
          product_cn: productTranslation.cn,
          platform:   step1.platform,
          category:   step1.category,
        }),
      });
      const data = await res.json();
      if (data.status === 'ok') {
        setStep3Result({
          title:        data.title,
          body:         data.body,
          title_kr:     data.title_kr,
          body_kr:      data.body_kr,
          hashtags:     data.hashtags,
          realHashtags: data.real_hashtags,
        });
        setActiveStep(3);  // STEP3 완료 — STEP4는 버튼으로 진행
      }
    } catch (e) { console.error(e); }
    finally { setLoading(p => ({ ...p, 3: false })); }
  };

  const runStep4 = async () => {
    setLoading(p => ({ ...p, 4: true }));
    try {
      const res = await fetch(`${getApiBase()}/api/v1/marketing/step4-memo`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          brand: step1.brand, product: step1.product,
          features: step1.features, platform: step1.platform,
          category: step1.category, price: step1.price,
          promo: step1.promo, target: step3In.target,
        }),
      });
      const data = await res.json();
      if (data.status === 'ok') {
        setStep4Result({ memo: data.memo, banned: data.banned_explanation });
        setActiveStep(4);
      }
    } catch (e) { console.error(e); }
    finally { setLoading(p => ({ ...p, 4: false })); }
  };

  const runStep5 = async () => {
    setLoading(p => ({ ...p, 5: true }));
    try {
      const res = await fetch(`${getApiBase()}/api/v1/marketing/step5-video`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          brand: step1.brand, product: step1.product,
          title: step3Result.title, body: step3Result.body,
          platform: step1.platform,
        }),
      });
      const data = await res.json();
      if (data.status === 'ok') {
        setStep5Result({
          storyboard: data.storyboard,
          subtitles: { cn: data.subtitles_cn, kr: data.subtitles_kr },
        });
        setActiveStep(5);
      }
    } catch (e) { console.error(e); }
    finally { setLoading(p => ({ ...p, 5: false })); }
  };

  // 현재 언어에 따른 제목/본문
  const displayTitle = step3Lang === 'cn' ? step3Result.title    : step3Result.title_kr;
  const displayBody  = step3Lang === 'cn' ? step3Result.body     : step3Result.body_kr;

  return (
    <>
      <Header />
      <main className="marketing-page min-h-screen pt-24 pb-16 px-6" style={{ background: 'var(--ink)' }}>
        <div className="max-w-6xl mx-auto space-y-12">

          <div className="mb-12 text-center">
            <p className="section-tag mb-3">AI Marketing Orchestration</p>
            <h1 className="section-heading text-4xl text-parchment mb-4">홍보물 제작</h1>
            <div className="deco-line w-16 mx-auto" />
          </div>

          {/* ─── STEP 1 ─── */}
          <section className="glass-card p-10">
            <div className="flex items-center justify-between mb-8">
              <p className="section-tag text-gold" style={{ fontSize: '20px' }}>STEP 01. 플랫폼 및 제품 기초 설정</p>
              <div className="flex gap-2">
                <button
                  onClick={loadPreviousData}
                  disabled={loadingPrev}
                  className={`px-5 py-2 text-xs border font-mono uppercase tracking-widest transition-all ${inputMode === 'loaded' ? 'border-gold text-gold bg-gold/10' : 'border-white/15 text-white/40 hover:border-gold/50 hover:text-gold/70'} ${loadingPrev ? 'opacity-50 pointer-events-none' : ''}`}
                >
                  {loadingPrev ? '불러오는 중...' : '📂 이전 데이터 불러오기'}
                </button>
                <button
                  onClick={resetToManual}
                  className={`px-5 py-2 text-xs border font-mono uppercase tracking-widest transition-all ${inputMode === 'manual' ? 'border-gold text-gold bg-gold/10' : 'border-white/15 text-white/40 hover:border-gold/25'}`}
                >
                  ✏️ 직접 입력
                </button>
              </div>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-10">
              <div className="space-y-6">
                <div className="grid grid-cols-2 gap-4">
                  {/* 브랜드명: 영문 필수 안내 */}
                  <input
                    value={step1.brand}
                    onChange={e => setStep1({ ...step1, brand: e.target.value })}
                    placeholder="브랜드명 (영문 필수, e.g. SUNRIU)"
                    className="bg-white/5 border border-white/10 px-4 py-3 text-sm text-parchment outline-none focus:border-gold/50"
                  />
                  <div className="flex flex-col gap-1.5">
                    <input
                      value={step1.product}
                      onChange={e => {
                        setStep1({ ...step1, product: e.target.value });
                        setProductTranslation({ kr: '', en: '', cn: '' });
                      }}
                      onBlur={e => { if (e.target.value.trim()) translateProduct(e.target.value.trim()); }}
                      placeholder="제품명 (한국어 입력)"
                      className="bg-white/5 border border-white/10 px-4 py-3 text-sm text-parchment outline-none focus:border-gold/50"
                    />

                  </div>
                </div>
                <input value={step1.category} onChange={e => setStep1({ ...step1, category: e.target.value })} placeholder="카테고리" className="w-full bg-white/5 border border-white/10 px-4 py-3 text-sm text-parchment outline-none focus:border-gold/50" />
                <div className="grid grid-cols-2 gap-4">
                  <input value={step1.price} onChange={e => setStep1({ ...step1, price: e.target.value })} placeholder="판매 가격 (위안)" className="bg-white/5 border border-white/10 px-4 py-3 text-sm text-parchment outline-none focus:border-gold/50" />
                  <input value={step1.promo} onChange={e => setStep1({ ...step1, promo: e.target.value })} placeholder="프로모션" className="bg-white/5 border border-white/10 px-4 py-3 text-sm text-parchment outline-none focus:border-gold/50" />
                </div>
                <textarea value={step1.features} onChange={e => setStep1({ ...step1, features: e.target.value })} placeholder="제품 핵심 특징" className="w-full h-32 bg-white/5 border border-white/10 px-4 py-3 text-sm text-parchment outline-none focus:border-gold/50" />
                <div className="flex flex-col gap-2 pt-2">
                  <label className="text-[11px] text-white/40 uppercase font-mono">이미지 비율 / 해상도</label>
                  <select value={step1.imageSize} onChange={e => setStep1({ ...step1, imageSize: e.target.value })}
                    className="w-full bg-white/5 border border-white/10 px-3 py-2 text-xs text-parchment outline-none focus:border-gold/50">
                    <option value="1024x1792">세로형 1024×1792 (DALL-E 3 표준)</option>
                    <option value="1024x1024">정사각형 1024×1024</option>
                  </select>
                </div>
              </div>
              <div className="flex flex-col justify-center items-center border-2 border-dashed border-white/10 rounded-xl p-10 bg-white/[0.02]">
                {step1.image
                  ? <img src={step1.image} className="max-h-[300px] object-contain rounded shadow-2xl" />
                  : <div className="h-48"></div>}
                
                {/* 이미지 업로드 그룹: 문구 + 버튼을 중앙에 묶음 */}
                <div className="flex flex-col items-center gap-2">
                  <p className="text-white/50 text-sm font-noto text-center">이미지를 업로드하세요</p>
                  <label className="px-8 py-4 bg-gold text-ink font-bold uppercase text-sm tracking-widest rounded cursor-pointer hover:bg-gold/80 transition-all">
                    📁 파일 선택
                    <input
                      type="file"
                      onChange={e => {
                        const f = e.target.files?.[0];
                        if (f) { const r = new FileReader(); r.onloadend = () => setStep1({ ...step1, image: r.result as string }); r.readAsDataURL(f); }
                      }}
                      className="hidden"
                    />
                  </label>
                  <p className="text-xs text-white/30 font-mono">
                    {step1.image ? '✓ 파일 선택됨' : '선택된 파일 없음'}
                  </p>
                </div>
              </div>
            </div>
            <div className="mt-10 pt-10 border-t border-white/5 space-y-6">
              <div>
                <p className="text-sm text-black/30 uppercase font-mono tracking-widest mb-4 text-center">이미지 생성 테마 선택 (복수 선택 가능)</p>
                <div className="flex flex-wrap gap-3 justify-center">
                  {IMAGE_THEMES.map(theme => (
                    <button key={theme.id}
                      onClick={() => setSelectedThemes(prev => prev.includes(theme.id) ? prev.filter(id => id !== theme.id) : [...prev, theme.id])}
                      className={`px-6 py-3 text-sm border rounded-sm transition-all font-mono ${selectedThemes.includes(theme.id) ? 'border-gold text-gold bg-gold/10' : 'border-white/10 text-white/40 hover:border-white/20 hover:text-white/60'}`}>
                      {theme.name_kr}
                    </button>
                  ))}
                </div>
              </div>
              <div className="text-center">
                <button onClick={runStep2} disabled={!step1.product || !step1.image || loading[2]}
                  className={`btn-primary px-20 py-4 font-bold uppercase text-sm tracking-widest ${loading[2] ? 'pointer-events-none opacity-70' : ''}`}>
                  {loading[2] ? '마케팅 컨텐츠 생성 중...' : '마케팅 컨텐츠 생성 시작'}
                </button>
              </div>
            </div>
          </section>

          {/* ─── STEP 2 ─── */}
          {(activeStep >= 2 || step2.themes.length > 0) && (
            <section className="glass-card p-10 animate-fadeUp border-gold/20">
              <p className="section-tag mb-8 text-gold" style={{ fontSize: '20px' }}>STEP 02. AI 테마 생성 및 썸네일 디자인 확정</p>
              <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">

                {/* 좌측: 테마 그리드 + 디자인 툴 */}
                <div className="lg:col-span-1 space-y-4">
                  <p className="text-[10px] text-white/30 uppercase font-mono tracking-widest">Select Base Theme</p>
                  <div className="grid grid-cols-2 gap-3">
                    {step2.themes.map((t, i) => (
                      <div key={i} onClick={() => setStep2({ ...step2, selectedBase: t.image_b64 })}
                        className={`cursor-pointer border transition-all rounded overflow-hidden ${step2.selectedBase === t.image_b64 ? 'border-gold scale-105 shadow-xl shadow-gold/10' : 'border-white/5 opacity-60'}`}
                        style={{ aspectRatio: step1.imageSize === '1024x1024' ? '1 / 1' : '9 / 16' }}>
                        <img src={t.image_b64} className="w-full h-full object-cover" />
                      </div>
                    ))}
                  </div>

                  <div className="glass-card p-6 bg-white/5 space-y-5">
                    <p className="text-[10px] text-gold/60 uppercase font-mono tracking-[0.2em]">Precision Design Tools</p>
                    <select value={design.font} onChange={e => setDesign({ ...design, font: e.target.value })}
                      className="w-full bg-black/40 border border-white/10 px-3 py-2 text-xs text-parchment outline-none mb-2">
                      {FONTS.map(f => <option key={f.id} value={f.id} className="bg-zinc-900">{f.label}</option>)}
                    </select>

                    {/* 슬라이더 */}
                    {[
                      { label: 'X Pos',     val: design.x,        set: (v: number) => setDesign({ ...design, x: v }),        min: 0.05, max: 0.95, step: 0.01, fmt: (v: number) => `${Math.round(v * 100)}%` },
                      { label: 'Y Pos',     val: design.y,        set: (v: number) => setDesign({ ...design, y: v }),        min: 0.05, max: 0.95, step: 0.01, fmt: (v: number) => `${Math.round(v * 100)}%` },
                      { label: 'Rotation',  val: design.rotation, set: (v: number) => setDesign({ ...design, rotation: v }), min: -180,  max: 180,  step: 1,    fmt: (v: number) => `${v}°` },
                      { label: 'Font Size', val: design.size,     set: (v: number) => setDesign({ ...design, size: v }),     min: 0.02,  max: 0.2,  step: 0.005, fmt: (v: number) => `${Math.round(v * 1000)}px` },
                    ].map(s => (
                      <div key={s.label}>
                        <label className="text-[9px] text-white/20 uppercase font-mono flex justify-between">{s.label}<span>{s.fmt(s.val)}</span></label>
                        <input type="range" min={s.min} max={s.max} step={s.step} value={s.val}
                          onChange={e => s.set(parseFloat(e.target.value))} className="w-full accent-gold h-1" />
                      </div>
                    ))}

                    <div className="grid grid-cols-2 gap-4 pt-1">
                      <div><label className="text-[9px] text-white/20 uppercase font-mono">Font Color</label>
                        <input type="color" value={design.color} onChange={e => setDesign({ ...design, color: e.target.value })} className="w-full h-8 bg-transparent cursor-pointer" /></div>
                      <div><label className="text-[9px] text-white/20 uppercase font-mono">Outline Color</label>
                        <input type="color" value={design.outColor} onChange={e => setDesign({ ...design, outColor: e.target.value })} className="w-full h-8 bg-transparent cursor-pointer" /></div>
                    </div>

                    <div className="flex gap-6 pt-1">
                      <label className="flex items-center gap-2 cursor-pointer text-[11px] text-white/40 hover:text-gold transition-colors">
                        <input type="checkbox" checked={design.shadow} onChange={e => setDesign({ ...design, shadow: e.target.checked })} className="accent-gold" />그림자
                      </label>
                      <label className="flex items-center gap-2 cursor-pointer text-[11px] text-white/40 hover:text-gold transition-colors">
                        <input type="checkbox" checked={design.outline} onChange={e => setDesign({ ...design, outline: e.target.checked })} className="accent-gold" />윤곽선
                      </label>
                    </div>

                    {/* 브랜드명 오버레이 옵션 - 개별 설정 */}
                    <div className="pt-4 border-t border-white/5 space-y-3">
                      <label className="flex items-center gap-2 cursor-pointer text-[11px] text-white/40 hover:text-gold transition-colors">
                        <input type="checkbox" checked={design.showBrand} onChange={e => setDesign({ ...design, showBrand: e.target.checked })} className="accent-gold" />
                        브랜드명 오버레이
                      </label>
                      {design.showBrand && (
                        <div className="space-y-3 bg-black/20 p-3 rounded">
                          <input value={design.brandText || step1.brand}
                            onChange={e => setDesign({ ...design, brandText: e.target.value })}
                            placeholder={step1.brand || '브랜드명 (영문)'}
                            className="w-full bg-white/5 border border-white/10 px-2 py-1.5 text-xs text-parchment outline-none focus:border-gold/50" />
                          
                          <select value={design.brandFont} onChange={e => setDesign({ ...design, brandFont: e.target.value })}
                            className="w-full bg-black/40 border border-white/10 px-2 py-1.5 text-xs text-parchment outline-none">
                            {FONTS.map(f => <option key={f.id} value={f.id}>{f.label}</option>)}
                          </select>

                          <div className="grid grid-cols-2 gap-2">
                            <div><label className="text-[8px] text-white/20 uppercase">색상</label>
                              <input type="color" value={design.brandColor} onChange={e => setDesign({ ...design, brandColor: e.target.value })} className="w-full h-6" /></div>
                            <div><label className="text-[8px] text-white/20 uppercase">크기</label>
                              <input type="range" min="0.02" max="0.2" step="0.005" value={design.brandSize}
                                onChange={e => setDesign({ ...design, brandSize: parseFloat(e.target.value) })} className="w-full accent-gold" /></div>
                          </div>

                          <div className="grid grid-cols-2 gap-2">
                            <div><label className="text-[8px] text-white/20 uppercase">X위치</label>
                              <input type="range" min="0.05" max="0.95" step="0.01" value={design.brandX}
                                onChange={e => setDesign({ ...design, brandX: parseFloat(e.target.value) })} className="w-full accent-gold" /></div>
                            <div><label className="text-[8px] text-white/20 uppercase">Y위치</label>
                              <input type="range" min="0.05" max="0.95" step="0.01" value={design.brandY}
                                onChange={e => setDesign({ ...design, brandY: parseFloat(e.target.value) })} className="w-full accent-gold" /></div>
                          </div>

                          <div className="flex gap-2">
                            <label className="flex items-center gap-1 cursor-pointer text-[8px] text-white/30">
                              <input type="checkbox" checked={design.brandShadow} onChange={e => setDesign({ ...design, brandShadow: e.target.checked })} className="accent-gold" />그림자
                            </label>
                            <label className="flex items-center gap-1 cursor-pointer text-[8px] text-white/30">
                              <input type="checkbox" checked={design.brandBg} onChange={e => setDesign({ ...design, brandBg: e.target.checked })} className="accent-gold" />배경
                            </label>
                          </div>
                        </div>
                      )}
                    </div>

                    {/* 가격 오버레이 옵션 - 개별 설정 */}
                    <div className="space-y-3">
                      <label className="flex items-center gap-2 cursor-pointer text-[11px] text-white/40 hover:text-gold transition-colors">
                        <input type="checkbox" checked={design.showPrice} onChange={e => setDesign({ ...design, showPrice: e.target.checked })} className="accent-gold" />
                        가격 오버레이
                      </label>
                      {design.showPrice && (
                        <div className="space-y-3 bg-black/20 p-3 rounded">
                          <input value={design.priceText || step1.price}
                            onChange={e => setDesign({ ...design, priceText: e.target.value })}
                            placeholder={step1.price ? `¥${step1.price}` : '가격 입력 (예: ¥1,299)'}
                            className="w-full bg-white/5 border border-white/10 px-2 py-1.5 text-xs text-parchment outline-none focus:border-gold/50" />
                          
                          <select value={design.priceFont} onChange={e => setDesign({ ...design, priceFont: e.target.value })}
                            className="w-full bg-black/40 border border-white/10 px-2 py-1.5 text-xs text-parchment outline-none">
                            {FONTS.map(f => <option key={f.id} value={f.id}>{f.label}</option>)}
                          </select>

                          <div className="grid grid-cols-2 gap-2">
                            <div><label className="text-[8px] text-white/20 uppercase">색상</label>
                              <input type="color" value={design.priceColor} onChange={e => setDesign({ ...design, priceColor: e.target.value })} className="w-full h-6" /></div>
                            <div><label className="text-[8px] text-white/20 uppercase">크기</label>
                              <input type="range" min="0.02" max="0.2" step="0.005" value={design.priceSize}
                                onChange={e => setDesign({ ...design, priceSize: parseFloat(e.target.value) })} className="w-full accent-gold" /></div>
                          </div>

                          <div className="grid grid-cols-2 gap-2">
                            <div><label className="text-[8px] text-white/20 uppercase">X위치</label>
                              <input type="range" min="0.05" max="0.95" step="0.01" value={design.priceX}
                                onChange={e => setDesign({ ...design, priceX: parseFloat(e.target.value) })} className="w-full accent-gold" /></div>
                            <div><label className="text-[8px] text-white/20 uppercase">Y위치</label>
                              <input type="range" min="0.05" max="0.95" step="0.01" value={design.priceY}
                                onChange={e => setDesign({ ...design, priceY: parseFloat(e.target.value) })} className="w-full accent-gold" /></div>
                          </div>

                          <div className="flex gap-2">
                            <label className="flex items-center gap-1 cursor-pointer text-[8px] text-white/30">
                              <input type="checkbox" checked={design.priceShadow} onChange={e => setDesign({ ...design, priceShadow: e.target.checked })} className="accent-gold" />그림자
                            </label>
                            <label className="flex items-center gap-1 cursor-pointer text-[8px] text-white/30">
                              <input type="checkbox" checked={design.priceBg} onChange={e => setDesign({ ...design, priceBg: e.target.checked })} className="accent-gold" />배경
                            </label>
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                </div>

                {/* 우측: 미리보기 + 문구 선택 */}
                <div className="lg:col-span-2 space-y-8">
                  <div className="flex flex-col items-center bg-black/40 p-10 rounded-xl relative min-h-[600px] justify-center">
                    {(step2.final || step2.selectedBase) ? (
                      <img src={step2.final || step2.selectedBase || ''} className="max-h-[600px] object-contain shadow-2xl border border-white/5 rounded" />
                    ) : (
                      <div className="flex flex-col items-center gap-3 text-white/20">
                        <p className="text-xs font-mono uppercase tracking-widest">이미지 생성 대기 중</p>
                        <p className="text-[10px]">좌측 테마를 선택하세요</p>
                      </div>
                    )}

                    <div className="mt-10 w-full">
                      <p className="text-[10px] text-white/20 uppercase text-center mb-5 tracking-[0.2em] font-mono">AI Recommended Copies</p>
                      <div className="flex flex-wrap justify-center gap-2">
                        {step2.overlays.map(ov => (
                          <button key={ov} onClick={() => setDesign({ ...design, text: ov })}
                            className={`px-5 py-2.5 text-xs border transition-all ${design.text === ov ? 'border-gold text-gold bg-gold/10' : 'border-white/10 text-white/30 hover:border-white/20 hover:text-white/60'}`}>
                            {ov}
                          </button>
                        ))}
                        <div className="w-full mt-4 max-w-md mx-auto relative">
                          <input value={design.text} onChange={e => setDesign({ ...design, text: e.target.value })}
                            placeholder="또는 문구를 직접 입력하세요"
                            className="w-full bg-white/5 border border-white/10 px-4 py-2 text-xs text-parchment outline-none focus:border-gold/50" />
                          <span className="absolute right-3 top-1/2 -translate-y-1/2 text-[9px] text-white/20 uppercase font-mono">Manual Input</span>
                        </div>
                      </div>
                    </div>

                    <div className="mt-10 flex gap-4 w-full">
                      <a href={step2.final || step2.selectedBase || ''} download="marketing-thumbnail.jpg"
                        className="flex-1 text-center py-4 border border-white/10 text-white/40 text-xs hover:text-gold transition-all uppercase font-bold tracking-widest">
                        이미지 다운로드
                      </a>
                      <button onClick={() => setActiveStep(3)} className="flex-[2] btn-primary py-4 font-bold tracking-widest">
                        디자인 확정 및 다음 단계
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            </section>
          )}

          {/* ─── STEP 3 ─── */}
          {activeStep >= 3 && (
            <section className="glass-card p-10 animate-fadeUp border-gold/20 space-y-10">
              <p className="section-tag mb-2 text-gold"style={{ fontSize: '20px' }}>STEP 03. 타겟 맞춤 카피라이팅</p>
              <p className="text-[11px] text-white/30 font-mono -mt-6">DeepSeek AI · XHS 문체 학습 기반</p>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <input value={step3In.target} onChange={e => setStep3In({ ...step3In, target: e.target.value })}
                  placeholder="타겟 고객 (예: 20대 도시 여성 집사)"
                  className="bg-white/5 border border-white/10 px-4 py-3 text-sm text-parchment outline-none focus:border-gold/50" />
                <input value={step3In.concept} onChange={e => setStep3In({ ...step3In, concept: e.target.value })}
                  placeholder="원하는 게시글 컨셉 (예: 감성적인 인테리어 후기)"
                  className="bg-white/5 border border-white/10 px-4 py-3 text-sm text-parchment outline-none focus:border-gold/50" />
              </div>

              <button onClick={runStep3} disabled={loading[3]}
                className="btn-primary w-full py-4 font-bold transition-all active:scale-[0.98]">
                {loading[3]
                  ? <span className="flex items-center justify-center gap-3"><span className="animate-spin inline-block w-4 h-4 border-2 border-white/30 border-t-white rounded-full" />DeepSeek AI 카피 생성 중...</span>
                  : '제목·본문 & 해시태그 생성'}
              </button>

              {step3Result.title && (
                <div className="animate-fadeUp">
                  <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">

                    {/* 좌측 2/3: 게시글 드래프트 */}
                    <div className="lg:col-span-2 glass-card p-8 bg-white/5 border-gold/10 space-y-5">
                      <div className="flex items-center justify-between">
                        <p className="text-[10px] text-gold/60 uppercase tracking-widest font-mono">
                          {step1.platform === 'xiaohongshu' ? 'Xiaohongshu' : step1.platform.toUpperCase()} Post Draft · DeepSeek
                        </p>
                        {/* 언어 토글 버튼 */}
                        <div className="flex gap-1">
                          {(['cn', 'kr'] as const).map(lang => (
                            <button key={lang} onClick={() => setStep3Lang(lang)}
                              className={`px-4 py-1.5 text-[11px] font-mono border rounded-sm transition-all ${step3Lang === lang ? 'border-gold text-gold bg-gold/10' : 'border-white/10 text-white/30 hover:border-white/20'}`}>
                              {lang === 'cn' ? '🇨🇳 中文' : '🇰🇷 한국어'}
                            </button>
                          ))}
                        </div>
                      </div>

                      <div>
                        <p className="text-[9px] text-white/30 uppercase font-mono mb-1">제목</p>
                        <h3 className="text-lg font-bold text-parchment leading-snug">{displayTitle}</h3>
                      </div>
                      <div>
                        <p className="text-[9px] text-white/30 uppercase font-mono mb-1">본문</p>
                        <div className="bg-black/30 p-5 rounded text-sm text-parchment/70 leading-relaxed whitespace-pre-wrap italic min-h-[180px]">
                          {displayBody}
                        </div>
                      </div>
                      <div>
                        <p className="text-[9px] text-white/30 uppercase font-mono mb-2">AI 추천 해시태그</p>
                        <div className="flex flex-wrap gap-2">
                          {step3Result.hashtags.map(h => (
                            <span key={h} className="px-3 py-1 bg-gold/10 border border-gold/30 text-gold text-xs font-mono rounded-sm">{h}</span>
                          ))}
                        </div>
                      </div>
                    </div>

                    {/* 우측 1/3: 실제 XHS 해시태그 + 한국어 뜻 */}
                    <div className="lg:col-span-1 glass-card p-6 bg-white/5 border-gold/10 h-fit">
                      <p className="text-[10px] text-gold/60 uppercase tracking-widest font-mono mb-1">
                        Real XHS Hashtag Library
                      </p>
                      <p className="text-[9px] text-white/20 mb-4 font-mono">{step3Result.realHashtags.length}개 태그 학습됨 · 클릭하여 복사</p>
                      <div className="space-y-1 max-h-[550px] overflow-y-auto pr-2 custom-scrollbar">
                        {step3Result.realHashtags.map(({ tag, kr }) => (
                          <div key={tag}
                            onClick={() => navigator.clipboard?.writeText(tag)}
                            title="클릭하여 복사"
                            className="flex items-center justify-between px-3 py-2 bg-white/[0.03] border border-white/5 rounded cursor-pointer hover:border-gold/30 hover:bg-white/5 transition-colors group">
                            <span className="text-[11px] text-parchment/60 font-mono group-hover:text-parchment/90 transition-colors">{tag}</span>
                            {kr && <span className="text-[9px] text-white/25 ml-2 shrink-0 group-hover:text-gold/50 transition-colors">{kr}</span>}
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* STEP 3 완료 후 → STEP 4 진입 버튼 */}
              {step3Result.title && !step4Result.memo && (
                <div className="pt-4 text-center animate-fadeUp">
                  <button
                    onClick={runStep4}
                    disabled={loading[4]}
                    className={`btn-primary px-20 py-4 font-bold tracking-widest uppercase text-sm transition-all active:scale-[0.98] ${loading[4] ? 'opacity-70 pointer-events-none' : ''}`}
                  >
                    {loading[4]
                      ? <span className="flex items-center justify-center gap-3"><span className="animate-spin inline-block w-4 h-4 border-2 border-white/30 border-t-white rounded-full" />DeepSeek AI 전략 분석 중...</span>
                      : '광고법 검수 & 마케팅 전략 생성 →'}
                  </button>
                </div>
              )}
            </section>
          )}

          {/* ─── STEP 4 로딩 표시 ─── */}
          {loading[4] && !step4Result.memo && (
            <section className="glass-card p-10 border-gold/10 flex flex-col items-center gap-4 animate-fadeUp">
              <span className="animate-spin inline-block w-8 h-8 border-2 border-white/10 border-t-gold rounded-full" />
              <p className="text-sm text-gold/70 font-mono uppercase tracking-widest">DeepSeek AI — 마케팅 전략 분석 중...</p>
              <p className="text-[10px] text-white/20 font-mono">XHS · 타오바오 · 바이두 · 최종리포트 종합 분석</p>
            </section>
          )}

          {/* ─── STEP 4 ─── */}
          {step4Result.memo && (
            <section className="glass-card p-10 animate-fadeUp border-gold/20 space-y-10">
              <p className="section-tag mb-2 text-gold"style={{ fontSize: '20px' }}>STEP 04. 중국 광고법 금지 문구 & 마케팅 전략</p>
              <p className="text-[11px] text-white/30 font-mono -mt-6">DeepSeek AI · XHS + 타오바오 + 바이두 + 최종리포트 종합 분석</p>

              {/* 금지 문구 카드 */}
              <div>
                <p className="text-sm text-red-400/80 uppercase font-mono font-bold mb-4 tracking-widest">
                  ⚠ 중국 광고법 금지 표현 가이드
                </p>
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-3">
                  {Object.entries(step4Result.banned).map(([key, val]) => (
                    <div key={key} className="p-5 bg-red-500/5 border border-red-500/20 rounded-lg space-y-2">
                      {/* 금지 표현 */}
                      <p className="text-red-400 font-bold text-xl leading-none">{key}</p>
                      {/* 설명 */}
                      <p className="text-sm text-white/50 leading-relaxed">{val}</p>
                    </div>
                  ))}
                </div>
              </div>

              {/* 상세 마케팅 전략 */}
              <div className="glass-card p-8 bg-white/5 border-gold/10">
                <p className="text-[10px] text-gold/60 uppercase mb-6 tracking-widest font-mono">
                  Detailed AI Marketing Strategy · DeepSeek
                </p>
                <div className="text-sm text-parchment/80 leading-loose whitespace-pre-wrap font-light space-y-4">
                  {step4Result.memo.split('\n').map((line, i) => {
                    // 제목 검출: "1. ", "2. " 등으로 시작하는 라인
                    const isTitleLine = /^\\d+\\.\\s/.test(line);
                    return (
                      <p key={i} className={isTitleLine ? 'text-lg font-bold text-parchment mt-6 mb-2' : 'mb-0'}>
                        {renderBold(line)}
                      </p>
                    );
                  })}
                </div>
              </div>

              <div className="text-center">
                <button onClick={runStep5} disabled={loading[5]}
                  className={`btn-primary px-20 py-4 font-bold tracking-widest uppercase text-xs ${loading[5] ? 'opacity-70 pointer-events-none' : ''}`}>
                  {loading[5]
                    ? <span className="flex items-center justify-center gap-3"><span className="animate-spin inline-block w-4 h-4 border-2 border-white/30 border-t-white rounded-full" />DeepSeek AI 스토리보드 생성 중...</span>
                    : '최종 단계: 숏폼 영상 기획안 생성 →'}
                </button>
              </div>
            </section>
          )}

          {/* ─── STEP 5 ─── */}
          {(activeStep >= 5 || step5Result.storyboard.length > 0) && (
            <section className="glass-card p-10 animate-fadeUp border-gold/20 space-y-10">
              <p className="section-tag mb-2 text-gold">STEP 05. 숏폼 스토리보드 & 자막 생성</p>
              <p className="text-[13px] text-white/40 font-mono -mt-3 font-bold">DeepSeek AI · 플랫폼 최적화 숏폼 영상 기획안</p>

              <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
                {/* 스토리보드 테이블 */}
                <div className="lg:col-span-3 bg-black/20 rounded-xl overflow-hidden border border-white/5">
                  <table className="w-full text-left border-collapse">
                    <thead>
                      <tr className="bg-white/5 text-[11px] text-white/50 uppercase tracking-widest font-bold">
                        <th className="px-6 py-4 border-b border-white/10">Scene</th>
                        <th className="px-6 py-4 border-b border-white/10">Visual Composition</th>
                        <th className="px-6 py-4 border-b border-white/10 text-gold">Caption</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-white/5">
                      {step5Result.storyboard.map((scene, i) => (
                        <tr key={i} className="hover:bg-white/[0.02] transition-colors">
                          <td className="px-6 py-5">
                            <span className="text-gold font-mono text-[11px] block mb-1 font-bold">{typeof scene.duration === "string" && !scene.duration.includes("초") ? scene.duration + "초" : scene.duration}</span>
                            <span className="text-parchment font-bold text-[12px]">{scene.scene}</span>
                          </td>
                          <td className="px-6 py-5">
                            <div className="text-[12px] text-parchment/60 font-light leading-relaxed mb-3">
                              {scene.visual.split('\n')[0]}
                            </div>
                            {scene.visual.includes('\n') && (
                              <div className="bg-black/30 rounded p-3 border border-white/5">
                                <p className="text-[9px] text-white/40 font-mono leading-relaxed whitespace-pre-wrap">{scene.visual.split('\n').slice(1).join('\n')}</p>
                                <button
                                  onClick={() => {
                                    navigator.clipboard.writeText(scene.visual.split('\n').slice(1).join('\n'));
                                    alert('Prompt copied!');
                                  }}
                                  className="mt-2 text-[8px] text-gold hover:text-gold/80 font-bold uppercase tracking-widest"
                                >
                                  📋 Copy
                                </button>
                              </div>
                            )}
                          </td>
                          <td className="px-6 py-5">
                            <p className="text-[12px] text-gold font-noto mb-1 font-bold">{scene.caption_cn}</p>
                            <p className="text-[12px] text-white/50">{scene.caption_kr}</p>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>

                {/* 자막 리스트 */}
                <div className="lg:col-span-1 space-y-4">
                  <div className="glass-card p-6 bg-gold/5 border-gold/20 h-fit">
                    <p className="text-[10px] text-gold/60 uppercase mb-4 tracking-widest font-mono">Full Video Subtitles · DeepSeek</p>
                    <div className="space-y-4 max-h-[550px] overflow-y-auto pr-2 custom-scrollbar">
                      {step5Result.subtitles.cn.map((line, idx) => (
                        <div key={idx} className="border-l-2 border-gold/30 pl-4">
                          <p className="text-[12px] text-parchment mb-1 font-noto">{line}</p>
                          <p className="text-[12px] text-white/50">{step5Result.subtitles.kr[idx]}</p>
                        </div>
                      ))}
                    </div>
                  </div>

                  <div className="pt-6 border-t border-white/10">
                    <p className="text-[14px] text-white/70 uppercase tracking-[0.2em] mb-5 font-mono font-bold text-left">📹 Recommended AI Video Tools</p>
                    <div className="space-y-3">
                      {[
                        { label: '🎬 Runway Gen-4', desc: '정교한 카메라 워킹·모션 제어. 가장 안정적인 품질. 4K 지원.', url: 'https://runwayml.com', price: '월 $15~' },
                        { label: '🐲 Kling AI', desc: '중국 특화 AI. 동양적 텍스처·인물 묘사 최강. 5초~3분 영상.', url: 'https://klingai.com', price: '부분 무료 / 월 ¥66~' },
                        { label: '⚡ Pika Labs', desc: '초보 친화적 UI. 이미지→영상 변환 기능 탁월. 빠른 생성.', url: 'https://pika.art', price: '무료(워터마크) / 월 $8~' },
                        { label: '🌊 Hailuo AI', desc: '중국 MiniMax 제작. 사실적 인물 영상·광고 영상에 강점.', url: 'https://hailuoai.com', price: '부분 무료' },
                        { label: '✨ Luma Dream', desc: '물리적 사실감 최고 수준. 제품 클로즈업 영상에 특히 우수.', url: 'https://lumalabs.ai/dream-machine', price: '무료 30회/월 / 월 $29.99~' },
                        { label: '🤖 Grok (xAI)', desc: '일론 머스크 xAI 모델. 텍스트→영상 생성. X 바이럴 연동.', url: 'https://grok.com', price: 'X Premium 포함 ($8/월~)' },
                      ].map(tool => (
                        <a key={tool.label} href={tool.url} target="_blank" rel="noopener noreferrer"
                          className="block p-3 bg-white/[0.03] border border-white/10 hover:bg-gold/10 hover:border-gold/50 transition-all rounded">
                          <p className="text-[11px] text-gold/90 font-bold mb-1">{tool.label}</p>
                          <p className="text-[9px] text-white/40 leading-relaxed mb-1">{tool.desc}</p>
                          <p className="text-[8px] text-white/30">{tool.price}</p>
                        </a>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            </section>
          )}

        </div>
      </main>
      <Footer />
      <ChatbotButton />
    </>
  );
}
