import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  X, 
  Search, 
  Database, 
  BrainCircuit, 
  ShieldCheck, 
  Share2, 
  Cpu, 
  Network,
  Activity,
  Layers,
  Zap,
  ChevronRight,
  ExternalLink,
  Code,
  Box,
  Server,
  Workflow,
  BarChart3,
  TrendingUp,
  Map,
  FileText
} from 'lucide-react';
import { GlassCard } from '../ui/GlassCard';

interface RAGArchitectureModalProps {
  isOpen: boolean;
  onClose: () => void;
}

const RAGArchitectureModal: React.FC<RAGArchitectureModalProps> = ({ isOpen, onClose }) => {
  const serviceNodes = [
    {
      id: "API_Q",
      title: "Intelligent Q&A",
      tech: "Hybrid RAG (BM25 + MV)",
      desc: "Connects to MongoDB Vector store for semantic retrieval and BM25 for strict keyword indexing of 70k+ paragraphs.",
      color: "text-blue-400",
      icon: Search
    },
    {
      id: "API_P",
      title: "Outcome Predictor",
      tech: "Gradient Boosting ML",
      desc: "Trained on 10,000+ historical rulings to predict case success probability with dynamic impact factor analysis.",
      color: "text-primary",
      icon: TrendingUp
    },
    {
      id: "API_G",
      title: "Knowledge Graph",
      tech: "Entity Mapping (FS)",
      desc: "Visualizes legal relationships between ministries, sections, and case outcomes using high-dimensional feature space.",
      color: "text-purple-400",
      icon: Map
    },
    {
      id: "API_A",
      title: "Appeal Generator",
      tech: "Multi-Agent PG",
      desc: "Orchestrates 4 specialized agents to synthesize legal grounds and integrate verified precedents into final drafts.",
      color: "text-amber-400",
      icon: FileText
    }
  ];

  return (
    <AnimatePresence>
      {isOpen && (
        <div className="fixed inset-0 z-[100] flex items-center justify-center p-8 bg-background/95 backdrop-blur-3xl">
          <motion.div 
            initial={{ opacity: 0, scale: 0.9, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.9, y: 20 }}
            className="w-full max-w-6xl glass-card p-0 overflow-hidden border-white/10 shadow-[0_0_150px_rgba(0,243,255,0.15)]"
          >
            {/* Header */}
            <div className="px-12 py-10 border-b border-white/5 bg-white/5 flex justify-between items-center">
              <div className="flex items-center gap-6">
                <div className="p-4 bg-primary/10 rounded-2xl border border-primary/20 shadow-lg">
                  <Workflow className="text-primary w-8 h-8" />
                </div>
                <div>
                  <h2 className="text-2xl font-black text-white uppercase tracking-[0.1em]">RTI-Lens System Architecture</h2>
                  <div className="flex items-center gap-3 mt-1">
                    <span className="px-3 py-1 rounded-full bg-purple-500/10 border border-purple-500/20 text-[10px] font-black text-purple-400 uppercase tracking-widest flex items-center gap-2">
                      <Activity size={10} /> State Managed by Backboard.io
                    </span>
                    <span className="text-[11px] text-white/30 font-medium italic">Synchronized Service Mesh v2.8.0</span>
                  </div>
                </div>
              </div>
              <button onClick={onClose} className="p-3 hover:bg-white/10 rounded-full transition-all border border-white/10 bg-white/5"><X size={28} /></button>
            </div>

            {/* Content */}
            <div className="p-16 space-y-16 overflow-y-auto max-h-[70vh] scrollbar-hide">
              
              {/* Architecture Mermaid-style Flow */}
              <div className="relative p-12 rounded-[3rem] bg-black/50 border border-white/5 overflow-hidden group">
                <div className="absolute inset-0 bg-gradient-to-r from-primary/5 via-purple-500/5 to-amber-500/5" />
                
                <div className="relative space-y-12">
                   {/* Flow Layer 1 */}
                   <div className="flex justify-center items-center gap-10">
                      <div className="flex flex-col items-center gap-3">
                        <div className="w-16 h-16 rounded-2xl bg-white/5 border border-white/10 flex items-center justify-center text-white/40">
                          <Zap size={28} />
                        </div>
                        <span className="text-[10px] font-black uppercase text-white/20">React UI</span>
                      </div>
                      <ChevronRight className="text-white/10" />
                      <div className="flex flex-col items-center gap-3">
                        <div className="px-10 py-4 rounded-2xl bg-primary/10 border border-primary/30 flex items-center justify-center text-primary shadow-[0_0_20px_rgba(0,243,255,0.1)]">
                          <span className="text-xs font-black uppercase tracking-[0.2em]">FastAPI Backend</span>
                        </div>
                        <span className="text-[10px] font-black uppercase text-white/20">REST Endpoints</span>
                      </div>
                   </div>

                   {/* Vertical Lines */}
                   <div className="flex justify-center h-10">
                      <div className="w-[1px] h-full bg-gradient-to-b from-primary/40 to-transparent" />
                   </div>

                   {/* Service Grid Layer */}
                   <div className="grid grid-cols-4 gap-4 px-10">
                      {serviceNodes.map((node, i) => (
                        <div key={i} className="flex flex-col items-center gap-3">
                           <div className={`w-14 h-14 rounded-xl bg-white/5 border border-white/10 flex items-center justify-center ${node.color}`}>
                              <node.icon size={22} />
                           </div>
                           <span className="text-[9px] font-black uppercase text-white/40 text-center">{node.id}</span>
                        </div>
                      ))}
                   </div>

                   <div className="flex justify-around px-10">
                      <div className="flex flex-col items-center gap-2">
                        <div className="h-8 w-[1px] bg-white/10" />
                        <span className="text-[8px] font-mono text-white/20 uppercase tracking-widest">RAG (BM25+MV)</span>
                      </div>
                      <div className="flex flex-col items-center gap-2">
                        <div className="h-8 w-[1px] bg-white/10" />
                        <span className="text-[8px] font-mono text-white/20 uppercase tracking-widest">Gradient Boost</span>
                      </div>
                      <div className="flex flex-col items-center gap-2">
                        <div className="h-8 w-[1px] bg-white/10" />
                        <span className="text-[8px] font-mono text-white/20 uppercase tracking-widest">Legal Graph</span>
                      </div>
                      <div className="flex flex-col items-center gap-2">
                        <div className="h-8 w-[1px] bg-white/10" />
                        <span className="text-[8px] font-mono text-white/20 uppercase tracking-widest">Multi-Agent</span>
                      </div>
                   </div>
                </div>
              </div>

              {/* Service Details Grid */}
              <div className="grid grid-cols-2 gap-10">
                {serviceNodes.map((node, i) => (
                  <GlassCard key={i} className="p-10 group hover:border-primary/30 transition-all bg-white/[0.02] flex gap-8">
                    <div className={`p-5 rounded-2xl bg-white/5 border border-white/5 ${node.color}`}>
                      <node.icon size={28} />
                    </div>
                    <div className="space-y-3 flex-1">
                      <div className="flex justify-between items-center">
                        <h3 className="text-sm font-black uppercase tracking-widest text-white">{node.title}</h3>
                        <span className="text-[9px] font-mono text-primary/60">{node.tech}</span>
                      </div>
                      <p className="text-xs text-white/40 leading-relaxed font-medium">
                        {node.desc}
                      </p>
                    </div>
                  </GlassCard>
                ))}
              </div>

              {/* Backboard.io State Integration */}
              <div className="p-12 rounded-[3rem] bg-gradient-to-br from-purple-500/10 to-primary/10 border border-white/10 relative overflow-hidden">
                <div className="absolute -right-20 -top-20 opacity-5"><Activity size={300} className="text-purple-500" /></div>
                <div className="relative space-y-10">
                  <div className="flex items-center gap-4">
                    <Activity className="text-purple-400 w-8 h-8" />
                    <div>
                      <h3 className="text-xl font-black text-white uppercase tracking-widest">Backboard.io Orchestration</h3>
                      <p className="text-xs text-white/40 font-bold uppercase tracking-widest mt-1">Cross-Service State Sync & Observation</p>
                    </div>
                  </div>
                  
                  <div className="grid grid-cols-3 gap-8 text-center">
                    <div className="space-y-2">
                       <h4 className="text-[10px] font-black text-primary uppercase">Hybrid Retrieval</h4>
                       <p className="text-[10px] text-white/30 italic">Coordinates MongoDB Vector results with BM25 keyword rankings via unified session ID.</p>
                    </div>
                    <div className="space-y-2">
                       <h4 className="text-[10px] font-black text-purple-400 uppercase">ML Traceability</h4>
                       <p className="text-[10px] text-white/30 italic">Logs feature weights and prediction confidence for every outcome analysis.</p>
                    </div>
                    <div className="space-y-2">
                       <h4 className="text-[10px] font-black text-amber-400 uppercase">Agent Persistence</h4>
                       <p className="text-[10px] text-white/30 italic">Maintains consensus history between legal agents for deterministic drafting.</p>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Footer Action */}
            <div className="p-10 border-t border-white/5 flex justify-center bg-white/5">
               <button onClick={onClose} className="px-16 py-4 rounded-2xl bg-primary text-background font-black text-xs uppercase tracking-widest neo-glow">
                 Close System Architecture
               </button>
            </div>
          </motion.div>
        </div>
      )}
    </AnimatePresence>
  );
};

export default RAGArchitectureModal;
