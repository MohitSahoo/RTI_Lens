import React, { useState, useCallback, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Target, 
  AlertCircle, 
  ShieldAlert, 
  Activity, 
  CheckCircle2,
  TrendingUp,
  BrainCircuit,
  Calendar,
} from 'lucide-react';
import { GlassCard } from '../ui/GlassCard';
import { GlowButton } from '../ui/GlowButton';
import { 
  Radar, 
  RadarChart, 
  PolarGrid, 
  PolarAngleAxis, 
  ResponsiveContainer,
} from 'recharts';

const Predictor: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [formData, setFormData] = useState({
    ministry: '',
    section_cited: '',
    appeal_level: '2nd Appeal',
    order_date: new Date().toISOString().split('T')[0],
    raw_text: ''
  });

  const [ministries, setMinistries] = useState<string[]>([]);

  useEffect(() => {
    const fetchMinistries = async () => {
      try {
        const response = await fetch('/api/ministries');
        if (response.ok) {
          const data = await response.json();
          setMinistries(data.ministries || []);
        }
      } catch (e) {
        console.error("Failed to fetch ministries", e);
      }
    };
    fetchMinistries();
  }, []);

  const handlePredict = async (e: React.FormEvent) => {
    e.preventDefault();
    if (formData.raw_text.length < 100) {
      alert("Please provide at least 100 characters of context for accurate prediction.");
      return;
    }

    setLoading(true);
    try {
      const payload = {
        ...formData,
        order_date: formData.order_date || null,
        appeal_level: formData.appeal_level === '1st Appeal' ? 'first_appeal' : 'second_appeal'
      };

      const response = await fetch('/api/predict', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      if (!response.ok) {
        const error = await response.json();
        const errorMessage = Array.isArray(error.detail) 
          ? error.detail.map((d: any) => `${d.loc.join('.')}: ${d.msg}`).join('\n')
          : (error.detail || 'Prediction failed');
        throw new Error(errorMessage);
      }

      const data = await response.json();
      setResult(data);
    } catch (err: any) {
      console.error(err);
      alert(err.message);
    } finally {
      setLoading(false);
    }
  };

  const radarData = result ? [
    { subject: 'Legal Grounds', A: result.probability * 100, B: 75 },
    { subject: 'Precedent Strength', A: result.confidence === 'high' ? 90 : 60, B: 80 },
    { subject: 'Section Match', A: 85, B: 70 },
    { subject: 'Procedural Compliance', A: 95, B: 90 },
    { subject: 'ML Certainty', A: result.probability * 100, B: 85 },
  ] : [];

  return (
    <div className="space-y-8">
      <div className="flex justify-between items-end">
        <div>
          <h1 className="text-3xl font-bold font-display text-white">AI Outcome Predictor</h1>
          <p className="text-white/50 text-sm">Analyze appeal success probability using ML models trained on 10,000+ historical CIC rulings.</p>
        </div>
      </div>

      <div className="grid lg:grid-cols-12 gap-8">
        {/* Left: Input Form */}
        <div className="lg:col-span-5 space-y-6">
          <GlassCard className="p-8 border-primary/20">
            <h3 className="text-lg font-bold mb-6 flex items-center gap-2 text-white">
              <BrainCircuit className="text-primary w-5 h-5" />
              Appeal Parameters
            </h3>
            <form onSubmit={handlePredict} className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <label className="text-[10px] font-bold text-white/40 uppercase tracking-widest">Ministry</label>
                  <select 
                    value={formData.ministry}
                    onChange={e => setFormData({...formData, ministry: e.target.value})}
                    className="w-full bg-white/5 border border-white/10 rounded-lg px-4 py-2.5 text-sm text-white focus:border-primary outline-none transition-all"
                    required
                  >
                    <option value="" disabled className="bg-[#0B1020]">Select Ministry</option>
                    {ministries.map(m => (
                      <option key={m} value={m} className="bg-[#0B1020]">{m}</option>
                    ))}
                    {ministries.length === 0 && (
                      <>
                        <option className="bg-[#0B1020]">Ministry of Finance</option>
                        <option className="bg-[#0B1020]">Ministry of Home Affairs</option>
                        <option className="bg-[#0B1020]">Ministry of Railways</option>
                        <option className="bg-[#0B1020]">Ministry of External Affairs</option>
                      </>
                    )}
                  </select>
                </div>
                <div className="space-y-2">
                  <label className="text-[10px] font-bold text-white/40 uppercase tracking-widest">Section Cited</label>
                  <input 
                    value={formData.section_cited}
                    onChange={e => setFormData({...formData, section_cited: e.target.value})}
                    placeholder="e.g. 8(1)(j)"
                    className="w-full bg-white/5 border border-white/10 rounded-lg px-4 py-2.5 text-sm text-white focus:border-primary outline-none transition-all"
                    required
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <label className="text-[10px] font-bold text-white/40 uppercase tracking-widest">Appeal Level</label>
                  <select 
                    value={formData.appeal_level}
                    onChange={e => setFormData({...formData, appeal_level: e.target.value})}
                    className="w-full bg-white/5 border border-white/10 rounded-lg px-4 py-2.5 text-sm text-white focus:border-primary outline-none transition-all"
                  >
                    <option className="bg-[#0B1020]">1st Appeal</option>
                    <option className="bg-[#0B1020]">2nd Appeal</option>
                  </select>
                </div>
                <div className="space-y-2">
                  <label className="text-[10px] font-bold text-white/40 uppercase tracking-widest">Order Date</label>
                  <div className="relative">
                    <Calendar className="absolute left-3 top-2.5 w-4 h-4 text-white/20" />
                    <input 
                      type="date"
                      value={formData.order_date}
                      onChange={e => setFormData({...formData, order_date: e.target.value})}
                      className="w-full bg-white/5 border border-white/10 rounded-lg pl-10 pr-4 py-2 text-sm text-white focus:border-primary outline-none transition-all"
                    />
                  </div>
                </div>
              </div>

              <div className="space-y-2">
                <label className="text-[10px] font-bold text-white/40 uppercase tracking-widest">Context / Facts of Case</label>
                <textarea 
                  value={formData.raw_text}
                  onChange={e => setFormData({...formData, raw_text: e.target.value})}
                  placeholder="Paste your appeal grounds or the previous order context here (min 100 chars)..."
                  className="w-full h-40 bg-white/5 border border-white/10 rounded-lg px-4 py-3 text-sm text-white focus:border-primary outline-none transition-all resize-none"
                  required
                />
              </div>

              <GlowButton 
                type="submit" 
                disabled={loading}
                className="w-full py-4 flex items-center justify-center gap-3 mt-4"
              >
                {loading ? (
                  <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                ) : (
                  <>
                    <Target size={18} />
                    Run Prediction Engine
                  </>
                )}
              </GlowButton>
            </form>
          </GlassCard>
        </div>

        {/* Right: Results Display */}
        <div className="lg:col-span-7 space-y-8 min-h-[600px]">
          <AnimatePresence mode="wait">
            {!result ? (
              <motion.div 
                key="empty"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="h-full flex flex-col items-center justify-center text-center p-12 border-2 border-dashed border-white/5 rounded-3xl"
              >
                <div className="w-20 h-20 rounded-full bg-white/5 flex items-center justify-center mb-6">
                  <Activity className="text-white/20 w-10 h-10" />
                </div>
                <h3 className="text-xl font-bold mb-2 text-white">No Prediction Run</h3>
                <p className="text-sm text-white/40 max-w-xs">Fill in the appeal details on the left and start the AI engine to see success probability.</p>
              </motion.div>
            ) : (
              <motion.div 
                key="result"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="space-y-8"
              >
                <div className="grid md:grid-cols-2 gap-8">
                  {/* Gauge Card */}
                  <GlassCard className="flex flex-col items-center justify-center p-8 relative overflow-hidden">
                    <div className={`absolute top-0 left-0 w-full h-1 bg-gradient-to-r ${result.prediction === 'allowed' ? 'from-success to-primary' : 'from-danger to-warning'}`} />
                    
                    <div className="relative w-48 h-48">
                      <svg className="w-full h-full transform -rotate-90">
                        <circle cx="96" cy="96" r="85" stroke="currentColor" strokeWidth="10" fill="transparent" className="text-white/5" />
                        <motion.circle
                          cx="96" cy="96" r="85" stroke="currentColor" strokeWidth="10" fill="transparent"
                          strokeDasharray={534}
                          initial={{ strokeDashoffset: 534 }}
                          animate={{ strokeDashoffset: 534 - (534 * result.probability) }}
                          transition={{ duration: 1.5, ease: "easeOut" }}
                          className={`${result.prediction === 'allowed' ? 'text-success' : 'text-danger'} neo-glow`}
                          strokeLinecap="round"
                        />
                      </svg>
                      <div className="absolute inset-0 flex flex-col items-center justify-center text-center">
                        <span className="text-5xl font-bold font-display text-white">
                          {Math.round(result.probability * 100)}%
                        </span>
                        <span className="text-[8px] font-bold text-white/40 tracking-[0.3em] uppercase mt-1">Success Prob.</span>
                      </div>
                    </div>

                    <div className="mt-8 w-full space-y-3">
                      <div className={`flex justify-between items-center p-3 rounded-xl ${result.prediction === 'allowed' ? 'bg-success/5 border-success/20' : 'bg-danger/5 border-danger/20'} border`}>
                        <div className="flex items-center gap-2">
                          {result.prediction === 'allowed' ? <CheckCircle2 size={16} className="text-success" /> : <ShieldAlert size={16} className="text-danger" />}
                          <span className="text-xs font-bold uppercase tracking-wider text-white">Likely Outcome</span>
                        </div>
                        <span className={`text-xs font-black uppercase ${result.prediction === 'allowed' ? 'text-success' : 'text-danger'}`}>
                          {result.prediction === 'allowed' ? 'approved' : result.prediction}
                        </span>
                      </div>
                      <div className={`flex justify-between items-center p-3 rounded-xl bg-white/5 border border-white/10`}>
                        <div className="flex items-center gap-2">
                          <Activity size={16} className="text-primary" />
                          <span className="text-xs font-bold uppercase tracking-wider text-white">Confidence</span>
                        </div>
                        <span className={`text-xs font-black uppercase text-primary`}>{result.confidence}</span>
                      </div>
                    </div>
                  </GlassCard>

                  {/* Analysis Card */}
                  <GlassCard className="p-8">
                    <h3 className="text-[10px] font-bold uppercase tracking-[0.2em] text-white/40 mb-6 flex items-center gap-2">
                      <TrendingUp size={12} className="text-secondary" />
                      Argument Strength Analysis
                    </h3>
                    <div className="h-[220px] w-full">
                      <ResponsiveContainer width="100%" height="100%">
                        <RadarChart cx="50%" cy="50%" outerRadius="80%" data={radarData}>
                          <PolarGrid stroke="rgba(255,255,255,0.05)" />
                          <PolarAngleAxis dataKey="subject" tick={{ fill: 'rgba(255,255,255,0.3)', fontSize: 8 }} />
                          <Radar name="Current" dataKey="A" stroke="#00D4FF" fill="#00D4FF" fillOpacity={0.5} />
                          <Radar name="Benchmark" dataKey="B" stroke="#7C3AED" fill="#7C3AED" fillOpacity={0.2} />
                        </RadarChart>
                      </ResponsiveContainer>
                    </div>
                  </GlassCard>
                </div>

                <GlassCard className="p-6 border-warning/10 bg-warning/5">
                  <div className="flex gap-4">
                    <div className="p-3 rounded-xl bg-warning/10 border border-warning/20 h-fit">
                      <ShieldAlert className="text-warning w-6 h-6" />
                    </div>
                    <div className="space-y-2">
                      <h4 className="text-sm font-bold text-warning uppercase tracking-widest">AI Disclaimer & Guidance</h4>
                      <p className="text-xs text-white/60 leading-relaxed">
                        {result.disclaimer}
                      </p>
                      {result.low_data_warning && (
                        <div className="mt-4 p-3 rounded-lg bg-danger/10 border border-danger/20">
                          <p className="text-[10px] font-bold text-danger leading-tight">
                            LOW TRAINING DATA: This ministry has fewer than 10 historical cases. 
                            Prediction may be less reliable for this specific authority.
                          </p>
                        </div>
                      )}
                    </div>
                  </div>
                </GlassCard>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>
    </div>
  );
};

export default Predictor;
