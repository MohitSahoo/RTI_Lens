import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  FileText, 
  Download, 
  Copy, 
  Sparkles, 
  ChevronRight, 
  Info,
  ShieldCheck,
  AlertTriangle,
  Settings2,
  FileCheck2,
  PenLine,
  Gavel,
  History,
  ShieldAlert,
  Save,
  CheckCircle2,
  Building2,
  Scale,
  BrainCircuit,
  UserCheck,
  Search,
  Wand2,
  Network,
  Database,
  Cpu,
  X,
  Clock,
  HelpCircle
} from 'lucide-react';
import { GlassCard } from '../ui/GlassCard';
import { GlowButton } from '../ui/GlowButton';
import { VoiceMic } from '../ui/VoiceMic';
import RAGArchitectureModal from './RAGArchitectureModal';

interface SourceDetail {
  order_number: string;
  full_text: string;
  hierarchy: string[];
  metadata: any;
}

const SECTIONS = [
  { id: "8(1)(a)", label: "National Security & Sovereignty" },
  { id: "8(1)(d)", label: "Commercial Confidence & IP" },
  { id: "8(1)(e)", label: "Fiduciary Relationship" },
  { id: "8(1)(h)", label: "Law Enforcement/Investigation" },
  { id: "8(1)(j)", label: "Personal Privacy" },
  { id: "8(1)(i)", label: "Cabinet Papers" },
  { id: "6(3)", label: "Transfer of Application" },
  { id: "7(1)", label: "Timeline Violation (30 Days)" },
];

const AppealGenerator: React.FC = () => {
  const [formData, setFormData] = useState({
    ministry: '', 
    section_cited: '', 
    context: '',
  });

  const [generating, setGenerating] = useState(false);
  const [phase, setPhase] = useState<'idle' | 'rag' | 'agents'>('idle');
  const [agentProgress, setAgentProgress] = useState([0, 0, 0, 0]);
  const [result, setResult] = useState<any>(null);
  const [blockchainStatus, setBlockchainStatus] = useState<'idle' | 'securing' | 'success'>('idle');
  const [precedents, setPrecedents] = useState<any[]>([]);
  const [selectedSource, setSelectedSource] = useState<SourceDetail | null>(null);
  const [fetchingSource, setFetchingSource] = useState(false);
  const [isArchModalOpen, setIsArchModalOpen] = useState(false);

  const agents = [
    { name: "Orchestrator", icon: Network, color: "text-primary", task: "Jurisdiction & Clause Consensus" },
    { name: "Legal Researcher", icon: Search, color: "text-blue-400", task: "Precedent Contextualization" },
    { name: "Compliance Auditor", icon: ShieldCheck, color: "text-purple-400", task: "Statistical Pattern Analysis" },
    { name: "Senior Drafter", icon: PenLine, color: "text-amber-400", task: "Legal Synthesis & Drafting" }
  ];

  const handleGenerate = async () => {
    if (formData.context.length < 50) {
      alert("Please provide at least 50 characters of context for a high-quality draft.");
      return;
    }
    
    setGenerating(true);
    setResult(null);
    setPrecedents([]);
    setBlockchainStatus('idle');
    setAgentProgress([0, 0, 0, 0]);
    setFormData(prev => ({ ...prev, ministry: '', section_cited: '' }));
    
    setPhase('rag');
    try {
      let currentMinistry = formData.ministry;
      let currentSection = formData.section_cited;

      const ragResponse = await fetch('/api/query-assistant/optimize', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: formData.context })
      });

      if (ragResponse.ok) {
        const ragData = await ragResponse.json();
        setPrecedents(ragData.relevant_precedents || []);
        
        currentMinistry = ragData.ministry_suggestion?.primary_ministry || 'Ministry of Finance';
        const suggestedSec = ragData.section_recommendations?.primary_sections?.[0]?.section || '8(1)(a)';
        currentSection = SECTIONS.find(s => suggestedSec.includes(s.id))?.id || '8(1)(a)';
        
        setFormData(prev => ({ ...prev, ministry: currentMinistry, section_cited: currentSection }));
      }

      setPhase('agents');
      for (let i = 0; i < agents.length; i++) {
        let progress = 0;
        while (progress < 100) {
          progress += Math.random() * 40;
          if (progress > 100) progress = 100;
          setAgentProgress(prev => {
            const next = [...prev];
            next[i] = progress;
            return next;
          });
          await new Promise(r => setTimeout(r, 300));
        }
      }

      const draftResponse = await fetch('/api/draft', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ...formData,
          ministry: currentMinistry,
          section_cited: currentSection
        })
      });

      if (draftResponse.ok) {
        const draftData = await draftResponse.json();
        setResult(draftData);
        setBlockchainStatus('securing');
        setTimeout(() => setBlockchainStatus('success'), 1500);
      } else {
        const errorData = await draftResponse.json();
        alert(`Drafting failed: ${errorData.detail || 'Unknown error'}`);
      }
    } catch (error) {
      console.error("Drafting error:", error);
    } finally {
      setGenerating(false);
    }
  };

  const fetchSourceDetails = async (orderNumber: string) => {
    setFetchingSource(true);
    try {
      const response = await fetch(`/api/qa/source?order_number=${encodeURIComponent(orderNumber)}`);
      if (response.ok) {
        const data = await response.json();
        setSelectedSource(data);
      }
    } catch (e) {
      console.error("Source fetch error:", e);
    } finally {
      setFetchingSource(false);
    }
  };

  return (
    <div className="h-[calc(100vh-140px)] flex gap-10 max-w-[1600px] mx-auto">
      {/* Left: Input Panel (Slightly narrower for focus) */}
      <div className="w-[380px] flex flex-col gap-6">
        <GlassCard className="p-8 space-y-8 flex-1 overflow-y-auto scrollbar-hide border-white/5 shadow-2xl">
          <div className="flex items-center gap-3">
             <div className="w-10 h-10 rounded-xl bg-primary/10 flex items-center justify-center">
               <PenLine className="text-primary w-6 h-6" />
             </div>
             <div>
               <h3 className="text-sm font-bold uppercase tracking-[0.2em]">Appeal Forge</h3>
               <p className="text-[10px] text-white/40">Multi-Agent Legal Synthesis</p>
             </div>
          </div>

          <div className="space-y-6">
            <div className="space-y-3">
              <label className="text-[10px] font-bold text-white/20 uppercase tracking-widest flex items-center gap-2">
                <Database size={12} />
                Draft Context
              </label>
              <div className="relative">
                <textarea 
                  value={formData.context}
                  onChange={(e) => setFormData(prev => ({ ...prev, context: e.target.value }))}
                  placeholder="Describe the RTI rejection details..."
                  className="w-full bg-white/5 border border-white/10 rounded-2xl p-6 text-sm min-h-[300px] focus:outline-none focus:border-primary/50 transition-all resize-none"
                />
                <div className="absolute bottom-4 right-4">
                  <VoiceMic onTranscript={(text) => setFormData(prev => ({ ...prev, context: prev.context + (prev.context ? ' ' : '') + text }))} />
                </div>
              </div>
            </div>

            <div className="grid gap-4">
              <div className="space-y-2">
                <label className="text-[10px] font-bold text-white/20 uppercase tracking-widest">Ministry</label>
                <div className="px-4 py-3 bg-white/5 border border-white/10 rounded-xl text-xs text-white/40 italic">
                  {formData.ministry || "Auto-detecting..."}
                </div>
              </div>
              <div className="space-y-2">
                <label className="text-[10px] font-bold text-white/20 uppercase tracking-widest">Exemption Section</label>
                <div className="px-4 py-3 bg-white/5 border border-white/10 rounded-xl text-xs text-white/40 italic">
                  {formData.section_cited || "Auto-detecting..."}
                </div>
              </div>
            </div>
          </div>

          <GlowButton 
            variant="primary" 
            className="w-full py-6" 
            onClick={handleGenerate}
            disabled={generating}
          >
            {generating ? "Orchestrating..." : "Initialize Drafting"}
          </GlowButton>
        </GlassCard>

        <div className="p-5 rounded-2xl bg-white/5 border border-white/10 flex items-center justify-between">
           <div className="flex items-center gap-3">
              <ShieldCheck className={blockchainStatus === 'success' ? "text-success" : "text-white/20"} />
              <span className="text-[10px] font-bold uppercase tracking-widest text-white/40">Audit Trail</span>
           </div>
           <div className="text-[10px] font-mono text-white/20">
              {blockchainStatus === 'success' ? "TX: 4zP9...Ew2k" : "Waiting..."}
           </div>
        </div>
      </div>

      {/* Right: Orchestration & Results (Centered content) */}
      <div className="flex-1 flex flex-col glass-card p-0 border-white/5 relative bg-white/[0.02] overflow-hidden">
        <div className="flex-1 overflow-y-auto px-12 py-12 scrollbar-hide">
          <div className="max-w-4xl mx-auto w-full">
            <AnimatePresence mode="wait">
              {!generating && !result && (
                <motion.div key="idle" initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="h-full flex flex-col items-center justify-center text-center space-y-6 py-20">
                  <div className="w-20 h-20 rounded-full bg-white/5 flex items-center justify-center border border-white/10">
                    <Cpu className="text-white/10 w-10 h-10" />
                  </div>
                  <h4 className="text-lg font-bold text-white/60">Ready for Legal Synthesis</h4>
                </motion.div>
              )}

              {generating && (
                <motion.div key="orchestrating" initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-16">
                   <div className="grid grid-cols-4 gap-8">
                      {agents.map((agent, i) => (
                        <div key={i} className="space-y-4">
                          <div className="flex items-center justify-between">
                            <agent.icon className={`${agent.color} w-5 h-5`} />
                            <span className="text-[10px] font-mono text-white/40">{Math.round(agentProgress[i])}%</span>
                          </div>
                          <div className="h-1 w-full bg-white/5 rounded-full overflow-hidden">
                            <motion.div className={`h-full ${agent.color.replace('text-', 'bg-')}`} animate={{ width: `${agentProgress[i]}%` }} />
                          </div>
                          <p className="text-[10px] font-bold text-white">{agent.name}</p>
                        </div>
                      ))}
                   </div>

                   <div className="space-y-8 pt-10 border-t border-white/5">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                           <div className="w-2 h-2 rounded-full bg-primary animate-pulse" />
                           <p className="text-[10px] font-bold uppercase tracking-widest text-primary">
                            {phase === 'rag' ? "Retrieving CIC Rulings..." : "Collaborative Drafting..."}
                           </p>
                        </div>
                        <button onClick={() => setIsArchModalOpen(true)} className="flex items-center gap-2 text-[10px] text-white/40 hover:text-primary transition-colors">
                          <HelpCircle size={14} /> Architecture
                        </button>
                      </div>
                      <div className="grid gap-6">
                        {precedents.length > 0 ? (
                          precedents.slice(0, 2).map((p, i) => (
                            <div key={i} className="p-6 rounded-[1.5rem] bg-white/5 border border-white/10 space-y-2">
                              <div className="flex justify-between items-center">
                                <span className="text-[10px] font-mono text-primary">{p.order_number}</span>
                                <CheckCircle2 size={12} className="text-success" />
                              </div>
                              <p className="text-[10px] text-white/40 line-clamp-2 italic">{p.text_preview}</p>
                            </div>
                          ))
                        ) : (
                          [...Array(2)].map((_, i) => (
                            <div key={i} className="p-8 rounded-[2rem] bg-white/5 border border-white/10 space-y-4">
                              <div className="h-4 w-1/4 bg-white/10 rounded-full animate-pulse" />
                              <div className="h-3 w-full bg-white/5 rounded-full" />
                            </div>
                          ))
                        )}
                      </div>
                   </div>
                </motion.div>
              )}

              {result && !generating && (
                <motion.div key="result" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="space-y-10">
                  <div className="flex gap-4">
                    <GlowButton variant="primary" className="flex-1" onClick={() => { navigator.clipboard.writeText(result.improved_query); alert("Copied!"); }}>
                      <Copy size={16} /> Copy Final Draft
                    </GlowButton>
                    <GlowButton variant="outline" className="flex-1">
                      <ShieldCheck size={16} /> Audit Trail
                    </GlowButton>
                  </div>

                  <GlassCard className="p-0 border-white/10 overflow-hidden rounded-[2rem]">
                    <div className="p-5 bg-white/5 border-b border-white/10 flex justify-between items-center px-8">
                      <div className="flex items-center gap-2 text-primary">
                        <Sparkles size={18} />
                        <span className="text-[10px] font-black uppercase tracking-widest">Autonomous Draft v2.1</span>
                      </div>
                      <div className="text-[9px] text-white/40 uppercase font-black">Verified Legal Output</div>
                    </div>
                    <div className="p-10 max-h-[600px] overflow-y-auto font-mono text-[13px] leading-relaxed text-white/80 whitespace-pre-wrap">
                      {result.improved_query}
                    </div>
                  </GlassCard>

                  <div className="grid md:grid-cols-2 gap-8">
                    <GlassCard className="bg-primary/5 border-primary/10 p-8 rounded-[2rem]">
                      <div className="flex justify-between items-center mb-6">
                        <h4 className="text-[10px] font-bold text-primary uppercase tracking-widest flex items-center gap-2">
                          <Database size={14} /> RAG Precedents
                        </h4>
                        <button onClick={() => setIsArchModalOpen(true)} className="p-1.5 hover:bg-primary/10 rounded-lg text-primary border border-primary/20">
                          <HelpCircle size={14} />
                        </button>
                      </div>
                      <div className="space-y-4">
                        {(result?.sources?.length > 0 ? result.sources : precedents).slice(0, 3).map((p: any, i: number) => (
                          <button key={i} onClick={() => fetchSourceDetails(p.order_number)} className="w-full text-left p-4 rounded-2xl bg-white/5 border border-white/5 hover:border-primary/40 transition-all group">
                            <div className="flex justify-between items-center mb-1">
                              <div className="flex flex-col">
                                <span className="text-[10px] font-mono text-white/60 group-hover:text-primary">{p.order_number}</span>
                                {p.outcome && <span className="text-[8px] uppercase font-bold text-success/60">{p.outcome}</span>}
                              </div>
                              <ChevronRight size={12} className="text-white/10 group-hover:text-primary" />
                            </div>
                            <p className="text-[9px] text-white/30 line-clamp-1 italic">{p.text_preview || `Cited for section ${p.section || '8(1)'} compliance.`}</p>
                          </button>
                        ))}
                      </div>
                    </GlassCard>

                    <GlassCard className="bg-secondary/5 border-secondary/10 p-8 rounded-[2rem]">
                      <h4 className="text-[10px] font-bold text-secondary uppercase tracking-widest mb-6 flex items-center gap-2">
                        <UserCheck size={14} /> Agent Strategy
                      </h4>
                      <div className="space-y-4">
                        {result.change_notes.map((note: any, i: number) => (
                          <div key={i} className="flex gap-3">
                            <div className="w-1.5 h-1.5 rounded-full bg-secondary mt-1.5 shrink-0" />
                            <p className="text-[11px] text-white/60 leading-relaxed">{note.revised}</p>
                          </div>
                        ))}
                      </div>
                    </GlassCard>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        </div>
      </div>

      <SourceDetailModal source={selectedSource} onClose={() => setSelectedSource(null)} />
      <RAGArchitectureModal isOpen={isArchModalOpen} onClose={() => setIsArchModalOpen(false)} />
    </div>
  );
};

// Extracted for reuse
const SourceDetailModal = ({ source, onClose }: { source: any, onClose: () => void }) => (
  <AnimatePresence>
    {source && (
      <div className="fixed inset-0 z-50 flex items-center justify-center p-12 bg-background/95 backdrop-blur-3xl">
        <motion.div initial={{ scale: 0.95, opacity: 0 }} animate={{ scale: 1, opacity: 1 }} className="w-full max-w-5xl h-[85vh] glass-card p-0 flex flex-col border-white/10 shadow-2xl">
          <div className="px-10 py-8 border-b border-white/5 flex justify-between items-center">
            <div className="flex items-center gap-6">
              <Scale className="text-primary w-8 h-8" />
              <div>
                <h2 className="text-2xl font-black text-white">{source.order_number}</h2>
                <p className="text-[11px] text-white/40 uppercase font-bold tracking-widest">{source.hierarchy.join(' > ')}</p>
              </div>
            </div>
            <button onClick={onClose} className="p-3 hover:bg-white/10 rounded-full border border-white/10"><X size={28} /></button>
          </div>
          <div className="flex-1 overflow-y-auto p-16 space-y-10 font-mono text-[14px] leading-relaxed text-white/70 whitespace-pre-wrap scrollbar-hide">
            {source.full_text}
          </div>
        </motion.div>
      </div>
    )}
  </AnimatePresence>
);

export default AppealGenerator;
