import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Send, 
  Mic, 
  Paperclip, 
  Sparkles, 
  History, 
  BookOpen, 
  ChevronRight,
  ExternalLink,
  MessageSquare,
  ThumbsUp,
  ThumbsDown,
  RotateCcw
} from 'lucide-react';
import { GlassCard } from '../ui/GlassCard';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  citations?: any[];
  confidence?: number;
}

const AIQA: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      role: 'assistant',
      content: "Hello! I'm your RTI-Lens AI assistant. I've analyzed over 700 CIC rulings and can help you navigate RTI laws, find precedents, or strategize your appeals. What can I help you with today?",
    }
  ]);
  const [input, setInput] = useState('');

  const suggestedPrompts = [
    "Can Section 8(1)(j) deny salary information?",
    "Find CIC rulings related to pension disputes.",
    "What are successful second appeal arguments?"
  ];

  const handleSend = async () => {
    if (!input.trim()) return;
    
    const userMsg: Message = { id: Date.now().toString(), role: 'user', content: input };
    setMessages(prev => [...prev, userMsg]);
    const currentInput = input;
    setInput('');

    const loadingId = (Date.now() + 1).toString();
    setMessages(prev => [...prev, {
      id: loadingId,
      role: 'assistant',
      content: "Analyzing legal precedents..."
    }]);

    try {
      const response = await fetch('/api/qa', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ question: currentInput, top_k: 3 })
      });
      
      if (!response.ok) {
        throw new Error('Network response was not ok');
      }
      
      const data = await response.json();
      
      const aiMsg: Message = {
        id: loadingId,
        role: 'assistant',
        content: data.answer,
        citations: data.sources ? data.sources.map((src: any) => ({
          title: src.order_number,
          snippet: src.text ? src.text.substring(0, 100) + "..." : "No context snippet available."
        })) : [],
        confidence: data.confidence === 'high' ? 0.95 : data.confidence === 'medium' ? 0.75 : 0.45
      };

      setMessages(prev => prev.map(msg => msg.id === loadingId ? aiMsg : msg));
    } catch (error) {
      console.error("Error fetching QA:", error);
      setMessages(prev => prev.map(msg => 
        msg.id === loadingId 
          ? { ...msg, content: "Sorry, I encountered an error connecting to the RTI backend. Please ensure the API is running." } 
          : msg
      ));
    }
  };

  return (
    <div className="h-[calc(100vh-140px)] flex gap-6">
      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col glass-card p-0 overflow-hidden border-white/5">
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          <AnimatePresence>
            {messages.map((msg) => (
              <motion.div
                key={msg.id}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <div className={`max-w-[80%] ${msg.role === 'user' ? 'bg-primary/20 border border-primary/20' : 'bg-white/5 border border-white/10'} p-4 rounded-2xl`}>
                  <div className="flex items-center gap-2 mb-2">
                    {msg.role === 'assistant' ? (
                      <div className="w-6 h-6 bg-primary rounded-full flex items-center justify-center">
                        <Sparkles size={12} className="text-background" />
                      </div>
                    ) : (
                      <div className="w-6 h-6 bg-white/10 rounded-full flex items-center justify-center">
                        <MessageSquare size={12} className="text-white/60" />
                      </div>
                    )}
                    <span className="text-[10px] font-bold uppercase tracking-widest text-white/40">
                      {msg.role === 'assistant' ? 'RTI-Lens Intelligence' : 'You'}
                    </span>
                    {msg.confidence && (
                      <span className="ml-auto text-[10px] font-bold text-success bg-success/10 px-2 py-0.5 rounded">
                        {Math.round(msg.confidence * 100)}% Confidence
                      </span>
                    )}
                  </div>
                  <p className="text-sm leading-relaxed text-white/90">{msg.content}</p>
                  
                  {msg.citations && (
                    <div className="mt-4 pt-4 border-t border-white/5 space-y-3">
                      <p className="text-[10px] font-bold text-white/30 uppercase tracking-widest">Sources & Citations</p>
                      {msg.citations.map((cite: any, i: number) => (
                        <div key={i} className="p-2 rounded-lg bg-background/50 border border-white/5 group cursor-pointer hover:border-primary/30 transition-all">
                          <div className="flex justify-between items-center mb-1">
                            <span className="text-xs font-bold text-primary">{cite.title}</span>
                            <ExternalLink size={10} className="text-white/20 group-hover:text-primary" />
                          </div>
                          <p className="text-[10px] text-white/40 italic">"{cite.snippet}"</p>
                        </div>
                      ))}
                    </div>
                  )}
                  
                  {msg.role === 'assistant' && (
                    <div className="mt-4 flex gap-3 text-white/20">
                      <ThumbsUp size={14} className="hover:text-success cursor-pointer" />
                      <ThumbsDown size={14} className="hover:text-danger cursor-pointer" />
                      <RotateCcw size={14} className="hover:text-primary cursor-pointer" />
                    </div>
                  )}
                </div>
              </motion.div>
            ))}
          </AnimatePresence>
        </div>

        {/* Input Area */}
        <div className="p-6 border-t border-white/5 bg-background/40">
          {messages.length === 1 && (
            <div className="flex gap-2 mb-6 overflow-x-auto pb-2 scrollbar-hide">
              {suggestedPrompts.map((p, i) => (
                <button 
                  key={i} 
                  onClick={() => setInput(p)}
                  className="whitespace-nowrap px-4 py-2 rounded-full bg-white/5 border border-white/10 text-xs text-white/50 hover:bg-white/10 hover:text-white transition-all"
                >
                  {p}
                </button>
              ))}
            </div>
          )}
          <div className="relative">
            <input 
              type="text" 
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSend()}
              placeholder="Ask about RTI laws, CIC orders, or appeal strategy..." 
              className="w-full bg-white/5 border border-white/10 rounded-xl py-4 pl-6 pr-32 text-sm focus:outline-none focus:border-primary/50 transition-all"
            />
            <div className="absolute right-2 top-1/2 -translate-y-1/2 flex gap-2">
              <button className="p-2 text-white/30 hover:text-white transition-colors"><Mic size={18} /></button>
              <button className="p-2 text-white/30 hover:text-white transition-colors"><Paperclip size={18} /></button>
              <button 
                onClick={handleSend}
                className="bg-primary text-background p-2 rounded-lg neo-glow hover:scale-105 transition-all"
              >
                <Send size={18} />
              </button>
            </div>
          </div>
          <p className="text-[10px] text-center text-white/20 mt-4 uppercase tracking-[0.2em]">
            AI can make mistakes. Verify legal citations with official gazettes.
          </p>
        </div>
      </div>

      {/* Right Intelligence Panel */}
      <div className="w-80 space-y-6">
        <GlassCard>
          <div className="flex items-center gap-2 mb-4">
            <History className="text-primary w-4 h-4" />
            <h3 className="text-sm font-bold uppercase tracking-widest">Recent Context</h3>
          </div>
          <div className="space-y-4">
            {[1, 2].map((i) => (
              <div key={i} className="p-3 rounded-xl bg-white/5 border border-white/5 group cursor-pointer hover:bg-white/10 transition-all">
                <p className="text-xs font-medium mb-1 line-clamp-1">Personal information vs Public Disclosure</p>
                <div className="flex justify-between text-[10px] text-white/30">
                  <span>Section 8(1)(j)</span>
                  <span>2m ago</span>
                </div>
              </div>
            ))}
          </div>
        </GlassCard>

        <GlassCard>
          <div className="flex items-center gap-2 mb-4">
            <BookOpen className="text-secondary w-4 h-4" />
            <h3 className="text-sm font-bold uppercase tracking-widest">Related Rulings</h3>
          </div>
          <div className="space-y-4">
            {[1, 2, 3].map((i) => (
              <div key={i} className="group cursor-pointer">
                <div className="flex justify-between items-start mb-1">
                  <span className="text-[10px] font-bold text-primary">CIC/FINANCE/2024/A</span>
                  <ChevronRight size={12} className="text-white/20 group-hover:text-primary transition-transform group-hover:translate-x-1" />
                </div>
                <p className="text-[11px] text-white/60 line-clamp-2">Disclosure of loan default information under RTI...</p>
              </div>
            ))}
          </div>
          <button className="w-full mt-6 py-2 rounded-lg bg-white/5 border border-white/10 text-[10px] font-bold uppercase tracking-widest hover:bg-white/10 transition-all">
            Full Precedent Map
          </button>
        </GlassCard>

        <div className="p-5 rounded-2xl bg-gradient-to-br from-primary/10 to-secondary/10 border border-white/10">
          <div className="flex items-center gap-2 mb-2">
            <div className="w-2 h-2 rounded-full bg-success animate-pulse" />
            <span className="text-[10px] font-bold uppercase tracking-widest">Live Legal Feed</span>
          </div>
          <p className="text-[11px] text-white/70 italic leading-relaxed">
            "CIC just released 14 new orders related to the Ministry of Railways (10:42 AM IST)"
          </p>
        </div>
      </div>
    </div>
  );
};

export default AIQA;
