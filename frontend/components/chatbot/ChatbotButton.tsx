'use client';

import { useState, useRef, useEffect } from 'react';

interface Message {
  role: 'user' | 'assistant';
  content: string;
}

export default function ChatbotButton() {
  const [open, setOpen] = useState(false);
  const [messages, setMessages] = useState<Message[]>([
    { role: 'assistant', content: '안녕하세요! 마케띵호와 AI 컨설턴트입니다. 무엇을 도와드릴까요?' },
  ]);
  const [input, setInput] = useState('');
  const [typing, setTyping] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, typing]);

  // 🔥 채팅 내역 초기화 함수
  const resetChat = () => {
    setMessages([
      { role: 'assistant', content: '안녕하세요! 마케띵호와 AI 컨설턴트입니다. 무엇을 도와드릴까요?' },
    ]);
    setInput('');
    setTyping(false);
  };

  // 🔥 창을 닫을 때 실행되는 핸들러
  const handleClose = () => {
    setOpen(false);
    resetChat();
  };

  const send = async () => {
    const text = input.trim();
    if (!text || typing) return;

    const userMessage: Message = { role: 'user', content: text };
    setMessages((prev) => [...prev, userMessage]);
    setInput('');
    setTyping(true);

    try {
      const response = await fetch('/api/v1/chatbot/stream', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: text,
          history: messages.slice(-6), 
        }),
      });

      if (!response.body) return;
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let assistantMsg = "";

      setMessages((prev) => [...prev, { role: 'assistant', content: "" }]);

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value);
        const lines = chunk.split('\n');

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = line.slice(6);
            if (data === '[DONE]') break;
            try {
              const parsed = JSON.parse(data);
              assistantMsg += parsed.content;
              setMessages((prev) => {
                const updated = [...prev];
                updated[updated.length - 1].content = assistantMsg;
                return updated;
              });
            } catch (e) {
              console.error("JSON Parse Error", e);
            }
          }
        }
      }
    } catch (error) {
      console.error("Chat API Error:", error);
      setMessages((prev) => [...prev, { role: 'assistant', content: "서버 통신에 실패했습니다. 다시 시도해주세요." }]);
    } finally {
      setTyping(false);
    }
  };

  return (
    <>
      {/* 챗봇 창 */}
      {open && (
        <div className="fixed bottom-24 right-6 w-[360px] h-[540px] flex flex-col z-50 border border-white/10 shadow-2xl overflow-hidden"
          style={{ background: '#0d0d0d', borderRadius: '4px' }}>
          
          {/* Header */}
          <div className="flex items-center justify-between px-5 py-4 border-b border-white/5 bg-[#141414]">
            <div className="flex items-center gap-3">
              <div className="w-2.5 h-2.5 bg-[#C9A84C] rounded-full animate-pulse" />
              <p className="text-sm font-bold text-white tracking-widest">MARKETTINGHOWA AI AGENT</p>
            </div>
            {/* 🔥 onClick에 handleClose 연결 */}
            <button onClick={handleClose} className="text-white/40 hover:text-white">
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          {/* 메시지 영역 */}
          <div className="flex-1 overflow-y-auto p-5 space-y-6 bg-[#0d0d0d]">
            {messages.map((m, i) => (
              <div key={i} className={`flex ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                <div className={`max-w-[85%] p-4 text-xs leading-relaxed ${
                  m.role === 'user' ? 'bg-[#C8102E] text-white' : 'bg-[#1a1a1a] text-white/90 border border-white/5'
                }`} style={{ borderRadius: '4px' }}>
                  {m.content}
                </div>
              </div>
            ))}
            <div ref={bottomRef} />
          </div>

          {/* 입력창 */}
          <div className="p-4 bg-[#141414] border-t border-white/5 flex gap-2">
            <input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && send()}
              disabled={typing}
              placeholder={typing ? "에이전트가 생각 중입니다..." : "중국에 가구 수출을 위해 필요한 요소는?"}
              className="flex-1 bg-[#1a1a1a] border border-white/10 px-4 py-3 text-xs text-white outline-none focus:border-[#C9A84C]/50 transition-all"
            />
            <button
              onClick={send}
              disabled={typing}
              className="w-12 h-12 flex items-center justify-center bg-[#333] hover:bg-[#444] transition-all"
              style={{ borderRadius: '2px' }}
            >
              <svg className="w-5 h-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14 5l7 7m0 0l-7 7m7-7H3" />
              </svg>
            </button>
          </div>
        </div>
      )}

      {/* 플로팅 버튼 */}
      <button
        onClick={() => {
          // 🔥 열려있을 때 누르면(닫을 때) 초기화 로직 실행
          if (open) handleClose();
          else setOpen(true);
        }}
        className={`fixed bottom-6 right-6 w-14 h-14 flex items-center justify-center z-50 transition-all duration-300 ${open ? 'bg-[#1a1a1a]' : 'bg-[#C8102E]'}`}
        style={{ borderRadius: '4px', boxShadow: '0 8px 32px rgba(200, 16, 46, 0.3)' }}
      >
        {open ? (
          <svg className="w-6 h-6 text-[#C9A84C]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        ) : (
          <svg className="w-6 h-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
          </svg>
        )}
      </button>
    </>
  );
}