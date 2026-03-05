'use client';

import Header from '@/components/layout/Header';
import Footer from '@/components/layout/Footer';
import CursorGlow from '@/components/layout/CursorGlow';
import ChatbotButton from '@/components/chatbot/ChatbotButton';
import HeroSection from '@/components/landing/HeroSection';
import MarqueeSection from '@/components/landing/MarqueeSection';
import ServicesSection from '@/components/landing/ServicesSection';
import ProcessSection from '@/components/landing/ProcessSection';
import StatsSection from '@/components/landing/StatsSection';
import CtaSection from '@/components/landing/CtaSection';

export default function Home() {
  return (
    <>
      <CursorGlow />
      <Header />
      <main>
        <HeroSection />
        <MarqueeSection />
        
        <ServicesSection />
        <ProcessSection />
        <StatsSection />
        <CtaSection />
      </main>
      <Footer />
      <ChatbotButton />
    </>
  );
}
