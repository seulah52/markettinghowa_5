'use client';
import { useState } from 'react';
import Header from '@/components/layout/Header';
import Footer from '@/components/layout/Footer';
import ChatbotButton from '@/components/chatbot/ChatbotButton';
import { apiClient, ApiError } from '@/lib/api/client';
import Link from 'next/dist/client/link';

type Wanghong = {
  id: string;
  name: string;
  avatar?: string;
  followers?: string;
  growth_amount?: string;
  growth_rate?: string;
  score?: number;
  description?: string;
  reason?: string;
};

export default function WanghongPage() {
  const [keyword, setKeyword] = useState('');
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState('');
  const [count, setCount] = useState(10);
  const [results, setResults] = useState<Wanghong[] | null>(null);
  const [detailOpen, setDetailOpen] = useState(false);
  const [detailLoading, setDetailLoading] = useState(false);
  const [detailTarget, setDetailTarget] = useState<Wanghong | null>(null);
  const [detailData, setDetailData] = useState<any>(null);
  const [loginHint, setLoginHint] = useState(false);
  const [selected, setSelected] = useState<number | null>(null);
  const [proposal, setProposal] = useState<string | null>(null);
  const [proposalLoading, setProposalLoading] = useState(false);
  const [usePrevious, setUsePrevious] = useState(false);
  const [previousKeyword, setPreviousKeyword] = useState<string | null>(null);
  const [previousLoading, setPreviousLoading] = useState(false);

  const loadPrevious = async () => {
    setPreviousLoading(true);
    setStatus('');
    try {
      const data = await apiClient.wanghong.previousData();
      if (data.keyword) {
        setPreviousKeyword(data.keyword);
        setKeyword(data.keyword);
        setUsePrevious(true);
      } else {
        setStatus('이전 리서치 데이터에 키워드가 없습니다. 먼저 시장 분석을 실행해주세요.');
      }
    } catch (e) {
      setStatus('이전 데이터를 불러오지 못했습니다. 먼저 시장 분석을 실행해주세요.');
    } finally {
      setPreviousLoading(false);
    }
  };

  const switchToManual = () => {
    setUsePrevious(false);
    setPreviousKeyword(null);
    setKeyword('');
  };

  const runOneClick = async () => {
    if (!keyword.trim()) return;
    setLoading(true);
    setStatus('실시간 왕홍 데이터를 수집하고 AI가 최적 후보를 선별합니다...');
    setResults(null);
    setLoginHint(false);
    try {
      const res = await apiClient.wanghong.oneClick({ keyword, recommend_count: count, use_previous: usePrevious });
      setResults(res.recommendation || []);
      setStatus('');
    } catch (e) {
      console.error(e);
      if (e instanceof ApiError && (e.payload?.detail?.code === 'COOKIE_EXPIRED' || e.message.includes('COOKIE_EXPIRED'))) {
        setLoginHint(true);
        setStatus('로그인 세션이 만료되었습니다. 쿠키를 재발급해주세요.');
      } else {
        setStatus('오류가 발생했습니다. 콘솔 로그를 확인해주세요.');
      }
    } finally {
      setLoading(false);
    }
  };

  const openDetail = async (w: Wanghong) => {
    setDetailTarget(w);
    setDetailOpen(true);
    setDetailLoading(true);
    setDetailData(null);
    try {
      const res = await apiClient.wanghong.detailJson(w.id);
      setDetailData(res.detail);
    } catch (e) {
      console.error(e);
      setDetailData({ error: '상세 정보 조회 실패' });
    } finally {
      setDetailLoading(false);
    }
  };

  const startLogin = async () => {
    try {
      await apiClient.wanghong.loginStart();
      setStatus('브라우저가 열리면 QR 로그인 후 다시 시도해주세요.');
    } catch (e) {
      console.error(e);
      setStatus('로그인 프로세스 시작에 실패했습니다.');
    }
  };

  const genProposal = (rank: number) => {
    setSelected(rank);
    setProposal(null);
    setProposalLoading(true);
    setTimeout(() => {
      setProposalLoading(false);
      setProposal(`[광고 제안서]\n\nTo. ${results?.find((_, i) => i + 1 === rank)?.name || ''} 님\n\n안녕하세요. [브랜드명] 마케팅팀입니다.\n\n■ 협업 제안 배경\n저희 제품의 핵심 타겟층과 채널이 완벽하게 일치합니다.\n\n■ 제안 내용\n- 협업 형태: 제품 체험 리뷰 영상 (60초 내외)\n- 제작 자유도: 채널 톤앤매너 전적으로 존중\n- 게재 일정: 협의 후 결정\n\n■ 제공 혜택\n- 제품 무상 제공 (체험 세트 + 추가 증정)\n- 협찬비: 협의\n- 전용 할인코드 제공\n\n상호 윈-윈이 되는 협업을 기대합니다.\n문의: contact@chai-na.com`);
    }, 1500);
  };

  return (
    <>
      <Header />
      <main className="min-h-screen pt-24 pb-16 px-6" style={{ background: 'var(--ink)' }}>
        <div className="max-w-5xl mx-auto">
          <div className="mb-12">
            <p className="section-tag mb-3">Influencer Matching</p>
            <h1 className="section-heading text-[clamp(28px,4vw,48px)] text-parchment mb-4">왕홍 매칭</h1>
            <div className="deco-line w-16" />
          </div>

          <div className="glass-card p-8 mb-8">
            <label className="section-tag block mb-3">제품 정보 입력</label>

            {/* 이전 데이터 / 직접 입력 토글 버튼 */}
            <div className="flex gap-2 mb-4">
              <button
                onClick={loadPrevious}
                disabled={previousLoading || loading}
                className={`text-xs px-4 py-2 border transition-colors ${usePrevious ? 'border-gold/60 text-gold bg-gold/10' : 'btn-outline'}`}
                style={{ borderRadius: 2 }}
              >
                {previousLoading ? '불러오는 중...' : '이전 데이터 불러오기'}
              </button>
              <button
                onClick={switchToManual}
                disabled={loading}
                className={`text-xs px-4 py-2 border transition-colors ${!usePrevious ? 'border-gold/60 text-gold bg-gold/10' : 'btn-outline'}`}
                style={{ borderRadius: 2 }}
              >
                직접 입력
              </button>
              {usePrevious && previousKeyword && (
                <span className="text-xs text-parchment/35 font-noto self-center ml-1">
                  적용됨: <span className="text-gold/60">{previousKeyword}</span>
                </span>
              )}
            </div>

            <div className="flex flex-col md:flex-row gap-3">
              <input
                value={keyword}
                onChange={(e) => !usePrevious && setKeyword(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && !usePrevious && runOneClick()}
                placeholder={usePrevious ? '이전 데이터가 적용되었습니다.' : '제품명 또는 제품 키워드를 입력하세요.'}
                disabled={usePrevious}
                className={`flex-1 border px-4 py-3 text-sm font-noto outline-none transition-colors ${
                  usePrevious
                    ? 'bg-white/2 border-white/8 text-parchment/35 cursor-not-allowed'
                    : 'bg-white/5 border-gold/20 text-parchment/80 placeholder-parchment/25 focus:border-gold/50'
                }`}
                style={{ borderRadius: 2 }}
              />
              <div className="flex gap-3">
                <select
                  value={count}
                  onChange={(e) => setCount(parseInt(e.target.value))}
                  className="bg-white/5 border border-white/10 px-3 py-3 text-sm text-parchment/80 outline-none focus:border-gold/50"
                  style={{ borderRadius: 2, backgroundColor: 'var(--ink)', color: 'var(--parchment)' }}
                >
                  {[5, 10, 15, 20].map((n) => (
                    <option key={n} value={n} style={{ backgroundColor: 'var(--ink)', color: 'var(--parchment)' }}>
                      {n}명 추천
                    </option>
                  ))}
                </select>
                <button onClick={runOneClick} className="btn-primary" disabled={loading || (!keyword.trim() && !usePrevious)}>
                  {loading ? '왕홍 찾는 중...' : '왕홍 찾기'}
                </button>
              </div>
            </div>
            {status && <p className="mt-4 text-xs text-parchment/40 font-noto">{status}</p>}
            {loginHint && (
              <div className="mt-4 flex flex-col sm:flex-row gap-3">
                <button onClick={startLogin} className="btn-outline text-xs px-4 py-2">
                  쿠키 재발급(로그인) 시작
                </button>
                <p className="text-xs text-parchment/30 font-noto">
                  로그인 완료 후 다시 “원클릭 실행”을 눌러주세요.
                </p>
              </div>
            )}
          </div>

          <div className="fixed bottom-24 right-10 z-40">
            <Link href="/contact" className="btn-outline bg-white/10 backdrop-blur-md px-10 py-4 shadow-brand rounded-full flex items-center gap-3 group border-gold/50">
              <span className="font-bold text-gold">프로젝트 문의하기</span>
              <svg className="w-5 h-5 group-hover:scale-110 transition-transform" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
              </svg>
            </Link>
          </div>

          {loading && (
            <div className="glass-card p-12 text-center">
              <div className="flex items-center justify-center gap-3 mb-4">
                {[0,1,2].map((i) => <div key={i} className="w-2 h-2 bg-gold rounded-full animate-bounce" style={{ animationDelay: `${i*0.15}s` }} />)}
              </div>
              <p className="text-sm text-parchment/50 font-noto">왕홍 정보를 수집하고 있습니다...</p>
            </div>
          )}

          {results && results.length === 0 && (
            <div className="glass-card p-12 text-center">
              <p className="text-sm text-parchment/50 font-noto">추천 결과가 없습니다. 키워드를 바꿔 다시 시도해보세요.</p>
            </div>
          )}

          {results && results.length > 0 && (
            <div className="animate-fadeUp">
              <p className="section-tag mb-4">검색 결과 — {keyword}</p>
              <div className="space-y-3 mb-8">
                {results.map((w, i) => (
                  <div key={w.id} className="glass-card p-6 flex items-center justify-between gap-4">
                    <div className="flex items-center gap-5">
                      <span className="stat-number text-2xl w-8 text-center">{i + 1}</span>
                      <div className="deco-line-v h-10" />
                      {w.avatar ? (
                        <img src={w.avatar} alt={w.name} className="w-12 h-12 rounded-full border border-gold/20 object-cover shrink-0" />
                      ) : (
                        <div className="w-12 h-12 rounded-full border border-gold/20 bg-white/5 shrink-0" />
                      )}
                      <div>
                        <p className="font-notosc text-base text-parchment/90 mb-1">{w.name}</p>
                        <div className="flex items-center gap-3 text-xs text-parchment/35 font-noto">
                          <span>팔로워 {w.followers || '-'}</span>
                          <span className="w-1 h-1 bg-parchment/20 rounded-full" />
                          <span className="text-gold/70">팔로워 증가율 {w.growth_rate || '-'}</span>
                          <span className="w-1 h-1 bg-parchment/20 rounded-full" />
                          <span>점수 {typeof w.score === 'number' ? w.score : '-'}</span>
                        </div>
                        {w.reason && (
                          <p className="text-xs text-parchment/40 font-noto mt-1 max-w-md line-clamp-2">{w.reason}</p>
                        )}
                      </div>
                    </div>
                    <div className="flex items-center gap-3 shrink-0">
                      <div className="text-center">
                        <p className="stat-number text-xl">{typeof w.score === 'number' ? w.score : '-'}</p>
                        <p className="text-[10px] text-parchment/30 font-noto">매칭 점수</p>
                      </div>
                      <div className="flex flex-col gap-2">
                        <button onClick={() => openDetail(w)} className="btn-outline text-xs px-4 py-2">
                          상세 정보
                        </button>
                        <button onClick={() => genProposal(i + 1)} className="btn-outline text-xs px-4 py-2">
                          제안서 작성
                        </button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>

              {selected && proposalLoading && (
                <div className="glass-card p-8 text-center">
                  <div className="flex items-center justify-center gap-3 mb-3">
                    {[0,1,2].map((i) => <div key={i} className="w-2 h-2 bg-gold rounded-full animate-bounce" style={{ animationDelay: `${i*0.15}s` }} />)}
                  </div>
                  <p className="text-sm text-parchment/50 font-noto">광고 제안서를 작성하고 있습니다...</p>
                </div>
              )}

              {proposal && (
                <div className="glass-card p-8 opacity-0 animate-fadeUp">
                  <div className="flex items-center gap-3 mb-6">
                    <p className="section-tag">자동 생성 광고 제안서</p>
                    <div className="deco-line flex-1" />
                    <span className="text-xs text-parchment/30 font-noto">#{selected}위 왕홍 대상</span>
                  </div>
                  <pre className="text-sm text-parchment/65 leading-relaxed font-noto font-light whitespace-pre-wrap">{proposal}</pre>
                  <div className="flex gap-3 mt-6">
                    <button className="btn-primary text-xs">제안서 다운로드</button>
                    <button className="btn-outline text-xs">컨택 자동화 (준비 중)</button>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </main>
      <Footer />
      <ChatbotButton />

      {detailOpen && (
        <div className="fixed inset-0 z-[100] flex items-center justify-center p-6 bg-#gold_lt/80 backdrop-blur-xs">
          <div className="glass-card w-full max-w-2xl p-8 max-h-[80vh] overflow-y-auto border-gold/30">
            <div className="flex items-center gap-3 mb-6">
              <p className="section-tag">상세 정보</p>
              <div className="deco-line flex-1" />
              <button onClick={() => { setDetailOpen(false); setDetailTarget(null); setDetailData(null); }} className="btn-outline text-xs px-4 py-2">
                닫기
              </button>
            </div>

            {detailLoading && (
              <div className="text-sm text-parchment/50 items-center justify-centerfont-noto">상세 정보를 로딩 중입니다...</div>
            )}

            {!detailLoading && detailData?.error && (
              <div className="text-sm text-red-400">{detailData.error}</div>
            )}

            {!detailLoading && detailData && !detailData.error && (
              <div className="space-y-6">

                {/* 프로필 이미지 */}
                {(detailData['프로필 이미지'] || detailTarget?.avatar) && (
                  <div className="flex justify-center">
                    <img
                      src={detailData['프로필 이미지'] || detailTarget?.avatar}
                      alt="프로필"
                      className="w-20 h-20 rounded-full border-2 border-gold/30 object-cover"
                    />
                  </div>
                )}

                {/* 견적 항목 — key에 '报价' 포함된 것들 */}
                {Object.entries(detailData).some(([k]) => k.includes('报价')) && (
                  <div>
                    <p className="text-xs text-gold/70 font-bold tracking-widest uppercase mb-3">견적</p>
                    <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 text-center">
                      {Object.entries(detailData)
                        .filter(([k, v]) => k.includes('报价') && String(v).trim() !== '' && String(v) !== '-')
                        .map(([k, v]) => {
                          const raw = String(v);
                          const numMatch = raw.match(/[\d,\.]+/);
                          const displayVal = numMatch ? `¥${numMatch[0]}` : raw;
                          return (
                            <div key={k} className="bg-white/5 p-3 rounded border border-gold/10">
                              <p className="text-[10px] text-parchment/40 mb-1">{k.replace('报价_', '')}</p>
                              <p className="text-sm text-gold font-bold">{displayVal}</p>
                            </div>
                          );
                        })}
                    </div>
                  </div>
                )}

                {/* 구분선 */}
                {Object.entries(detailData).some(([k]) => k.includes('报价')) && (
                  <div className="border-t border-white/10" />
                )}

                {/* 개요 — 나머지 항목 */}
                <div>
                  <p className="text-xs text-gold/70 font-bold tracking-widest uppercase mb-3">개요</p>
                  <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 text-center">
                    {Object.entries(detailData)
                      .filter(([k, v]) =>
                        k !== '프로필 이미지' &&
                        k !== '소개' &&
                        !k.includes('报价') &&
                        String(v).trim() !== '' &&
                        String(v) !== '-'
                      )
                      .map(([k, v]) => {
                        const isLong = String(v).length > 40;
                        return isLong ? (
                          <div key={k} className="col-span-2 sm:col-span-3 bg-white/5 p-3 rounded border border-white/10 text-left">
                            <p className="text-[10px] text-parchment/40 mb-1">{k}</p>
                            <p className="text-sm text-parchment/80 whitespace-pre-wrap leading-relaxed">{String(v)}</p>
                          </div>
                        ) : (
                          <div key={k} className="bg-white/5 p-3 rounded border border-white/10">
                            <p className="text-[10px] text-parchment/40 mb-1">{k}</p>
                            <p className="text-sm text-gold font-bold">{String(v)}</p>
                          </div>
                        );
                      })}
                  </div>
                </div>

              </div>
            )}
          </div>
        </div>
      )}
    </>
  );
}
