'use client';
import { useState, useEffect } from 'react';
import Link from 'next/link';
import Image from 'next/image';

const NAV_ITEMS = [
  { label: '시장 분석', href: '/analysis', children: [ { label: '중국 시장 분석', href: '/analysis' }, { label: '키워드 트렌드', href: '/analysis#trend' }, { label: '분석 레포트', href: '/analysis#report' } ] },
  { label: '브랜드 스토리', href: '/branding', children: [ { label: '브랜드 스토리 제작', href: '/branding' }, { label: '리브랜딩', href: '/branding#rebrand' } ] },
  { label: '홍보물 제작', href: '/marketing', children: [ { label: '이미지 제작', href: '/marketing' }, { label: '마케팅 문구 추천', href: '/marketing#copy' } ] },
  { label: '왕홍 매칭', href: '/wanghong', children: [ { label: '왕홍 추천', href: '/wanghong' }, { label: '상세 정보', href: '/wanghong#proposal' } ] },
];

export default function Header() {
  const [scrolled, setScrolled] = useState(false);
  const [menuOpen, setMenuOpen] = useState(false);

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 40);
    window.addEventListener('scroll', onScroll);
    return () => window.removeEventListener('scroll', onScroll);
  }, []);

  return (
    <header
      className="fixed top-0 left-0 right-0 z-50 transition-all duration-500"
      style={{
        height: 72,
        background: 'var(--ink)',
        borderBottom: scrolled ? '1px solid rgba(201,168,76,.15)' : '1px solid transparent',
        backdropFilter: 'blur(16px)',
      }}
    >
      <div className="max-w-7xl mx-auto h-full px-6 flex items-center justify-between">

        {/* Logo Section - 아이콘 + 텍스트 로고 나란히 */}
        <Link href="/" className="flex items-center gap-3 group">

          {/* 첫 번째 로고 아이콘 - 호버 시 회전 */}
          <div className="relative w-8 h-8 flex-shrink-0 transition-transform duration-700 ease-in-out group-hover:rotate-[360deg]">
            <Image
              src="/images/markettinghowa_logo_icon.png"
              alt="마케팅화 아이콘"
              fill
              className="object-contain"
            />
          </div>

          {/* 두 번째 텍스트 로고 이미지 */}
          <div className="relative h-7 w-40 flex-shrink-0">
            <Image
              src="/images/markettinghowa_logo_text.png"
              alt="MARKETTINGHOWA"
              fill
              className="object-contain object-left"
            />
          </div>

        </Link>

        {/* Center Nav */}
        <nav className="hidden md:flex items-center gap-1">
          {NAV_ITEMS.map((item) => (
            <div key={item.label} className="nav-item relative px-1">
              <Link
                href={item.href}
                className="hover-line relative px-4 py-2 text-xs tracking-[.15em] uppercase font-noto font-medium text-parchment/90 hover:text-gold transition-colors duration-300 flex items-center gap-1.5"
              >
                {item.label}
                <svg className="w-2.5 h-2.5 opacity-50" fill="none" viewBox="0 0 8 5">
                  <path d="M1 1l3 3 3-3" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
                </svg>
              </Link>

              {/* Dropdown */}
              <div className="nav-dropdown z-50 rounded-b-md shadow-xl border border-gold/10" style={{ background: 'var(--ink)' }}>
                {item.children.map((child) => (
                  <Link
                    key={child.label}
                    href={child.href}
                    className="block px-5 py-3 text-xs tracking-[.1em] text-parchment/70 hover:text-red-deep hover:bg-gold/5 transition-all duration-200"
                  >
                    {child.label}
                  </Link>
                ))}
              </div>
            </div>
          ))}
        </nav>

        {/* Right CTA */}
        <div className="hidden md:flex items-center gap-4">
          <Link href="/analysis" className="btn-primary text-xs font-bold px-6 py-3 rounded-sm shadow-brand transition-transform hover:scale-105">
            무료 분석 시작
            <svg className="w-3.5 h-3.5 ml-2" fill="none" viewBox="0 0 16 16">
              <path d="M3 8h10M9 4l4 4-4 4" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
          </Link>
        </div>

        {/* Mobile menu button */}
        <button
          className="md:hidden flex flex-col gap-1.5 p-2"
          onClick={() => setMenuOpen(!menuOpen)}
        >
          <span className={`block w-6 h-px bg-gold transition-all duration-300 ${menuOpen ? 'rotate-45 translate-y-2' : ''}`} />
          <span className={`block w-6 h-px bg-gold transition-all duration-300 ${menuOpen ? 'opacity-0' : ''}`} />
          <span className={`block w-6 h-px bg-gold transition-all duration-300 ${menuOpen ? '-rotate-45 -translate-y-2' : ''}`} />
        </button>
      </div>

      {/* Mobile menu */}
      {menuOpen && (
        <div className="md:hidden absolute top-full left-0 right-0 border-t border-gold/15 py-4 shadow-2xl" style={{ background: 'var(--ink)' }}>
          {NAV_ITEMS.map((item) => (
            <div key={item.label} className="border-b border-gold/5 last:border-none">
              <Link href={item.href} className="block px-6 py-4 text-xs tracking-[.15em] uppercase text-parchment font-bold" onClick={() => setMenuOpen(false)}>
                {item.label}
              </Link>
              <div className="bg-black/5 pb-2">
                {item.children.map((c) => (
                  <Link key={c.label} href={c.href} className="block px-10 py-2.5 text-xs text-parchment/60 hover:text-gold" onClick={() => setMenuOpen(false)}>
                    {c.label}
                  </Link>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}
    </header>
  );
}