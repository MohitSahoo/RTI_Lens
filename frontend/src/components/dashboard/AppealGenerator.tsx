import React, { useMemo, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  AlertTriangle,
  Building2,
  Clock,
  Copy,
  Cpu,
  Database,
  Download,
  FileText,
  HelpCircle,
  Loader2,
  Network,
  PenLine,
  ChevronRight,
  Search,
  Scale,
  ShieldCheck,
  Sparkles,
  UserCheck,
  Wand2,
  X,
} from 'lucide-react';
import { GlassCard } from '../ui/GlassCard';
import { GlowButton } from '../ui/GlowButton';
import { VoiceMic } from '../ui/VoiceMic';
import RAGArchitectureModal from './RAGArchitectureModal';

type StepStatus = 'pending' | 'active' | 'complete';

interface PipelineStep {
  key: string;
  title: string;
  detail: string;
  icon: React.ComponentType<{ className?: string; size?: number }>;
}

interface SourceDetail {
  order_number: string;
  full_text: string;
  hierarchy: string[];
  metadata: any;
}

const PIPELINE_STEPS: PipelineStep[] = [
  {
    key: 'intake',
    title: 'Query intake',
    detail: 'Capture the user facts and prepare the request for drafting.',
    icon: FileText,
  },
  {
    key: 'rag',
    title: 'RAG retrieval',
    detail: 'Pull similar precedents using BM25 and semantic search.',
    icon: Search,
  },
  {
    key: 'classify',
    title: 'Ministry + section',
    detail: 'Resolve the most likely ministry and exemption section.',
    icon: Building2,
  },
  {
    key: 'agents',
    title: '3 Groq agents',
    detail: 'Generate three drafts with different prompts and keys.',
    icon: Cpu,
  },
  {
    key: 'predict',
    title: 'Prediction model',
    detail: 'Score each draft and keep only the accepted candidates.',
    icon: ShieldCheck,
  },
  {
    key: 'merge',
    title: 'Gemini merge',
    detail: 'Blend the strongest accepted drafts into one final version.',
    icon: Wand2,
  },
];

const AppealGenerator: React.FC = () => {
  const [formData, setFormData] = useState({ context: '' });
  const [loading, setLoading] = useState(false);
  const [liveStepIndex, setLiveStepIndex] = useState(0);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);
  const [sessionStatus, setSessionStatus] = useState<any>(null);
  const [selectedSource, setSelectedSource] = useState<SourceDetail | null>(null);
  const [isArchModalOpen, setIsArchModalOpen] = useState(false);

  const stepStates = useMemo(() => {
    return PIPELINE_STEPS.map((step, index) => {
      let status: StepStatus = 'pending';
      if (loading) {
        status = index < liveStepIndex ? 'complete' : index === liveStepIndex ? 'active' : 'pending';
      } else if (result) {
        status = 'complete';
      }

      return { ...step, status };
    });
  }, [loading, liveStepIndex, result]);

  const currentStep = stepStates[Math.min(liveStepIndex, stepStates.length - 1)];

  const handleGenerate = async () => {
    const context = formData.context.trim();
    if (context.length < 50) {
      setError('Please provide at least 50 characters of context so the retrieval step has enough signal.');
      return;
    }

    setLoading(true);
    setError(null);
    setResult(null);
    setSessionStatus(null);
    setLiveStepIndex(0);

    const payload = {
      context,
      ministry: null,
      section_cited: null,
    };

    const timer = window.setInterval(() => {
      setLiveStepIndex((current) => Math.min(current + 1, PIPELINE_STEPS.length - 1));
    }, 1200);

    try {
      const response = await fetch('/api/draft', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      const rawBody = await response.text();
      let data: any = {};
      try {
        data = rawBody ? JSON.parse(rawBody) : {};
      } catch {
        data = { detail: rawBody || 'Draft generation failed' };
      }

      if (!response.ok) {
        throw new Error(
          Array.isArray(data.detail)
            ? data.detail.map((item: any) => item.msg).join('\n')
            : data.detail || 'Draft generation failed'
        );
      }

      setResult(data);
      setLiveStepIndex(PIPELINE_STEPS.length - 1);

      if (data.session_id) {
        try {
          const statusResponse = await fetch(`/api/draft/status/${encodeURIComponent(data.session_id)}`);
          if (statusResponse.ok) {
            setSessionStatus(await statusResponse.json());
          }
        } catch (statusError) {
          console.error('Unable to fetch draft status', statusError);
        }
      }
    } catch (generationError: any) {
      console.error('Draft generation error:', generationError);
      setError(generationError.message || 'Something went wrong while building the draft.');
    } finally {
      window.clearInterval(timer);
      setLoading(false);
    }
  };

  const fetchSourceDetails = async (orderNumber: string) => {
    try {
      const response = await fetch(`/api/qa/source?order_number=${encodeURIComponent(orderNumber)}`);
      if (response.ok) {
        setSelectedSource(await response.json());
      }
    } catch (sourceError) {
      console.error('Source fetch error:', sourceError);
    }
  };

  const copyDraft = async () => {
    const text = result?.draft || result?.improved_query || '';
    if (!text) return;
    await navigator.clipboard.writeText(text);
  };

  const downloadDraft = () => {
    const text = result?.draft || result?.improved_query || '';
    if (!text) return;

    const blob = new Blob([text], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement('a');
    anchor.href = url;
    anchor.download = 'rti-first-appeal-draft.txt';
    document.body.appendChild(anchor);
    anchor.click();
    document.body.removeChild(anchor);
    URL.revokeObjectURL(url);
  };

  const finalMinistry = result?.predicted_ministry || 'Waiting for the RAG pass';
  const finalSection = result?.predicted_section || 'Waiting for the RAG pass';
  const acceptedAgents = result?.accepted_agent_results || [];
  const rejectedAgents = result?.rejected_agent_results || [];
  const trace = result?.pipeline_trace || [];
  const statusActions = sessionStatus?.actions || [];

  return (
    <div className="relative min-h-[calc(100vh-140px)] overflow-hidden">
      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_top_left,_rgba(0,212,255,0.14),_transparent_28%),radial-gradient(circle_at_top_right,_rgba(245,158,11,0.12),_transparent_24%),linear-gradient(180deg,rgba(11,16,32,0.92),rgba(11,16,32,1))]" />
      <div className="pointer-events-none absolute inset-0 opacity-30 [background-image:linear-gradient(rgba(255,255,255,0.04)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,0.04)_1px,transparent_1px)] [background-size:48px_48px]" />

      <div className="relative mx-auto flex min-h-[calc(100vh-140px)] max-w-[1680px] gap-8 px-4 py-4 lg:px-6">
        <div className="w-full max-w-[430px] shrink-0 space-y-6">
          <GlassCard className="border-white/10 bg-white/[0.03] p-6">
            <div className="flex items-start justify-between gap-4">
              <div>
                <p className="text-[10px] font-bold uppercase tracking-[0.35em] text-cyan-300/80">Appeal Forge</p>
                <h1 className="mt-2 text-3xl font-black tracking-tight text-white">Draft generator</h1>
                <p className="mt-2 text-sm leading-6 text-white/50">
                  Type the query once, then let retrieval, three Groq agents, the prediction model, and Gemini shape the final draft.
                </p>
              </div>
              <div className="flex h-12 w-12 items-center justify-center rounded-2xl border border-cyan-300/20 bg-cyan-300/10 text-cyan-300">
                <PenLine size={22} />
              </div>
            </div>

            <div className="mt-6 space-y-3">
              <label className="flex items-center gap-2 text-[10px] font-bold uppercase tracking-[0.3em] text-white/35">
                <Database size={12} />
                Query
              </label>
              <div className="relative">
                <textarea
                  value={formData.context}
                  onChange={(event) => setFormData({ context: event.target.value })}
                  placeholder="Describe the RTI denial, appeal facts, and any context you already have..."
                  className="min-h-[270px] w-full resize-none rounded-[24px] border border-white/10 bg-black/20 px-5 py-4 text-[14px] leading-6 text-white outline-none transition focus:border-cyan-300/40 focus:bg-black/25"
                />
                <div className="absolute bottom-4 right-4">
                  <VoiceMic
                    onTranscript={(text) =>
                      setFormData((prev) => ({
                        context: prev.context ? `${prev.context} ${text}` : text,
                      }))
                    }
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-4">
                  <div className="text-[9px] font-bold uppercase tracking-[0.3em] text-white/30">Ministry</div>
                  <div className="mt-2 text-sm text-white/80">{finalMinistry}</div>
                </div>
                <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-4">
                  <div className="text-[9px] font-bold uppercase tracking-[0.3em] text-white/30">Section</div>
                  <div className="mt-2 text-sm text-white/80">{finalSection}</div>
                </div>
              </div>

              <div className="rounded-2xl border border-cyan-300/10 bg-cyan-300/5 p-4 text-[11px] leading-5 text-cyan-100/70">
                The backend now returns the resolved ministry and section after the RAG pass, so these fields become populated from the actual pipeline rather than manual entry.
              </div>
            </div>

            {error && (
              <div className="mt-4 flex items-start gap-3 rounded-2xl border border-red-400/20 bg-red-400/10 p-4 text-sm text-red-100">
                <AlertTriangle size={16} className="mt-0.5 shrink-0" />
                <span>{error}</span>
              </div>
            )}

            <GlowButton
              variant="primary"
              className="mt-6 w-full py-4 text-[13px] font-semibold"
              onClick={handleGenerate}
              disabled={loading}
            >
              {loading ? (
                <>
                  <Loader2 size={16} className="animate-spin" />
                  Building draft
                </>
              ) : (
                <>
                  <Wand2 size={16} />
                  Generate draft
                </>
              )}
            </GlowButton>
          </GlassCard>

          <GlassCard className="border-white/10 bg-white/[0.025] p-5">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2 text-[10px] font-bold uppercase tracking-[0.3em] text-white/30">
                <ShieldCheck size={13} />
                Audit trail
              </div>
              <div className="text-[10px] font-mono text-white/35">
                {result?.session_id ? result.session_id.slice(0, 8) : 'waiting'}
              </div>
            </div>
            <div className="mt-3 text-sm text-white/60">
              {sessionStatus?.workflow_stage || (loading ? 'Drafting in progress' : 'Ready')}
            </div>
          </GlassCard>
        </div>

        <div className="min-w-0 flex-1">
          <GlassCard className="h-full border-white/10 bg-white/[0.025] p-0">
            <div className="flex h-full flex-col">
              <div className="flex flex-wrap items-center justify-between gap-4 border-b border-white/8 px-6 py-5 lg:px-8">
                <div>
                  <p className="text-[10px] font-bold uppercase tracking-[0.3em] text-white/30">Workflow monitor</p>
                  <h2 className="mt-2 text-xl font-black text-white">
                    {loading ? currentStep.title : result ? 'Final output' : 'Waiting for your query'}
                  </h2>
                  <p className="mt-1 text-sm text-white/45">
                    {loading ? currentStep.detail : 'The panel below shows the exact steps once the run completes.'}
                  </p>
                </div>

                <div className="flex items-center gap-3">
                  <button
                    onClick={() => setIsArchModalOpen(true)}
                    className="flex items-center gap-2 rounded-xl border border-white/10 bg-white/[0.04] px-3 py-2 text-[11px] font-semibold uppercase tracking-[0.24em] text-white/55 transition hover:border-cyan-300/30 hover:text-cyan-200"
                  >
                    <HelpCircle size={14} />
                    Architecture
                  </button>
                  {result && (
                    <>
                      <GlowButton variant="outline" className="px-4 py-2 text-[12px]" onClick={copyDraft}>
                        <Copy size={14} />
                        Copy
                      </GlowButton>
                      <GlowButton variant="secondary" className="px-4 py-2 text-[12px]" onClick={downloadDraft}>
                        <Download size={14} />
                        Download
                      </GlowButton>
                    </>
                  )}
                </div>
              </div>

              <div className="grid gap-6 px-6 py-6 xl:grid-cols-[1.15fr_0.85fr] xl:px-8">
                <div className="space-y-6">
                  <GlassCard className="border-white/8 bg-black/15 p-5" hover={false}>
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2 text-[10px] font-bold uppercase tracking-[0.25em] text-cyan-300/70">
                        <Cpu size={13} />
                        Live pipeline
                      </div>
                      <div className="text-[10px] font-mono text-white/35">
                        {loading ? `${liveStepIndex + 1}/${PIPELINE_STEPS.length}` : result ? 'complete' : 'idle'}
                      </div>
                    </div>

                    <div className="mt-4 grid gap-3">
                      {stepStates.map((step, index) => {
                        const StepIcon = step.icon;
                        const active = step.status === 'active';
                        const complete = step.status === 'complete';

                        return (
                          <div
                            key={step.key}
                            className={`rounded-2xl border px-4 py-4 transition ${
                              active
                                ? 'border-cyan-300/35 bg-cyan-300/10'
                                : complete
                                  ? 'border-emerald-400/20 bg-emerald-400/8'
                                  : 'border-white/8 bg-white/[0.03]'
                            }`}
                          >
                            <div className="flex items-start gap-3">
                              <div
                                className={`mt-0.5 flex h-9 w-9 shrink-0 items-center justify-center rounded-xl ${
                                  active
                                    ? 'bg-cyan-300/20 text-cyan-200'
                                    : complete
                                      ? 'bg-emerald-400/15 text-emerald-300'
                                      : 'bg-white/5 text-white/35'
                                }`}
                              >
                                <StepIcon size={16} />
                              </div>

                              <div className="min-w-0 flex-1">
                                <div className="flex items-center justify-between gap-4">
                                  <div className="min-w-0">
                                    <div className="text-sm font-semibold text-white">{step.title}</div>
                                    <div className="mt-1 text-[12px] leading-5 text-white/45">{step.detail}</div>
                                  </div>
                                  <div className="text-[10px] font-mono uppercase tracking-[0.25em] text-white/30">
                                    {index + 1}
                                  </div>
                                </div>

                                <div className="mt-3 h-1 overflow-hidden rounded-full bg-white/8">
                                  <div
                                    className={`h-full rounded-full transition-all duration-700 ${
                                      active
                                        ? 'w-3/4 bg-cyan-300'
                                        : complete
                                          ? 'w-full bg-emerald-400'
                                          : 'w-0 bg-white/20'
                                    }`}
                                  />
                                </div>
                              </div>
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </GlassCard>

                  {loading && (
                    <GlassCard className="border-white/8 bg-white/[0.02] p-5" hover={false}>
                      <div className="flex items-center gap-3 text-[10px] font-bold uppercase tracking-[0.25em] text-white/35">
                        <Clock size={13} />
                        Running now
                      </div>
                      <div className="mt-3 text-lg font-semibold text-white">{currentStep.title}</div>
                      <p className="mt-2 text-sm leading-6 text-white/55">{currentStep.detail}</p>
                    </GlassCard>
                  )}

                  {result && (
                    <GlassCard className="border-white/8 bg-white/[0.02] p-0" hover={false}>
                      <div className="border-b border-white/8 px-5 py-4">
                        <div className="flex items-center gap-2 text-[10px] font-bold uppercase tracking-[0.25em] text-amber-300/80">
                          <Sparkles size={13} />
                          Final draft
                        </div>
                      </div>
                      <div className="max-h-[540px] overflow-y-auto whitespace-pre-wrap px-6 py-6 text-[14px] leading-7 text-white/80">
                        {result.draft || result.improved_query}
                      </div>
                    </GlassCard>
                  )}

                  {trace.length > 0 && (
                    <GlassCard className="border-white/8 bg-white/[0.02] p-5" hover={false}>
                      <div className="flex items-center gap-2 text-[10px] font-bold uppercase tracking-[0.25em] text-white/35">
                        <Network size={13} />
                        Backend trace
                      </div>
                      <div className="mt-4 grid gap-3">
                        {trace.map((item: any, index: number) => (
                          <div key={`${item.step}-${index}`} className="rounded-2xl border border-white/8 bg-white/[0.03] p-4">
                            <div className="flex items-center justify-between gap-4">
                              <div className="text-sm font-semibold text-white">{item.step}</div>
                              <div className="text-[10px] font-mono uppercase tracking-[0.25em] text-cyan-200/70">
                                {item.status}
                              </div>
                            </div>
                            <div className="mt-2 text-sm text-white/55">{item.detail}</div>
                          </div>
                        ))}
                      </div>
                    </GlassCard>
                  )}
                </div>

                <div className="space-y-6">
                  <GlassCard className="border-white/8 bg-white/[0.02] p-5" hover={false}>
                    <div className="flex items-center gap-2 text-[10px] font-bold uppercase tracking-[0.25em] text-white/35">
                      <Building2 size={13} />
                      Auto-populated fields
                    </div>
                    <div className="mt-4 space-y-3">
                      <div className="rounded-2xl border border-white/8 bg-white/[0.03] p-4">
                        <div className="text-[9px] font-bold uppercase tracking-[0.25em] text-white/30">Ministry</div>
                        <div className="mt-2 text-sm text-white">{result?.predicted_ministry || 'Pending RAG inference'}</div>
                      </div>
                      <div className="rounded-2xl border border-white/8 bg-white/[0.03] p-4">
                        <div className="text-[9px] font-bold uppercase tracking-[0.25em] text-white/30">Section</div>
                        <div className="mt-2 text-sm text-white">{result?.predicted_section || 'Pending RAG inference'}</div>
                      </div>
                      <div className="rounded-2xl border border-cyan-300/15 bg-cyan-300/6 p-4 text-[11px] leading-5 text-cyan-100/70">
                        These values come from the retrieval-guided classification step, then get passed into the prediction model for each candidate draft.
                      </div>
                    </div>
                  </GlassCard>

                  <GlassCard className="border-white/8 bg-white/[0.02] p-5" hover={false}>
                    <div className="flex items-center justify-between gap-4">
                      <div className="flex items-center gap-2 text-[10px] font-bold uppercase tracking-[0.25em] text-emerald-300/80">
                        <UserCheck size={13} />
                        Accepted drafts
                      </div>
                      <div className="text-[10px] font-mono text-white/35">{acceptedAgents.length} kept</div>
                    </div>
                    <div className="mt-4 space-y-3">
                      {acceptedAgents.length > 0 ? (
                        acceptedAgents.map((agent: any, index: number) => (
                          <div key={`${agent.agent}-${index}`} className="rounded-2xl border border-emerald-400/15 bg-emerald-400/7 p-4">
                            <div className="flex items-center justify-between gap-3">
                              <div className="text-sm font-semibold text-white">{agent.agent}</div>
                              <div className="text-[10px] font-mono text-emerald-300">
                                {Math.round((agent.prediction_preview?.probability || 0) * 100)}%
                              </div>
                            </div>
                            <div className="mt-2 text-sm text-white/50 line-clamp-3">
                              {agent.draft_preview || agent.response_summary}
                            </div>
                          </div>
                        ))
                      ) : (
                        <div className="rounded-2xl border border-white/8 bg-white/[0.03] p-4 text-sm text-white/45">
                          Accepted drafts will appear here after the prediction model filters the Groq outputs.
                        </div>
                      )}
                    </div>
                  </GlassCard>

                  <GlassCard className="border-white/8 bg-white/[0.02] p-5" hover={false}>
                    <div className="flex items-center justify-between gap-4">
                      <div className="flex items-center gap-2 text-[10px] font-bold uppercase tracking-[0.25em] text-rose-300/80">
                        <Scale size={13} />
                        Rejected drafts
                      </div>
                      <div className="text-[10px] font-mono text-white/35">{rejectedAgents.length} filtered</div>
                    </div>
                    <div className="mt-4 space-y-3">
                      {rejectedAgents.length > 0 ? (
                        rejectedAgents.map((agent: any, index: number) => (
                          <div key={`${agent.agent}-${index}`} className="rounded-2xl border border-rose-400/15 bg-rose-400/7 p-4">
                            <div className="flex items-center justify-between gap-3">
                              <div className="text-sm font-semibold text-white">{agent.agent}</div>
                              <div className="text-[10px] font-mono text-rose-300">
                                {Math.round((agent.prediction_preview?.probability || 0) * 100)}%
                              </div>
                            </div>
                            <div className="mt-2 text-sm text-white/50 line-clamp-3">
                              {agent.draft_preview || agent.response_summary}
                            </div>
                          </div>
                        ))
                      ) : (
                        <div className="rounded-2xl border border-white/8 bg-white/[0.03] p-4 text-sm text-white/45">
                          Drafts filtered by the prediction model will show up here.
                        </div>
                      )}
                    </div>
                  </GlassCard>

                  {result?.retrieval && (
                    <GlassCard className="border-white/8 bg-white/[0.02] p-5" hover={false}>
                      <div className="flex items-center gap-2 text-[10px] font-bold uppercase tracking-[0.25em] text-white/35">
                        <Search size={13} />
                        Retrieval summary
                      </div>
                      <div className="mt-4 space-y-2 text-sm text-white/60">
                        <div>Method: {result.retrieval.method}</div>
                        <div>Precedents: {result.retrieval.precedents_count}</div>
                        <div>Orchestration: {result.orchestration_method}</div>
                      </div>
                      {result?.retrieved_precedents?.[0]?.order_number && (
                        <button
                          onClick={() => fetchSourceDetails(result.retrieved_precedents[0].order_number)}
                          className="mt-4 inline-flex items-center gap-2 rounded-xl border border-white/10 bg-white/[0.03] px-3 py-2 text-[11px] font-semibold uppercase tracking-[0.22em] text-white/60 transition hover:border-cyan-300/30 hover:text-cyan-200"
                        >
                          View precedent
                          <ChevronRight size={13} />
                        </button>
                      )}
                    </GlassCard>
                  )}

                  {sessionStatus?.actions?.length > 0 && (
                    <GlassCard className="border-white/8 bg-white/[0.02] p-5" hover={false}>
                      <div className="flex items-center gap-2 text-[10px] font-bold uppercase tracking-[0.25em] text-white/35">
                        <Clock size={13} />
                        Session actions
                      </div>
                      <div className="mt-4 space-y-3">
                        {statusActions.map((action: any, index: number) => (
                          <div key={`${action.action_name}-${index}`} className="rounded-2xl border border-white/8 bg-white/[0.03] p-4">
                            <div className="flex items-center justify-between gap-3">
                              <div className="text-sm font-semibold text-white">{action.action_name}</div>
                              <div className="text-[10px] font-mono uppercase tracking-[0.25em] text-white/30">
                                {action.action_type}
                              </div>
                            </div>
                            <div className="mt-2 text-sm text-white/55">{action.error_message || 'Recorded successfully'}</div>
                          </div>
                        ))}
                      </div>
                    </GlassCard>
                  )}
                </div>
              </div>
            </div>
          </GlassCard>
        </div>
      </div>

      <SourceDetailModal source={selectedSource} onClose={() => setSelectedSource(null)} />
      <RAGArchitectureModal isOpen={isArchModalOpen} onClose={() => setIsArchModalOpen(false)} />
    </div>
  );
};

const SourceDetailModal = ({ source, onClose }: { source: any; onClose: () => void }) => (
  <AnimatePresence>
    {source && (
      <div className="fixed inset-0 z-50 flex items-center justify-center bg-background/90 p-4 backdrop-blur-2xl">
        <motion.div
          initial={{ opacity: 0, scale: 0.97, y: 16 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.97, y: 16 }}
          className="flex h-[84vh] w-full max-w-5xl flex-col overflow-hidden rounded-[28px] border border-white/10 bg-[#0B1020] shadow-2xl"
        >
          <div className="flex items-center justify-between border-b border-white/8 px-6 py-5 lg:px-8">
            <div>
              <div className="text-[10px] font-bold uppercase tracking-[0.3em] text-cyan-300/70">Precedent source</div>
              <h3 className="mt-2 text-2xl font-black text-white">{source.order_number}</h3>
              <p className="mt-1 text-[11px] uppercase tracking-[0.22em] text-white/35">
                {(source.hierarchy || []).join(' > ')}
              </p>
            </div>
            <button
              onClick={onClose}
              className="rounded-full border border-white/10 bg-white/[0.04] p-3 text-white/60 transition hover:border-white/20 hover:text-white"
            >
              <X size={18} />
            </button>
          </div>

          <div className="flex-1 overflow-y-auto px-6 py-6 lg:px-8">
            <div className="whitespace-pre-wrap rounded-[24px] border border-white/8 bg-white/[0.03] p-6 font-mono text-[13px] leading-7 text-white/75">
              {source.full_text}
            </div>
          </div>
        </motion.div>
      </div>
    )}
  </AnimatePresence>
);

export default AppealGenerator;
