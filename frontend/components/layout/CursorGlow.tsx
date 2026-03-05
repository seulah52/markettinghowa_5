// 더미데이터
'use client';
import { useEffect, useRef } from 'react';

export default function CursorGlow() {
  const dotRef  = useRef<HTMLDivElement>(null);
  const ringRef = useRef<HTMLDivElement>(null);
  const pos = useRef({ x: 0, y: 0 });
  const ring = useRef({ x: 0, y: 0 });

  useEffect(() => {
    const onMove = (e: MouseEvent) => {
      pos.current = { x: e.clientX, y: e.clientY };
      if (dotRef.current) {
        dotRef.current.style.left = e.clientX + 'px';
        dotRef.current.style.top  = e.clientY + 'px';
      }
    };

    let raf: number;
    const lerp = (a: number, b: number, t: number) => a + (b - a) * t;
    const tick = () => {
      ring.current.x = lerp(ring.current.x, pos.current.x, 0.12);
      ring.current.y = lerp(ring.current.y, pos.current.y, 0.12);
      if (ringRef.current) {
        ringRef.current.style.left = ring.current.x + 'px';
        ringRef.current.style.top  = ring.current.y + 'px';
      }
      raf = requestAnimationFrame(tick);
    };
    tick();

    window.addEventListener('mousemove', onMove);
    return () => { window.removeEventListener('mousemove', onMove); cancelAnimationFrame(raf); };
  }, []);

  return (
    <>
      {/* Dot */}
      <div ref={dotRef} className="pointer-events-none fixed z-[9997] w-2 h-2 bg-gold rounded-full -translate-x-1/2 -translate-y-1/2 mix-blend-difference transition-none" />
      {/* Lagging ring */}
      <div ref={ringRef} className="pointer-events-none fixed z-[9996] w-10 h-10 border border-gold/40 rounded-full -translate-x-1/2 -translate-y-1/2 transition-none" />
    </>
  );
}
