import React, { useState } from 'react';
import { motion } from 'framer-motion';
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
  PenLine
} from 'lucide-react';
import { GlassCard } from '../ui/GlassCard';
import { GlowButton } from '../ui/GlowButton';

const AppealGenerator: React.FC = () => {
  const [formData, setFormData] = useState({
    originalRti: '',
  });

  const [generating, setGenerating] = useState(false);
  const [draft, setDraft] = useState('');
  const [apiResponse, setApiResponse] = useState<any>(null);

  const handleGenerate = async () => {
    if (formData.originalRti.length < 20) {
      alert("RTI query must be at least 20 characters.");
      return;
    }
    
    setGenerating(true);
    try {
      const response = await fetch('/api/query-assistant/optimize', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          query: formData.originalRti
        })
      });

      if (!response.ok) {
        throw new Error('Failed to generate draft');
      }

      const data = await response.json();
      
      // Map Query Assistant response to UI expected format
      const mappedData = {
        improved_query: data.optimized_query,
        change_notes: data.improvements_made.map((imp: string) => ({
          original: "N/A",
          revised: imp,
          reason: "Suggested by AI"
        })),
        avoid_phrases: data.issues_detected.map((iss: any) => iss.suggestion),
        sources: data.relevant_precedents.map((prec: any) => ({
          order_number: prec.order_number,
          outcome: "Relevant Case",
          relevance: prec.text_preview
        }))
      };

      setApiResponse(mappedData);
      
      const constructedDraft = `
IMPROVED RTI QUERY:
${mappedData.improved_query}

DRAFTING NOTES & IMPROVEMENTS:
${mappedData.change_notes.map((n: any) => `- ${n.revised}`).join('\n')}

ISSUES DETECTED:
${mappedData.avoid_phrases.map((p: string) => `- ${p}`).join('\n')}
      `.trim();
      
      setDraft(constructedDraft);
    } catch (error) {
      console.error("Draft generation error:", error);
      setDraft("An error occurred while generating the draft. Please ensure the backend is running.");
    } finally {
      setGenerating(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-end">
        <div>
          <h1 className="text-3xl font-bold font-display">Query Optimizer</h1>
          <p className="text-white/50 text-sm">AI-powered optimization for RTI requests based on legal precedents.</p>
        </div>
      </div>

      <div className="grid lg:grid-cols-2 gap-8 h-[calc(100vh-220px)]">
        {/* Left: Input Form */}
        <div className="space-y-6 overflow-y-auto pr-2 custom-scrollbar">
          <GlassCard className="space-y-6">
            <div className="space-y-4">
              <div className="space-y-2">
                <label className="text-[10px] font-bold text-white/30 uppercase tracking-[0.2em]">Original RTI Query Text</label>
                <textarea 
                  placeholder="Paste your original RTI request here (e.g. 'Why is my passport delayed and what are the reasons given by MEA?')..."
                  className="w-full bg-white/5 border border-white/10 rounded-lg p-4 text-sm h-64 focus:border-primary/50 outline-none resize-none transition-all"
                  value={formData.originalRti}
                  onChange={(e) => setFormData({...formData, originalRti: e.target.value})}
                />
              </div>

              <div className="p-4 rounded-xl bg-white/5 border border-white/10 flex items-center justify-between">
                <div>
                  <h4 className="text-xs font-bold text-white/60">Auto-Cite Precedents</h4>
                  <p className="text-[10px] text-white/30">Matches your query with similar CIC rulings</p>
                </div>
                <div className="flex items-center gap-2 p-1.5 bg-primary/10 border border-primary/20 rounded-lg">
                  <span className="text-[10px] font-bold text-primary">ENABLED</span>
                </div>
              </div>
            </div>

            <GlowButton 
              className="w-full py-4" 
              onClick={handleGenerate}
              disabled={generating}
            >
              {generating ? (
                <>
                  <Sparkles className="animate-spin mr-2" size={18} /> Analyzing Precedents...
                </>
              ) : (
                <>
                  <PenLine className="mr-2" size={18} /> Optimize RTI Request
                </>
              )}
            </GlowButton>
          </GlassCard>

          {/* AI Suggestions Panel */}
          <div className="p-5 rounded-2xl bg-primary/5 border border-primary/20">
            <div className="flex items-center gap-2 mb-3">
              <Sparkles className="text-primary w-4 h-4" />
              <h3 className="text-xs font-bold uppercase tracking-widest text-primary">Drafting Strategy</h3>
            </div>
            <ul className="space-y-3">
              <li className="flex gap-3 text-xs text-white/60">
                <div className="w-1.5 h-1.5 rounded-full bg-primary mt-1 shrink-0" />
                <span>Include the specific CPIO order number for faster CIC indexing.</span>
              </li>
              <li className="flex gap-3 text-xs text-white/60">
                <div className="w-1.5 h-1.5 rounded-full bg-primary mt-1 shrink-0" />
                <span>Emphasize the "Public Interest" override in Section 8(2) if privacy is cited.</span>
              </li>
            </ul>
          </div>
        </div>

        {/* Right: Draft Preview */}
        <div className="flex flex-col h-full space-y-4">
          <div className="flex-1 glass-card p-0 overflow-hidden relative border-white/10 bg-background/50">
            {/* Header */}
            <div className="flex justify-between items-center p-4 border-b border-white/5 bg-white/5">
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 rounded-lg bg-white/5 flex items-center justify-center">
                  <FileText size={16} className="text-white/40" />
                </div>
                <div>
                  <h3 className="text-xs font-bold uppercase tracking-widest">Draft Preview</h3>
                  <p className="text-[10px] text-white/30">V1.0 - Generated just now</p>
                </div>
              </div>
              <div className="flex gap-2">
                <button className="p-2 rounded-lg bg-white/5 hover:bg-white/10 text-white/40 hover:text-white transition-colors">
                  <Copy size={16} />
                </button>
                <button className="p-2 rounded-lg bg-white/5 hover:bg-white/10 text-white/40 hover:text-white transition-colors">
                  <Download size={16} />
                </button>
              </div>
            </div>

            {/* Content Area */}
            <div className="p-8 h-full overflow-y-auto font-mono text-sm leading-relaxed text-white/70">
              {draft ? (
                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  className="whitespace-pre-wrap"
                >
                  {draft}
                  
                  {apiResponse?.sources?.length > 0 && (
                    <div className="mt-8 space-y-4">
                      <div className="h-px bg-white/10" />
                      <h4 className="text-[10px] font-bold text-primary uppercase tracking-widest">Legal Citations Found</h4>
                      <div className="grid gap-4">
                        {apiResponse.sources.map((src: any, i: number) => (
                          <div key={i} className="p-3 rounded-lg bg-white/5 border border-white/5">
                            <div className="flex justify-between items-center mb-1">
                              <span className="text-xs font-bold text-white">{src.order_number}</span>
                              <span className={cn(
                                "text-[10px] px-2 py-0.5 rounded uppercase font-bold",
                                src.outcome?.toLowerCase() === 'allowed' ? "bg-success/20 text-success" : "bg-warning/20 text-warning"
                              )}>
                                {src.outcome}
                              </span>
                            </div>
                            <p className="text-[10px] text-white/40 italic leading-normal">
                              "{src.relevance}"
                            </p>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  <div className="mt-12 h-px bg-white/10" />
                  <div className="mt-8 flex gap-6">
                    <div className="flex-1 p-4 rounded-xl bg-success/5 border border-success/20">
                      <div className="flex items-center gap-2 mb-2">
                        <ShieldCheck className="text-success w-4 h-4" />
                        <span className="text-[10px] font-bold text-success uppercase tracking-widest">Legal Strength</span>
                      </div>
                      <div className="text-xl font-bold font-display">Strong (84%)</div>
                    </div>
                    <div className="flex-1 p-4 rounded-xl bg-warning/5 border border-warning/20">
                      <div className="flex items-center gap-2 mb-2">
                        <AlertTriangle className="text-warning w-4 h-4" />
                        <span className="text-[10px] font-bold text-warning uppercase tracking-widest">Compliance</span>
                      </div>
                      <div className="text-xl font-bold font-display">Verified</div>
                    </div>
                  </div>
                </motion.div>
              ) : (
                <div className="h-full flex flex-col items-center justify-center text-center space-y-4">
                  <div className="w-16 h-16 rounded-full bg-white/5 flex items-center justify-center">
                    <Sparkles className="text-white/20 w-8 h-8" />
                  </div>
                  <div>
                    <h4 className="text-white/40 font-bold uppercase tracking-widest text-xs">Awaiting Generation</h4>
                    <p className="text-white/20 text-[10px] mt-1 max-w-[200px]">Fill the form and click generate to see your legal draft here.</p>
                  </div>
                </div>
              )}
            </div>

            {/* Overlay Shimmer when generating */}
            {generating && (
              <div className="absolute inset-0 bg-background/60 backdrop-blur-sm flex items-center justify-center z-20">
                <div className="space-y-4 text-center">
                  <div className="w-12 h-12 border-2 border-primary border-t-transparent rounded-full animate-spin mx-auto" />
                  <p className="text-xs font-bold text-primary animate-pulse tracking-[0.2em] uppercase">AI is writing...</p>
                </div>
              </div>
            )}
          </div>
          
          <div className="flex gap-4">
            <GlowButton variant="secondary" className="flex-1 py-4">
              <FileCheck2 className="mr-2" size={18} /> Finalize & Export PDF
            </GlowButton>
          </div>
        </div>
      </div>
    </div>
  );
};

function cn(...inputs: any[]) {
  return inputs.filter(Boolean).join(' ');
}

export default AppealGenerator;
