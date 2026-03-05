'use client';
import { useState } from 'react';
import Header from '@/components/layout/Header';
import Footer from '@/components/layout/Footer';
import ChatbotButton from '@/components/chatbot/ChatbotButton';

type Mode = 'rebrand' | 'new' | null;

const DUMMY_STORY = {
  rebrand: {
    headline: '自然の恵み、中国へ',
    subheadline: '자연의 선물, 중국으로',
    story: `[브랜드명]은 한국의 청정 자연에서 출발했습니다. 제주의 화산 암반수, 한라산 진달래 추출물로 만든 이 마스크팩은 이제 중국 소비자의 피부 고민을 해결하기 위해 새 이름을 갖습니다.

"悦自然" (위에쯔란) — 자연을 즐기다.

중국 여성 소비자가 가장 신뢰하는 가치인 '천연 성분', '과학적 검증', '한국 품질'을 세 축으로 브랜드 스토리를 재구성했습니다. 小红书 트렌드 분석에 기반해 25-34세 도시 여성을 핵심 타겟으로 설정하였습니다.`,
    tags: ['#천연성분', '#K-Beauty', '#悦自然', '#补水保湿'],
  },
  new: {
    headline: '皙光 | Xi Guang',
    subheadline: '빛나는 피부, 새로운 시작',
    story: `皙光 (시광) — 피부의 빛을 되찾다.

중국 시장을 위해 처음부터 설계된 프리미엄 스킨케어 브랜드입니다. '皙'(하얗고 깨끗함)와 '光'(빛)의 결합으로, 중국 소비자가 꿈꾸는 피부 목표를 브랜드명 자체에 담았습니다.

百度 검색 데이터와 小红书 트렌드를 기반으로 '미백', '보습', '항노화' 세 가지 핵심 가치를 브랜드 DNA로 설정합니다. 天猫 플래그십 스토어를 주요 판매 채널로 하며, 왕홍 마케팅을 통한 바이럴 전략을 기반으로 합니다.`,
    tags: ['#皙光', '#美白', '#纯净美妆', '#K-Beauty'],
  },
};

export default function BrandingPage() {
  const [mode, setMode] = useState<Mode>(null);
  const [brandName, setBrandName] = useState('');
  const [brandDesc, setBrandDesc] = useState('');
  const [targetConcept, setTargetConcept] = useState(''); // 신규 브랜딩용 추가 필드
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<typeof DUMMY_STORY.rebrand | null>(null);

  const generate = () => {
    if (!mode || !brandName.trim()) return;
    setLoading(true);
    setResult(null);
    setTimeout(() => {
      setLoading(false);
      setResult(DUMMY_STORY[mode]);
    }, 2500);
  };

  return (
    <>
      <Header />
      <main className="min-h-screen pt-24 pb-16 px-6" style={{ background: 'var(--ink)' }}>
        <div className="max-w-4xl mx-auto">
          <div className="mb-12">
            <div className="flex items-center gap-3 mb-3">
              <p className="section-tag">Brand Story</p>
              <span className="px-2 py-0.5 bg-red-600 text-white text-[10px] font-bold rounded-sm animate-pulse">유료</span>
            </div>
            <h1 className="section-heading text-[clamp(28px,4vw,48px)] text-parchment mb-4">브랜드 스토리</h1>
            <div className="deco-line w-16" />
          </div>

          {/* Mode selection */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-8">
            {[
              {
                key: 'rebrand' as Mode,
                title: '중국 맞춤 리브랜딩',
                titleCn: '品牌重塑',
                desc: '기존 브랜드 스토리를 중국 소비자 문화와 트렌드에 맞게 재해석합니다.',
              },
              {
                key: 'new' as Mode,
                title: '신규 브랜딩',
                titleCn: '全新品牌',
                desc: '처음부터 중국 시장을 위한 완전히 새로운 브랜드 아이덴티티를 제작합니다.',
              },
            ].map((item) => (
              <button
                key={item.key}
                onClick={() => {
                  setMode(item.key);
                  setResult(null); // 모드 변경 시 결과 초기화
                }}
                className="glass-card p-8 text-left transition-all hover:border-gold/40"
                style={{
                  borderColor: mode === item.key ? 'rgba(201,168,76,.6)' : undefined,
                  background: mode === item.key ? 'rgba(201,168,76,.06)' : undefined,
                }}
              >
                <div className="flex justify-between items-start mb-3">
                  <h3 className="font-noto font-medium text-parchment/90">{item.title}</h3>
                  <span className="font-notosc text-xs text-parchment/30">{item.titleCn}</span>
                </div>
                <p className="text-xs text-parchment/45 leading-relaxed font-noto font-light">{item.desc}</p>
                {mode === item.key && (
                  <div className="mt-4 flex items-center gap-2 text-gold text-xs font-noto">
                    <span className="w-1.5 h-1.5 bg-gold rounded-full" />
                    선택됨
                  </div>
                )}
              </button>
            ))}
          </div>

          {/* Input Fields based on Mode */}
          {mode && (
            <div className="glass-card p-8 mb-8 opacity-0 animate-fadeUp">
              <div className="space-y-6">
                {/* 공통 입력 필드: 브랜드명 */}
                <div>
                  <label className="section-tag block mb-2">브랜드명 (또는 기업명)</label>
                  <input
                    value={brandName}
                    onChange={(e) => setBrandName(e.target.value)}
                    placeholder={mode === 'rebrand' ? "현재 사용 중인 브랜드명을 입력하세요" : "신규 브랜드의 가칭 또는 기업명을 입력하세요"}
                    className="w-full bg-white/5 border border-gold/20 px-4 py-3 text-sm text-parchment/80 placeholder-parchment/25 font-noto outline-none focus:border-gold/50 transition-colors"
                    style={{ borderRadius: 2 }}
                  />
                </div>

                {/* 리브랜딩 모드일 때 나타나는 필수 분석 항목 */}
                {mode === 'rebrand' && (
                  <div className="opacity-0 animate-fadeIn">
                    <label className="section-tag block mb-2 italic text-gold/80">기존 브랜드 분석 항목 (필수)</label>
                    <textarea
                      value={brandDesc}
                      onChange={(e) => setBrandDesc(e.target.value)}
                      rows={4}
                      placeholder="기존 브랜드의 핵심 가치, 주력 제품, 현재 한국 내 타겟 고객층 등을 상세히 입력해 주세요. 이를 바탕으로 중국화(Localization)를 진행합니다."
                      className="w-full bg-white/5 border border-gold/20 px-4 py-3 text-sm text-parchment/80 placeholder-parchment/25 font-noto outline-none focus:border-gold/50 transition-colors resize-none"
                      style={{ borderRadius: 2 }}
                    />
                  </div>
                )}

                {/* 신규 브랜딩 모드일 때 나타나는 필수 분석 항목 */}
                {mode === 'new' && (
                  <div className="opacity-0 animate-fadeIn">
                    <label className="section-tag block mb-2 italic text-gold/80">희망 브랜드 컨셉 분석 (필수)</label>
                    <textarea
                      value={targetConcept}
                      onChange={(e) => setTargetConcept(e.target.value)}
                      rows={4}
                      placeholder="지향하는 브랜드 이미지(예: 프리미엄, 친환경, 테크니컬), 주력 진출 카테고리, 경쟁사 벤치마킹 대상을 입력해 주세요."
                      className="w-full bg-white/5 border border-gold/20 px-4 py-3 text-sm text-parchment/80 placeholder-parchment/25 font-noto outline-none focus:border-gold/50 transition-colors resize-none"
                      style={{ borderRadius: 2 }}
                    />
                  </div>
                )}

                <button 
                  onClick={generate} 
                  disabled={!brandName.trim()}
                  className={`btn-primary w-full md:w-auto ${!brandName.trim() ? 'opacity-50 cursor-not-allowed' : ''}`}
                >
                  브랜드 스토리 생성
                </button>
              </div>
            </div>
          )}

          {loading && (
            <div className="glass-card p-12 text-center">
              <div className="flex items-center justify-center gap-3 mb-4">
                {[0,1,2].map((i) => <div key={i} className="w-2 h-2 bg-gold rounded-full animate-bounce" style={{ animationDelay: `${i*0.15}s` }} />)}
              </div>
              <p className="text-sm text-parchment/50 font-noto">AI가 중국 시장 트렌드를 분석하여 브랜드 스토리를 작성하고 있습니다...</p>
            </div>
          )}

          {result && (
            <div className="glass-card p-10 opacity-0 animate-fadeUp">
              <div className="flex items-center gap-3 mb-8">
                <p className="section-tag">생성된 브랜드 스토리</p>
                <div className="deco-line flex-1" />
              </div>
              <h2 className="font-cormorant text-4xl font-light text-gold mb-2">{result.headline}</h2>
              <p className="font-noto text-sm text-parchment/50 mb-8">{result.subheadline}</p>
              <div className="deco-line mb-8 w-24" />
              <p className="text-sm text-parchment/70 leading-relaxed font-noto font-light whitespace-pre-line mb-8">{result.story}</p>
              <div className="flex flex-wrap gap-2">
                {result.tags.map((t) => (
                  <span key={t} className="px-3 py-1 text-xs border border-gold/20 text-gold/60 font-notosc" style={{ borderRadius: 2 }}>{t}</span>
                ))}
              </div>
            </div>
          )}
        </div>
      </main>
      <Footer />
      <ChatbotButton />
    </>
  );
}