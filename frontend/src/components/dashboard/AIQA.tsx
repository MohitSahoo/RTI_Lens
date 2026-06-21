import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Send, 
  Sparkles, 
  RotateCcw,
  ShieldCheck,
  X,
  Scale,
  BrainCircuit,
  HelpCircle,
  Gavel,
  Volume2,
  Database,
  Cpu,
  Layers,
  Clock,
  Zap
} from 'lucide-react';
import { VoiceMic } from '../ui/VoiceMic';
import RAGArchitectureModal from './RAGArchitectureModal';

type SearchMode = 'bm25' | 'semantic' | 'hybrid';

interface RetrievalInfo {
  search_mode: SearchMode;
  bm25_results: number;
  semantic_results: number;
  final_sources: number;
  retrieval_time_s: number;
  vector_search_active: boolean;
}

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  citations?: any[];
  confidence?: number;
  timestamp: number;
  retrieval_info?: RetrievalInfo;
}

interface SourceDetail {
  order_number: string;
  full_text: string;
  hierarchy: string[];
  metadata: any;
}

const renderContent = (content: string) => {
  let html = content.replace(/\*\*(.*?)\*\*/g, '<strong class="text-primary">$1</strong>');
  html = html.replace(/^\d+\.\s+(.*)$/gm, '<div class="flex gap-2 mb-2"><span class="text-primary font-bold">•</span><span>$1</span></div>');
  html = html.replace(/\n/g, '<br/>');
  return <div dangerouslySetInnerHTML={{ __html: html }} />;
};

const SEARCH_MODES: { value: SearchMode; label: string; icon: React.ReactNode; description: string; color: string }[] = [
  {
    value: 'bm25',
    label: 'BM25',
    icon: <Database size={13} />,
    description: 'Keyword lexical search',
    color: 'text-amber-400 border-amber-400/40 bg-amber-400/10'
  },
  {
    value: 'semantic',
    label: 'Semantic',
    icon: <Cpu size={13} />,
    description: 'Vector similarity search',
    color: 'text-violet-400 border-violet-400/40 bg-violet-400/10'
  },
  {
    value: 'hybrid',
    label: 'Hybrid',
    icon: <Layers size={13} />,
    description: 'BM25 + Semantic fusion',
    color: 'text-primary border-primary/40 bg-primary/10'
  }
];

const SearchModeBadge: React.FC<{ info: RetrievalInfo }> = ({ info }) => {
  const mode = SEARCH_MODES.find(m => m.value === info.search_mode) ?? SEARCH_MODES[2];
  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.9 }}
      animate={{ opacity: 1, scale: 1 }}
      className="flex items-center gap-2 flex-wrap mt-2"
    >
      {/* Search mode chip */}
      <div className={`flex items-center gap-1.5 px-2.5 py-1 rounded-full border text-[10px] font-black uppercase tracking-widest ${mode.color}`}>
        {mode.icon}
        {mode.label} Search
      </div>

      {/* BM25 hit count */}
      {info.bm25_results > 0 && (
        <div className="flex items-center gap-1 px-2 py-1 rounded-full border border-amber-400/20 bg-amber-400/5 text-[10px] text-amber-400/70 font-bold">
          <Database size={9} />
          {info.bm25_results} BM25 hits
        </div>
      )}

      {/* Semantic hit count */}
      {info.semantic_results > 0 && (
        <div className="flex items-center gap-1 px-2 py-1 rounded-full border border-violet-400/20 bg-violet-400/5 text-[10px] text-violet-400/70 font-bold">
          <Cpu size={9} />
          {info.semantic_results} semantic hits
        </div>
      )}

      {/* Retrieval timing */}
      <div className="flex items-center gap-1 px-2 py-1 rounded-full border border-white/10 bg-white/5 text-[10px] text-white/40 font-bold">
        <Clock size={9} />
        {info.retrieval_time_s}s retrieval
      </div>

      {/* Atlas indicator */}
      {info.vector_search_active && (
        <div className="flex items-center gap-1 px-2 py-1 rounded-full border border-green-400/20 bg-green-400/5 text-[10px] text-green-400/70 font-bold">
          <Zap size={9} />
          Atlas Vector
        </div>
      )}
    </motion.div>
  );
};

const AIQA: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      role: 'assistant',
      content: "Hello! I'm your RTI-Lens AI assistant. Ask me about specific sections, ministries, or case strategies. I'm connected to the verified CIC archive.",
      timestamp: Date.now()
    }
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [loadingStage, setLoadingStage] = useState('');
  const [searchMode, setSearchMode] = useState<SearchMode>('hybrid');
  const [selectedSource, setSelectedSource] = useState<SourceDetail | null>(null);
  const [fetchingSource, setFetchingSource] = useState(false);
  const [isArchModalOpen, setIsArchModalOpen] = useState(false);
  const [playingId, setPlayingId] = useState<string | null>(null);
  const chatEndRef = useRef<HTMLDivElement>(null);
  const audioRef = useRef<HTMLAudioElement | null>(null);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);

  const handleSend = async (overrideInput?: string) => {
    const text = overrideInput || input;
    if (!text.trim()) return;
    
    setLoading(true);
    setLoadingStage('Retrieving documents...');
    const userMsg: Message = { id: Date.now().toString(), role: 'user', content: text, timestamp: Date.now() };
    setMessages(prev => [...prev, userMsg]);
    setInput('');

    try {
      // Animate loading stages
      const stages = [
        { msg: `Running ${searchMode === 'hybrid' ? 'BM25 + Semantic' : searchMode.toUpperCase()} search...`, delay: 400 },
        { msg: 'Scoring & ranking chunks...', delay: 1200 },
        { msg: 'Generating answer with Groq...', delay: 2200 },
      ];
      stages.forEach(({ msg, delay }) =>
        setTimeout(() => setLoadingStage(msg), delay)
      );

      const response = await fetch('/api/qa', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question: text, top_k: 4, search_mode: searchMode })
      });
      const data = await response.json();
      const aiMsg: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: data.answer,
        timestamp: Date.now(),
        citations: data.sources || [],
        confidence: data.confidence_score || (data.confidence === 'high' ? 0.95 : 0.75),
        retrieval_info: data.retrieval_info
      };
      setMessages(prev => [...prev, aiMsg]);
    } catch (error) {
      console.error("QA error:", error);
    } finally {
      setLoading(false);
      setLoadingStage('');
    }
  };

  const handleSpeak = async (text: string, msgId: string) => {
    if (playingId === msgId) {
      audioRef.current?.pause();
      setPlayingId(null);
      return;
    }

    setPlayingId(msgId);
    try {
      const response = await fetch('/api/voice/speak', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: text.replace(/<[^>]*>?/gm, '') })
      });

      if (response.ok) {
        const blob = await response.blob();
        const url = URL.createObjectURL(blob);
        if (audioRef.current) {
          audioRef.current.src = url;
          audioRef.current.play();
          audioRef.current.onended = () => setPlayingId(null);
        } else {
          const audio = new Audio(url);
          audioRef.current = audio;
          audio.play();
          audio.onended = () => setPlayingId(null);
        }
      }
    } catch (error) {
      console.error("TTS error:", error);
      setPlayingId(null);
    }
  };

  const fetchSourceDetails = async (orderNumber: string) => {
    setFetchingSource(true);
    try {
      const response = await fetch(`/api/qa/source?order_number=${encodeURIComponent(orderNumber)}`);
      if (response.ok) {
        const data = await response.json();
        setSelectedSource(data);
      } else {
        alert("Precedent mapping failed.");
      }
    } catch (e) {
      console.error("Source fetch error:", e);
    } finally {
      setFetchingSource(false);
    }
  };

  const activeMode = SEARCH_MODES.find(m => m.value === searchMode)!;

  return (
    <div className="h-[calc(100vh-140px)] flex flex-col items-center">
      <div className="w-full max-w-5xl h-full flex flex-col glass-card p-0 overflow-hidden border-white/5 relative shadow-2xl">
        
        {/* Header */}
        <div className="px-10 py-5 border-b border-white/5 bg-white/5 flex justify-between items-center">
          <div className="flex items-center gap-4">
            <div className="w-10 h-10 rounded-xl bg-primary/10 flex items-center justify-center border border-primary/20">
              <BrainCircuit className="text-primary w-6 h-6" />
            </div>
            <div>
              <h3 className="text-lg font-bold text-white tracking-tight">Legal Intelligence System</h3>
              <div className="flex items-center gap-2">
                <div className="w-1.5 h-1.5 rounded-full bg-success animate-pulse" />
                <p className="text-[10px] text-white/40 uppercase font-black tracking-widest">RAG Engine Online</p>
              </div>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <button 
              onClick={() => setIsArchModalOpen(true)}
              className="p-2.5 hover:bg-primary/10 rounded-xl text-primary hover:text-white transition-all border border-primary/20 flex items-center gap-2"
              title="View RAG Architecture"
            >
              <HelpCircle size={16} />
              <span className="text-[10px] font-bold uppercase">Architecture</span>
            </button>
            <button 
              onClick={() => setMessages([{ id: '1', role: 'assistant', content: "Chat cleared.", timestamp: Date.now() }])}
              className="p-2.5 hover:bg-white/10 rounded-xl text-white/40 transition-all"
            >
              <RotateCcw size={16} />
            </button>
          </div>
        </div>

        {/* Search Mode Toggle */}
        <div className="px-10 py-3 border-b border-white/5 bg-white/[0.02] flex items-center gap-4">
          <span className="text-[10px] text-white/30 font-black uppercase tracking-widest whitespace-nowrap">Search Mode</span>
          <div className="flex items-center gap-1.5 p-1 rounded-xl bg-white/5 border border-white/10">
            {SEARCH_MODES.map(mode => (
              <button
                key={mode.value}
                id={`search-mode-${mode.value}`}
                onClick={() => setSearchMode(mode.value)}
                title={mode.description}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-[11px] font-bold uppercase tracking-wider transition-all ${
                  searchMode === mode.value
                    ? `${mode.color} shadow-lg`
                    : 'text-white/30 hover:text-white/60 hover:bg-white/5'
                }`}
              >
                {mode.icon}
                {mode.label}
              </button>
            ))}
          </div>
          <span className="text-[10px] text-white/25 italic">{activeMode.description}</span>
        </div>

        {/* Message Stream */}
        <div className="flex-1 overflow-y-auto px-10 py-12 scrollbar-hide">
          <div className="max-w-3xl mx-auto space-y-12">
            <AnimatePresence>
              {messages.map((msg) => (
                <motion.div 
                  key={msg.id}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
                >
                  <div className={`max-w-[85%] space-y-3 ${msg.role === 'user' ? 'items-end' : 'items-start'}`}>
                    {msg.role === 'assistant' && msg.confidence && (
                      <div className="flex items-center gap-2 px-3 py-1 rounded-full bg-white/5 border border-white/10 w-fit">
                        <div className={`w-1.5 h-1.5 rounded-full ${msg.confidence > 0.8 ? 'bg-success' : 'bg-amber-500'} animate-pulse`} />
                        <span className="text-[9px] font-black text-white/50 uppercase tracking-widest">Confidence: {(msg.confidence * 100).toFixed(0)}%</span>
                        <button 
                          onClick={() => handleSpeak(msg.content, msg.id)}
                          className={`ml-2 p-1 rounded-full transition-all ${playingId === msg.id ? 'bg-primary text-background' : 'hover:bg-white/10 text-white/40'}`}
                        >
                          <Volume2 size={10} className={playingId === msg.id ? 'animate-pulse' : ''} />
                        </button>
                      </div>
                    )}

                    <div className={`p-6 rounded-[1.5rem] leading-relaxed text-sm shadow-lg ${
                      msg.role === 'user' 
                        ? 'bg-primary text-background font-semibold neo-glow rounded-tr-none' 
                        : 'bg-white/5 border border-white/10 text-white/90 rounded-tl-none backdrop-blur-xl'
                    }`}>
                      {msg.role === 'assistant' ? renderContent(msg.content) : msg.content}
                    </div>

                    {/* Retrieval info badge (assistant only) */}
                    {msg.role === 'assistant' && msg.retrieval_info && (
                      <SearchModeBadge info={msg.retrieval_info} />
                    )}

                    {/* Citations */}
                    {msg.role === 'assistant' && msg.citations && msg.citations.length > 0 && (
                      <div className="flex flex-wrap gap-2">
                        {msg.citations.map((cite, i) => (
                          <button key={i} onClick={() => fetchSourceDetails(cite.order_number)} className="px-3 py-1.5 rounded-lg bg-primary/10 border border-primary/20 text-primary text-[10px] font-bold hover:bg-primary/20 transition-all flex items-center gap-2">
                            <Gavel size={12} /> {cite.order_number}
                          </button>
                        ))}
                      </div>
                    )}
                  </div>
                </motion.div>
              ))}

              {/* Loading indicator with stage */}
              {loading && (
                <div className="flex justify-start">
                  <div className="bg-white/5 border border-white/10 p-5 rounded-2xl flex items-center gap-3">
                    <motion.div animate={{ rotate: 360 }} transition={{ repeat: Infinity, duration: 1, ease: "linear" }} className="w-4 h-4 border-2 border-primary border-t-transparent rounded-full flex-shrink-0" />
                    <div>
                      <AnimatePresence mode="wait">
                        <motion.span
                          key={loadingStage}
                          initial={{ opacity: 0, y: 4 }}
                          animate={{ opacity: 1, y: 0 }}
                          exit={{ opacity: 0, y: -4 }}
                          className="text-xs text-white/50 italic block"
                        >
                          {loadingStage || 'Initialising...'}
                        </motion.span>
                      </AnimatePresence>
                      <div className={`flex items-center gap-1 mt-1 ${activeMode.color}`}>
                        {activeMode.icon}
                        <span className="text-[9px] font-black uppercase tracking-wider">{activeMode.label} mode</span>
                      </div>
                    </div>
                  </div>
                </div>
              )}
              <div ref={chatEndRef} />
            </AnimatePresence>
          </div>
        </div>

        {/* Input Area */}
        <div className="p-10 border-t border-white/5 bg-background/40 backdrop-blur-xl">
          <div className="max-w-3xl mx-auto">
            <div className="relative group">
              <input 
                type="text" 
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleSend()}
                placeholder="Query the legal engine (e.g., 'Precedents on Section 8(1)(j) in Railways')" 
                className="w-full bg-white/5 border border-white/10 rounded-2xl py-5 pl-8 pr-32 text-sm focus:outline-none focus:border-primary/50 transition-all"
              />
              <div className="absolute right-3 top-1/2 -translate-y-1/2 flex items-center gap-2">
                <VoiceMic onTranscript={(text) => setInput(prev => prev + (prev ? ' ' : '') + text)} />
                <button onClick={() => handleSend()} disabled={loading} className="bg-primary text-background p-3 rounded-xl neo-glow hover:scale-105 transition-all disabled:opacity-50">
                  <Send size={20} />
                </button>
              </div>
            </div>
            <div className="flex justify-center gap-8 mt-6 opacity-30">
               <div className="flex items-center gap-2 text-[10px] font-bold uppercase tracking-widest"><ShieldCheck size={12} /> Verified Engine</div>
               <div className="flex items-center gap-2 text-[10px] font-bold uppercase tracking-widest"><Scale size={12} /> Legal Compliance</div>
            </div>
          </div>
        </div>
      </div>

      <RAGArchitectureModal isOpen={isArchModalOpen} onClose={() => setIsArchModalOpen(false)} />

      {/* Source Detail Modal */}
      <AnimatePresence>
        {selectedSource && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-12 bg-background/90 backdrop-blur-2xl">
            <motion.div initial={{ scale: 0.95, opacity: 0 }} animate={{ scale: 1, opacity: 1 }} className="w-full max-w-4xl h-[80vh] glass-card p-0 flex flex-col border-white/10">
              <div className="px-8 py-6 border-b border-white/5 flex justify-between items-center bg-white/5">
                <div className="flex items-center gap-4">
                  <Scale className="text-primary w-8 h-8" />
                  <div>
                    <h2 className="text-xl font-bold text-white">{selectedSource.order_number}</h2>
                    <p className="text-[10px] text-white/40 uppercase font-black">{selectedSource.hierarchy.join(' > ')}</p>
                  </div>
                </div>
                <button onClick={() => setSelectedSource(null)} className="p-2 hover:bg-white/10 rounded-full"><X size={24} /></button>
              </div>
              <div className="flex-1 overflow-y-auto p-12 space-y-8 font-mono text-xs leading-relaxed text-white/70 whitespace-pre-wrap">
                {selectedSource.full_text}
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default AIQA;
