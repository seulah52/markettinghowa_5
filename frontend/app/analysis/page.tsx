'use client';
import { useState, useRef } from 'react';
import html2canvas from 'html2canvas';
import jsPDF from 'jspdf';
import Header from '@/components/layout/Header';
import Footer from '@/components/layout/Footer';
import ChatbotButton from '@/components/chatbot/ChatbotButton';
import { apiClient } from '@/lib/api/client';
import Link from 'next/dist/client/link';

export default function AnalysisPage() {
  const [keyword, setKeyword] = useState('');
  const [loading, setLoading] = useState(false);
  const [report, setReport] = useState<any | null>(null);
  const [isExporting, setIsExporting] = useState(false);

  // PDF로 캡처할 영역을 지정하는 Ref
  const reportRef = useRef<HTMLDivElement>(null);

  const runAnalysis = async () => {
    if (!keyword.trim()) return;
    setLoading(true);
    setReport(null);
    try {
      const res = await apiClient.analysis.run({ keyword });
      if (res.success) {
        setReport(res.data);
      } else {
        alert('분석에 실패했습니다.');
      }
    } catch (error) {
      console.error('Analysis error:', error);
      const msg =
        error && typeof (error as Error).message === 'string' && (error as Error).message.includes('fetch')
          ? '백엔드에 연결할 수 없습니다. Vercel 환경 변수 NEXT_PUBLIC_API_URL 확인 후 재배포해 주세요.'
          : '서버 통신 중 오류가 발생했습니다.';
      alert(msg);
    } finally {
      setLoading(false);
    }
  };

  const downloadPDF = async () => {
    if (!reportRef.current) return;
    
    setIsExporting(true);
    try {
      const element = reportRef.current;
      const canvas = await html2canvas(element, {
        scale: 2,
        useCORS: true,
        backgroundColor: '#fbfbfb',
        logging: false,
      });

      const imgData = canvas.toDataURL('image/png');
      const pdf = new jsPDF('p', 'mm', 'a4');
      const imgWidth = 210;
      const pageHeight = 297;
      const imgHeight = (canvas.height * imgWidth) / canvas.width;
      let heightLeft = imgHeight;
      let position = 0;

      pdf.addImage(imgData, 'PNG', 0, position, imgWidth, imgHeight);
      heightLeft -= pageHeight;

      while (heightLeft >= 0) {
        position = heightLeft - imgHeight;
        pdf.addPage();
        pdf.addImage(imgData, 'PNG', 0, position, imgWidth, imgHeight);
        heightLeft -= pageHeight;
      }

      pdf.save(`CHAI-NA_Market_Report_${keyword.replace(/\s/g, '_')}.pdf`);
    } catch (error) {
      console.error('PDF 생성 실패:', error);
      alert('PDF 생성 중 오류가 발생했습니다.');
    } finally {
      setIsExporting(false);
    }
  };

  // 무역 데이터 가공: 2021~2024년 데이터만 추출하여 정렬
  const getTradeStatsArray = () => {
    if (!report?.trade_stats) return [];
    return Object.entries(report.trade_stats)
      .map(([year, data]: [string, any]) => ({
        year,
        export: data.Export || 0
      }))
      .filter(item => parseInt(item.year) >= 2021 && parseInt(item.year) <= 2024)
      .sort((a, b) => parseInt(a.year) - parseInt(b.year));
  };

  return (
    <>
      <Header />
      <main className="min-h-screen pt-24 pb-16 px-6" style={{ background: 'var(--ink)' }}>
        <div className="max-w-6xl mx-auto">
          
          <div className="mb-12 text-left">
            <h1 className="section-heading text-[clamp(28px,4vw,48px)] text-parchment mb-4">시장 분석</h1>
              <div className="glass-card p-8 mb-8">
                <div>
                  <label className="section-tag block mb-3 text-left" style={{ letterSpacing: '0px', fontSize: '20px' }}>제품 정보 입력</label>
                  <div className="flex gap-3">
                    <input
                      value={keyword}
                      onChange={(e) => setKeyword(e.target.value)}
                      onKeyDown={(e) => e.key === 'Enter' && runAnalysis()}
                      placeholder="분석할 제품명 또는 제품 키워드를 입력하세요."
                      className="flex-1 bg-white/5 border border-gold/20 px-4 py-4 text-parchment outline-none focus:border-gold/60 transition-all font-noto"
                    />
                    <button onClick={runAnalysis} className={`btn-primary px-10 ${loading ? 'opacity-50 cursor-not-allowed pointer-events-none' : ''}`} disabled={loading}>
                      {loading ? '분석 중...' : '분석 시작'}
                    </button>
                  </div>
                </div>
                <div className="flex gap-4 items-center">
                </div>
              </div>
          </div>

          <div className="fixed bottom-24 right-10 z-40">
            <Link href="/branding" className="btn-primary px-8 py-4 shadow-brand rounded-full flex items-center gap-3 group">
              <span className="font-bold">다음 | 브랜드 스토리</span>
              <svg className="w-5 h-5 group-hover:translate-x-1 transition-transform" fill="none" viewBox="0 0 16 16">
                <path d="M3 8h10M9 4l4 4-4 4" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
              </svg>
            </Link>
          </div>

          {loading && (
            <div className="text-center py-20 animate-pulse">
              <p className="text-gold font-noto" style={{ letterSpacing: '0px', fontSize: '20px' }}>"{keyword}"에 대한 실시간 데이터 수집 및 AI 분석 중...</p>
              <p className="text-gold font-noto" style={{ letterSpacing: '0px', fontSize: '20px' }}>AI가 보다 정확한 정보 제공을 위해 고민 중입니다. 조금만 기다려 주세요!</p>
            </div>
          )}

          {report && (
            <div className="space-y-16 animate-fadeUp">
              
              <div ref={reportRef} className="bg-[#f6f3ea] p-12 rounded-xl shadow-2xl">
                <div className="flex justify-between items-center mb-10 border-b border-gold/20 pb-6">
                  <div className="text-left font-cormorant text-par text-x1 tracking-tight italic" style={{ fontSize: '30px' }}>종합 분석 레포트</div>
                </div>

                {/* SECTION 1. 소비자 니즈 분석 */}
                <section className="space-y-12 mb-16">
                  <h2 className="text-2xl font-bold text-parchment border-l-4 border-gold pl-4 font-cormorant tracking-widest uppercase">01. 소비자 니즈 분석</h2>
                  
                  {/* 타오바오 분석 */}
                  <div className="glass-card p-10 bg-white/5">
                    <p className="section-tag mb-8 text-gold text-base" style={{ letterSpacing: '0px',fontSize: '20px' }}>淘宝 (Taobao) 실사용 후기 분석</p>
                    {report.taobao_market_summary ? (
                      <div className="w-full">
                        <div className="text-base text-parchment/80 leading-relaxed font-noto font-light mb-10">
                          {report.taobao_market_summary}
                        </div>
                        {report.review_reactions && (
                          <div className="space-y-10">
                            <div className="flex h-6 rounded-full overflow-hidden bg-white/5">
                              <div className="bg-green-500 shadow-[0_0_15px_rgba(34,197,94,0.4)]" style={{ width: '65%' }} />
                              <div className="bg-gold opacity-80" style={{ width: '25%' }} />
                              <div className="bg-orange-600" style={{ width: '10%' }} />
                            </div>
                            <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
                              {[
                                { label: 'Positive', color: 'text-green-500', fontSize: 'text-sm', data: report.review_reactions.positive },
                                { label: 'Neutral', color: 'text-gold', fontSize: 'text-sm', data: report.review_reactions.neutral },
                                { label: 'Negative', color: 'text-orange-500', fontSize: 'text-sm', data: report.review_reactions.negative },
                              ].map(group => (
                                <div key={group.label} className="bg-white/[0.02] p-5 rounded border border-white/5">
                                  <p className={`${group.color} font-bold mb-4 text-xs uppercase tracking-widest`}>{group.label}</p>
                                  <div className="space-y-3">
                                    {group.data?.map((r: string) => (
                                      <p key={r} className="text-parchment/60 text-xs leading-snug font-light">• {r}</p>
                                    ))}
                                  </div>
                                </div>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>
                    ) : <p className="text-white/20 text-xs italic text-center py-10">데이터를 불러오지 못했습니다.</p>}
                  </div>

                  {/* 바이두 분석 */}
                  <div className="glass-card p-10 bg-white/5">
                    <p className="section-tag mb-8 text-gold text-base" style={{ letterSpacing: '0px', fontSize: '20px' }}>Baidu(百度) 지수 분석</p>
                    {report.baidu_info ? (
                      <div className="space-y-10">
                        <div className="text-base text-parchment/80 font-noto leading-relaxed font-light">
                          {report.baidu_info.summary}
                          <span className="block mt-4 text-ml text-parchment/30 font-gothic tracking-tighter italic">
                            * 데이터 집계 기간: {report.baidu_info.period}
                          </span>
                        </div>
                        
                        <div className="flex flex-col md:flex-row border-y border-white/10 py-10">
                          {/* 1. 검색량 (20%) */}
                          <div className="flex-1 px-6 text-center border-r border-white/5">
                            <p className="text-[11px] text-parchment/60 uppercase tracking-widest mb-6" style={{ letterSpacing: '0px', fontSize: '15px' }}>검색량</p>
                            <div className="inline-block bg-gold/10 px-5 py-4 rounded-lg border border-gold/20 mb-4">
                              <p className="text-3xl font-bold text-gold font-noto">
                                {report.baidu_info.index?.toLocaleString() || '-'}
                              </p>
                            </div>
                          </div>

                          {/* 2. 성별 (25%) */}
                          <div className="flex-[1.2] px-6 flex flex-col items-center border-r border-white/5">
                            <p className="text-[11px] text-parchment/60 uppercase tracking-widest mb-6" style={{ letterSpacing: '0px', fontSize: '15px' }}>성별</p>
                            <div className="flex items-center gap-6">
                              <div className="relative w-20 h-20">
                                <svg viewBox="0 0 36 36" className="w-full h-20 transform -rotate-90">
                                  <circle cx="18" cy="18" r="16" fill="transparent" stroke="rgba(255,255,255,0.05)" strokeWidth="4" />
                                  <circle 
                                    cx="18" cy="18" r="16" fill="transparent" 
                                    stroke="#3b82f6" strokeWidth="4" 
                                    strokeDasharray={`${parseInt(report.baidu_info.gender_dist?.male) || 0} 100`} 
                                  />
                                  <circle 
                                    cx="18" cy="18" r="16" fill="transparent" 
                                    stroke="#ef4444" strokeWidth="4" 
                                    strokeDasharray={`${parseInt(report.baidu_info.gender_dist?.female) || 0} 100`}
                                    strokeDashoffset={`-${parseInt(report.baidu_info.gender_dist?.male) || 0}`}
                                  />
                                </svg>
                              </div>
                              <div className="text-sm space-y-2 font-noto">
                                <div className="flex items-center gap-2">
                                  <div className="w-2 h-2 rounded-full bg-blue-500" />
                                  <span className="text-parchment font-bold text-base">{report.baidu_info.gender_dist?.male || '0%'}</span>
                                </div>
                                <div className="flex items-center gap-2">
                                  <div className="w-2 h-2 rounded-full bg-orange-500" />
                                  <span className="text-parchment font-bold text-base">{report.baidu_info.gender_dist?.female || '0%'}</span>
                                </div>
                              </div>
                            </div>
                          </div>

                          {/* 3. 연령대 (55%) */}
                          <div className="flex-[2.8] px-8 text-center">
                            <p className="text-[11px] text-parchment/60 uppercase tracking-widest mb-6" style={{ letterSpacing: '0px', fontSize: '15px' }}>연령대</p>
                            <div className="w-full space-y-5 px-2">
                              <div className="flex h-4 w-full rounded-full overflow-hidden bg-white/5 border border-white/5">
                                {report.baidu_info.age_dist && Object.entries(report.baidu_info.age_dist).map(([age, pct]: [string, any], idx) => {
                                  const colors = ['bg-slate-600', 'bg-gold/40', 'bg-gold', 'bg-gold/70', 'bg-slate-800'];
                                  return (
                                    <div 
                                      key={age} 
                                      className={`${colors[idx % colors.length]}`} 
                                      style={{ width: pct }}
                                    />
                                  );
                                })}
                              </div>
                              <div className="grid grid-cols-5 gap-2 text-white/30 font-mono">
                                {report.baidu_info.age_dist && Object.entries(report.baidu_info.age_dist).map(([age, pct]) => (
                                  <div key={age} className="text-center">
                                    <p className="text-white/60 font-bold mb-1 text-xs">{age}</p>
                                    <p className="text-gold font-bold text-base">{String(pct)}</p>
                                  </div>
                                ))}
                              </div>
                            </div>
                          </div>
                        </div>
                      </div>
                    ) : <p className="text-white/20 text-xs italic text-center py-10">데이터를 불러오지 못했습니다.</p>}
                  </div>

                  {/* 샤오홍슈 분석 */}
                  <div className="glass-card p-10 bg-white/5">
                    <p className="section-tag mb-8 text-gold text-base" style={{ letterSpacing: '0px', fontSize: '20px' }}>Xiaohongshu(小红书) 트렌드 요약</p>
                    {report.xhs_trend_summary ? (
                      <div className="space-y-10">
                        <div className="text-base text-parchment/80 font-noto leading-relaxed font-light">
                          {report.xhs_trend_summary}
                        </div>
                        
                        <div className="pt-8 border-t border-white/10">
                          <p className="text-[15px] text-gold/60 uppercase tracking-widest mb-6 text-center" style={{ letterSpacing: '0px', fontSize: '15px' }}>가장 많이 언급된 키워드</p>
                          <div className="flex flex-wrap justify-center gap-4">
                            {report.xhs_keywords && report.xhs_keywords.length > 0 ? (
                              report.xhs_keywords.slice(0, 5).map((kw: string, i: number) => (
                                <div key={kw} className="bg-white/5 px-6 py-3 rounded-full border border-white/10 flex items-center gap-3 group hover:border-gold/40 transition-all">
                                  <span className="text-gold/40 font-mono text-xs italic">#0{i+1}</span>
                                  <span className="text-parchment/80 font-noto text-sm group-hover:text-gold transition-colors">{kw}</span>
                                </div>
                              ))
                            ) : (
                              <p className="text-white/20 text-[10px] italic">분석된 키워드가 없습니다.</p>
                            )}
                          </div>
                        </div>
                      </div>
                    ) : <p className="text-white/20 text-xs italic text-center py-10">데이터를 불러오지 못했습니다.</p>}
                  </div>
                </section>

                {/* SECTION 2. 수출 동향 데이터 */}
                <section className="space-y-8 mb-16">
                  <h2 className="text-2xl font-bold text-parchment border-l-4 border-gold pl-4 font-cormorant tracking-widest uppercase">02. 수출 동향 데이터</h2>
                  <div className="glass-card p-10 bg-white/5">
                    {report.trade_stats && Object.keys(report.trade_stats).length > 0 ? (
                      <div className="mb-8">
                        <p className="section-tag mb-10 text-gold font-noto" style={{ letterSpacing: '0px',fontSize: '20px' }}>2021~2024년 수출액 추이 (단위: K, USD)</p>
                        
                        <div className="relative h-64 w-full pl-16 pr-4 mb-12">
                          <div className="h-full w-full border-l border-b border-white/10 relative">
                            {(() => {
                              const stats = getTradeStatsArray();
                              const maxVal = Math.max(...stats.map(d => d.export), 1);
                              const levels = [1, 0.75, 0.5, 0.25, 0];
                              return (
                                <div className="absolute left-[-64px] top-0 h-full w-14 z-10">
                                  {levels.map(level => (
                                    <div 
                                      key={level} 
                                      className="absolute w-full flex items-center justify-end"
                                      style={{ top: `${(1 - level) * 100}%`, transform: 'translateY(-50%)' }}
                                    >
                                      <span className="text-[9px] text-white/30 font-mono">
                                        ${Math.round(maxVal * level).toLocaleString()}K
                                      </span>
                                    </div>
                                  ))}
                                </div>
                              );
                            })()}

                            <svg className="absolute inset-0 w-full h-full overflow-visible" viewBox="0 0 100 100" preserveAspectRatio="none">
                              {[0, 25, 50, 75, 100].map(level => (
                                <line key={level} x1="0" y1={level} x2="100" y2={level} stroke="white" strokeOpacity="0.05" strokeDasharray="1" />
                              ))}
                              {(() => {
                                const stats = getTradeStatsArray();
                                if (stats.length <= 1) return null;
                                const maxExport = Math.max(...stats.map(d => d.export), 1);
                                const points = stats.map((d, i) => `${(i / (stats.length - 1)) * 100},${100 - (d.export / maxExport) * 100}`).join(' ');
                                return (
                                  <polyline fill="none" stroke="var(--gold)" strokeWidth="1.5" points={points} vectorEffect="non-scaling-stroke" className="drop-shadow-[0_0_8px_rgba(201,168,76,0.5)]" />
                                );
                              })()}
                            </svg>

                            <div className="absolute inset-0 w-full h-full pointer-events-none">
                              {(() => {
                                const stats = getTradeStatsArray();
                                const maxExport = Math.max(...stats.map(d => d.export), 1);
                                return stats.map((d, i) => {
                                  const x = (i / (stats.length - 1)) * 100;
                                  const y = 100 - (d.export / maxExport) * 100;
                                  return (
                                    <div key={i} className="absolute group pointer-events-auto cursor-help" style={{ left: `${x}%`, top: `${y}%`, transform: 'translate(-50%, -50%)' }}>
                                      <div className="w-2.5 h-2.5 bg-gold rounded-full border border-black/50 shadow-[0_0_8px_rgba(201,168,76,0.8)] transition-transform group-hover:scale-150" />
                                      <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 px-2 py-1 bg-black/90 border border-gold/30 text-gold text-[10px] font-mono rounded opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap z-50">
                                        ${d.export.toLocaleString()}K
                                      </div>
                                    </div>
                                  );
                                });
                              })()}
                            </div>
                            <div className="absolute -bottom-8 left-0 w-full flex justify-between px-0 text-[13px] text-parchment/40 font-mono">
                              {getTradeStatsArray().map(d => <span key={d.year}>{d.year}</span>)}
                            </div>
                          </div>
                        </div>

                        <div className="mt-20 p-8 bg-gold/[0.02] border border-white/5 rounded italic text-sm text-parchment/60 leading-relaxed font-light">
                          {report.export_trend_summary}
                        </div>
                      </div>
                    ) : <p className="text-white/20 text-xs italic text-center py-10">수집된 실제 무역 통계 데이터가 없습니다.</p>}
                  </div>
                </section>

                {/* SECTION 3. 관련 시장 뉴스 */}
                <section className="space-y-8 mb-16">
                  <h2 className="text-2xl font-bold text-parchment border-l-4 border-gold pl-4 font-cormorant tracking-widest uppercase">03. 관련 시장 뉴스</h2>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
                    {report.news?.news ? (
                      report.news.news.slice(0, 3).map((n: any, i: number) => (
                        <div key={i} className="glass-card p-8 bg-white/5 flex flex-col h-full border-white/5 hover:border-gold/30 transition-all">
                          <p className="text-[15px] text-gold/50 mb-4 uppercase tracking-[0.2em] font-notosc" style={{ letterSpacing: '0px', fontSize: '20px' }}>{n.source || '시장 뉴스'}</p>
                          <h3 className="text-base font-bold text-parchment mb-6 leading-snug italic">
                            "{n.title}"
                          </h3>
                          <div className="deco-line w-12 mb-6 opacity-40" />
                          <p className="text-xs text-parchment/40 leading-relaxed font-light">
                            {n.summary}
                          </p>
                        </div>
                      ))
                    ) : (
                      <div className="col-span-3 glass-card p-10 bg-white/5 text-center">
                        <p className="text-white/20 text-xs italic text-center">수집된 실제 뉴스 데이터가 없습니다.</p>
                      </div>
                    )}
                  </div>
                </section>

                {/* SECTION 4. 경쟁사 분석 */}
                <section className="space-y-8 mb-16">
                  <h2 className="text-2xl font-bold text-parchment border-l-4 border-gold pl-4 font-cormorant tracking-widest uppercase">04. 경쟁사 분석 (TOP 10)</h2>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                    <div className="glass-card p-8 bg-white/5">
                      <p className="section-tag mb-6 text-gold/60" style={{ letterSpacing: '0px',fontSize: '20px' }}>제품군 타겟 경쟁사</p>
                      {report.competitors?.keyword_competitors ? (
                        <ul className="space-y-5">
                          {report.competitors.keyword_competitors.slice(0, 5).map((c: any, i: number) => (
                            <li key={i} className="border-b border-white/5 pb-4 last:border-0">
                              <div className="flex justify-between items-center mb-2">
                                <span className="text-base text-parchment font-bold">{c.name}</span>
                                <span className="text-[10px] px-2 py-0.5 bg-gold/10 text-gold italic border border-gold/20">#{i+1}</span>
                              </div>
                              <p className="text-xs text-gold/50 mb-2 font-medium">{c.main_product} | {c.origin}</p>
                              <p className="text-xs text-parchment/40 leading-relaxed font-light italic opacity-80">"{c.description}"</p>
                            </li>
                          ))}
                        </ul>
                      ) : <p className="text-white/20 text-xs italic text-center py-10">데이터를 불러오지 못했습니다.</p>}
                    </div>
                    <div className="glass-card p-8 bg-white/5">
                      <p className="section-tag mb-6 text-gold/60" style={{ letterSpacing: '0px',fontSize: '20px' }}>산업군 타겟 경쟁사</p>
                      {report.competitors?.industry_competitors ? (
                        <ul className="space-y-5">
                          {report.competitors.industry_competitors.slice(0, 5).map((c: any, i: number) => (
                            <li key={i} className="border-b border-white/5 pb-4 last:border-0">
                              <div className="flex justify-between items-center mb-2">
                                <span className="text-base text-parchment font-bold">{c.name}</span>
                                <span className="text-[10px] px-2 py-0.5 bg-gold/10 text-gold italic border border-gold/20">#{i+1}</span>
                              </div>
                              <p className="text-xs text-gold/50 mb-2 font-medium">{c.main_product} | {c.origin}</p>
                              <p className="text-xs text-parchment/40 leading-relaxed font-light italic opacity-80">"{c.description}"</p>
                            </li>
                          ))}
                        </ul>
                      ) : <p className="text-white/20 text-xs italic text-center py-10">데이터를 불러오지 못했습니다.</p>}
                    </div>
                  </div>
                </section>

                {/* SECTION 5. 마케팅 전략 (5 Force Mindmap) */}
                <section className="space-y-8 mb-16">
                  <h2 className="text-2xl font-bold text-parchment border-l-4 border-gold pl-4 font-cormorant tracking-widest uppercase">05. 마케팅 분석 (5-Forces)</h2>
                  <div className="glass-card p-16 bg-white/5">
                    {report.five_force_analysis ? (
                      <div className="relative max-w-4xl mx-auto h-[600px]">
                        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-52 h-52 border border-gold rounded-full flex flex-col items-center justify-center text-center p-8 z-20 shadow-[0_0_30px_rgba(212,175,55,0.3)]" style={{ background: '#fbfbfb' }}>
                          <p className="text-base font-bold text-parchment">기존 경쟁자</p>
                          <p className="text-[12px] text-orange-500 mt-3 leading-tight font-medium uppercase tracking-tighter">{report.five_force_analysis.rivalry}</p>
                        </div>

                        {[
                          { pos: 'top-2 left-1/2 -translate-x-1/2', label: '신규 진입자', key: 'new_entrants', sub: '신규 위협' },
                          { pos: 'bottom-2 left-1/2 -translate-x-1/2', label: '대체품 위협', key: 'substitutes', sub: '대체 위협' },
                          { pos: 'top-1/2 left-2 -translate-y-1/2', label: '공급자 교섭력', key: 'suppliers', sub: '공급자' },
                          { pos: 'top-1/2 right-2 -translate-y-1/2', label: '구매자 교섭력', key: 'buyers', sub: '구매자' },
                        ].map(node => (
                          <div key={node.key} className={`absolute ${node.pos} w-64 p-5 border border-gold text-center shadow-2xl rounded-sm transition-all hover:border-gold/50 z-10 shadow-[0_0_30px_rgba(212,175,55,0.3)`} style={{ background: '#fbfbfb' }}>                            
                            <p className="text-sm font-bold text-parchment mb-3 tracking-tight">{node.label}</p>
                            <p className="text-[12px] text-orange/60 leading-relaxed font-light">{report.five_force_analysis[node.key]}</p>
                          </div>
                        ))}
                        
                        <svg className="absolute inset-0 w-full h-full opacity-10" style={{ pointerEvents: 'none' }}>
                          <line x1="50%" y1="0%" x2="50%" y2="100%" stroke="var(--gold)" strokeWidth="1" />
                          <line x1="0%" y1="50%" x2="100%" y2="50%" stroke="var(--gold)" strokeWidth="1" />
                        </svg>
                      </div>
                    ) : <p className="text-white/20 text-xs italic text-center py-10">데이터를 불러오지 못했습니다.</p>}
                  </div>
                </section>

                {/* SECTION 06. AI 종합 진입 전략 */}
                <section className="space-y-8 pb-10">
                  <h2 className="text-2xl font-bold text-parchment border-l-4 border-gold pl-4 font-cormorant tracking-widest uppercase">06. 종합 시장 진입 전략</h2>
                  <div className="glass-card p-12 bg-gradient-to-br from-gold/10 to-transparent border-gold/30">
                    <div className="space-y-6">
                      <p className="section-tag text-gold" style={{ letterSpacing: '0px',fontSize: '20px' }}>AI 종합 분석 데이터</p>
                      <div className="text-base text-parchment/90 font-noto leading-loose whitespace-pre-wrap">
                        {report.summary}
                      </div>
                    </div>
                  </div>
                </section>
                
                <div className="mt-10 pt-10 border-t border-gold/10 text-center text-[9px] text-white/20 uppercase tracking-[0.5em]">
                  Generated by MarketTinghowa
                </div>
              </div>

              <div className="pt-12 text-center border-t border-gold/20">
                <button 
                  onClick={downloadPDF} 
                  disabled={isExporting}
                  className={`btn-primary px-12 py-5 text-lg group transition-all ${isExporting ? 'opacity-50 cursor-not-allowed' : ''}`}
                >
                  <span className="flex items-center gap-3">
                    {isExporting ? '레포트 제작 중...' : '수출 레포트 다운받기 (PDF)'}
                    {!isExporting && (
                      <svg className="w-5 h-5 group-hover:translate-y-1 transition-transform" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                      </svg>
                    )}
                  </span>
                </button>
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
