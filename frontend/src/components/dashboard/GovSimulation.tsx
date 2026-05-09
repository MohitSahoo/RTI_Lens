import React from 'react';
import { motion } from 'framer-motion';
import { Building2, Play, Pause, RotateCcw, Clock, Target, AlertTriangle } from 'lucide-react';
import { GlassCard } from '../ui/GlassCard';
import { GlowButton } from '../ui/GlowButton';

const GovSimulation: React.FC = () => {
  return (
    <div className="space-y-8">
      <div className="flex justify-between items-end">
        <div>
          <h1 className="text-3xl font-bold font-display">Government Simulation Engine</h1>
          <p className="text-white/50 text-sm">Simulate response behaviors of various ministries to optimize your RTI filing strategy.</p>
        </div>
        <div className="flex gap-4">
          <GlowButton>
            <Play size={16} className="mr-2" /> Start Simulation
          </GlowButton>
        </div>
      </div>

      <div className="grid lg:grid-cols-3 gap-8">
        <div className="space-y-6">
          <GlassCard>
            <h3 className="text-xs font-bold uppercase tracking-widest text-white/40 mb-6">Simulation Parameters</h3>
            <div className="space-y-6">
              <div className="space-y-3">
                <div className="flex justify-between text-[10px] font-bold uppercase">
                  <span>Ministry Rigidity</span>
                  <span className="text-primary">78%</span>
                </div>
                <div className="w-full h-1.5 bg-white/5 rounded-full">
                  <div className="h-full w-[78%] bg-primary rounded-full shadow-[0_0_8px_rgba(0,212,255,0.6)]" />
                </div>
              </div>
              <div className="space-y-3">
                <div className="flex justify-between text-[10px] font-bold uppercase">
                  <span>Transparency Pressure</span>
                  <span className="text-secondary">42%</span>
                </div>
                <div className="w-full h-1.5 bg-white/5 rounded-full">
                  <div className="h-full w-[42%] bg-secondary rounded-full shadow-[0_0_8px_rgba(124,58,237,0.6)]" />
                </div>
              </div>
              <div className="space-y-3">
                <div className="flex justify-between text-[10px] font-bold uppercase">
                  <span>AI Adversarial Depth</span>
                  <span className="text-success">Level 4</span>
                </div>
                <div className="flex gap-1">
                  {[1, 2, 3, 4, 5].map((i) => (
                    <div key={i} className={`flex-1 h-1.5 rounded-full ${i <= 4 ? 'bg-success' : 'bg-white/5'}`} />
                  ))}
                </div>
              </div>
            </div>
          </GlassCard>

          <GlassCard className="bg-warning/5 border-warning/20">
            <div className="flex items-start gap-3">
              <AlertTriangle className="text-warning shrink-0" size={20} />
              <div>
                <h4 className="text-xs font-bold text-warning uppercase mb-1">Bottleneck Predicted</h4>
                <p className="text-[10px] text-white/60">Ministry of Finance shows a 90% chance of 'Third Party' exemption claim based on your query structure.</p>
              </div>
            </div>
          </GlassCard>
        </div>

        <GlassCard className="lg:col-span-2 relative overflow-hidden flex flex-col items-center justify-center min-h-[400px]">
          <div className="absolute inset-0 bg-[radial-gradient(circle_at_center,rgba(0,212,255,0.05)_0%,transparent_70%)]" />
          <div className="relative z-10 text-center space-y-6">
            <div className="w-24 h-24 rounded-full border-2 border-white/5 flex items-center justify-center mx-auto relative">
              <Building2 size={40} className="text-white/20" />
              <div className="absolute inset-0 rounded-full border-t-2 border-primary animate-spin" />
            </div>
            <div>
              <h3 className="text-xl font-bold font-display">Ready for Execution</h3>
              <p className="text-white/40 text-xs mt-2 max-w-sm mx-auto">The engine will run 10,000 iterations to find the most successful path for your appeal.</p>
            </div>
            <div className="flex justify-center gap-8">
              <div className="text-center">
                <div className="text-2xl font-bold text-primary">--</div>
                <div className="text-[8px] text-white/30 uppercase font-bold mt-1">Simulated Days</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-secondary">--</div>
                <div className="text-[8px] text-white/30 uppercase font-bold mt-1">Success Prob.</div>
              </div>
            </div>
          </div>
        </GlassCard>
      </div>
    </div>
  );
};

export default GovSimulation;
