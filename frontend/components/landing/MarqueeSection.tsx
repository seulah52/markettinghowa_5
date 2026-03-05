// 더미데이터
export default function MarqueeSection() {
  const platforms = ['小红书', '淘宝', '百度指数', '抖音', '天猫', '微信', '京东', '微博'];
  const keywords  = ['왕홍 매칭', '시장 분석', '브랜딩', '홍보물 제작', '실시간', 'AI 분석', '수출 전략', '트렌드 리포트'];

  return (
    <section className="relative py-0 overflow-hidden border-y border-gold/10" style={{ background: 'rgba(201,168,76,.04)' }}>
      {/* Row 1 — platforms */}
      <div className="flex items-center py-4 border-b border-gold/10">
        <div className="flex animate-marquee whitespace-nowrap gap-0">
          {[...platforms, ...platforms].map((p, i) => (
            <span key={i} className="flex items-center gap-6 px-8 font-notosc text-sm text-gold/50 hover:text-gold transition-colors">
              <span className="w-1 h-1 rounded-full bg-gold/30 inline-block" />
              {p}
            </span>
          ))}
        </div>
      </div>

      {/* Row 2 — service keywords, reverse */}
      <div className="flex items-center py-4">
        <div className="flex animate-marqueeRev whitespace-nowrap gap-0">
          {[...keywords, ...keywords].map((k, i) => (
            <span key={i} className="flex items-center gap-6 px-8 font-noto text-xs tracking-[.18em] text-parchment/30 uppercase hover:text-parchment/60 transition-colors">
              <span className="w-1 h-1 bg-orange/50 inline-block rotate-45" />
              {k}
            </span>
          ))}
        </div>
      </div>
    </section>
  );
}
