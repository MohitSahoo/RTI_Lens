import React from 'react';
import { motion } from 'framer-motion';
import { Database, Terminal, Shield, Cpu, Activity, Clock, Lock, Globe } from 'lucide-react';
import { GlassCard } from '../ui/GlassCard';

const BlockchainTracker: React.FC = () => {
  const transactions = [
    { hash: '0x8f2e...9a1c', authority: 'Min. of Defense', type: 'RTI FILING', status: 'CONFIRMED', time: '2m ago' },
    { hash: '0x3c1d...4b8e', authority: 'Min. of Finance', type: 'APPEAL LODGED', status: 'PENDING', time: '14m ago' },
    { hash: '0x7a4f...2d0b', authority: 'Min. of Home', type: 'RESPONSE LOG', status: 'CONFIRMED', time: '1h ago' },
    { hash: '0x1e9b...6c5a', authority: 'CIC New Delhi', type: 'RULING SEAL', status: 'CONFIRMED', time: '3h ago' },
  ];

  return (
    <div className="space-y-8 font-mono">
      <div className="flex justify-between items-end">
        <div>
          <div className="flex items-center gap-3 mb-2">
            <div className="w-2 h-2 rounded-full bg-success animate-pulse" />
            <h1 className="text-3xl font-bold font-display tracking-tight uppercase">Immutable RTI Chain</h1>
          </div>
          <p className="text-success/50 text-xs">Node Status: <span className="text-success">ACTIVE</span> | Sync: 100% | Network: RTI-Lense-v1</p>
        </div>
        <div className="flex gap-4">
          <div className="px-4 py-2 bg-white/5 border border-white/10 rounded-lg flex items-center gap-3">
            <div className="text-right">
              <div className="text-[8px] text-white/30 uppercase">Network Hashrate</div>
              <div className="text-xs font-bold text-primary">124.5 TH/s</div>
            </div>
            <Cpu size={20} className="text-primary" />
          </div>
        </div>
      </div>

      <div className="grid lg:grid-cols-4 gap-6">
        {[
          { label: 'Total Blocks', val: '412,892', icon: Database },
          { label: 'Verified Filings', val: '84,120', icon: Shield },
          { label: 'Transparency Score', val: '99.4%', icon: Globe },
          { label: 'Pending Tx', val: '14', icon: Clock }
        ].map((stat, i) => (
          <GlassCard key={i} className="border-success/20 bg-success/5">
            <div className="flex items-center gap-4">
              <div className="p-3 rounded-lg bg-success/10 text-success">
                <stat.icon size={20} />
              </div>
              <div>
                <div className="text-[10px] text-success/40 uppercase tracking-widest">{stat.label}</div>
                <div className="text-xl font-bold text-success">{stat.val}</div>
              </div>
            </div>
          </GlassCard>
        ))}
      </div>

      <div className="grid lg:grid-cols-3 gap-8">
        <GlassCard className="lg:col-span-2 p-0 border-white/5 overflow-hidden">
          <div className="bg-white/5 p-4 flex justify-between items-center border-b border-white/5">
            <div className="flex items-center gap-2">
              <Terminal size={16} className="text-success" />
              <span className="text-[10px] font-bold uppercase tracking-widest">Real-time Transaction Feed</span>
            </div>
            <div className="flex gap-1">
              <div className="w-2 h-2 rounded-full bg-white/10" />
              <div className="w-2 h-2 rounded-full bg-white/10" />
              <div className="w-2 h-2 rounded-full bg-white/10" />
            </div>
          </div>
          <div className="p-0">
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="border-b border-white/5 text-white/20 uppercase">
                  <th className="p-4 font-normal">Tx Hash</th>
                  <th className="p-4 font-normal">Authority</th>
                  <th className="p-4 font-normal">Event Type</th>
                  <th className="p-4 font-normal">Status</th>
                  <th className="p-4 font-normal">Time</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/5">
                {transactions.map((tx, i) => (
                  <tr key={i} className="hover:bg-white/5 transition-colors group">
                    <td className="p-4 text-primary font-bold">{tx.hash}</td>
                    <td className="p-4 text-white/60">{tx.authority}</td>
                    <td className="p-4">
                      <span className="px-2 py-0.5 rounded bg-white/5 border border-white/10 text-[9px] font-bold">
                        {tx.type}
                      </span>
                    </td>
                    <td className="p-4">
                      <div className="flex items-center gap-2">
                        <div className={`w-1.5 h-1.5 rounded-full ${tx.status === 'CONFIRMED' ? 'bg-success shadow-[0_0_8px_#00FF9D]' : 'bg-warning shadow-[0_0_8px_#FFC857]'}`} />
                        <span className={tx.status === 'CONFIRMED' ? 'text-success' : 'text-warning'}>{tx.status}</span>
                      </div>
                    </td>
                    <td className="p-4 text-white/30">{tx.time}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </GlassCard>

        <div className="space-y-6">
          <GlassCard className="border-primary/20 bg-primary/5">
            <h3 className="text-xs font-bold uppercase tracking-widest mb-4 flex items-center gap-2">
              <Lock size={14} className="text-primary" /> Immutable Proof
            </h3>
            <p className="text-[10px] text-white/50 leading-relaxed mb-4">
              Every RTI filing is hashed and anchored to the Solana mainnet. This creates a cryptographically verifiable timeline that public authorities cannot alter.
            </p>
            <div className="p-3 rounded-lg bg-black/40 border border-white/5 space-y-2">
              <div className="flex justify-between text-[8px] uppercase font-bold text-white/20">
                <span>Block Height</span>
                <span>284,129,031</span>
              </div>
              <div className="w-full bg-white/5 h-1 rounded-full overflow-hidden">
                <motion.div 
                  initial={{ width: '60%' }}
                  animate={{ width: '100%' }}
                  transition={{ duration: 10, repeat: Infinity }}
                  className="bg-primary h-full"
                />
              </div>
            </div>
          </GlassCard>

          <GlassCard className="border-secondary/20">
            <h3 className="text-xs font-bold uppercase tracking-widest mb-4">Network Activity</h3>
            <div className="h-32 flex items-end gap-1 px-2">
              {[40, 70, 45, 90, 65, 80, 50, 85, 60, 75, 40, 95].map((h, i) => (
                <motion.div 
                  key={i}
                  initial={{ height: 0 }}
                  animate={{ height: `${h}%` }}
                  transition={{ delay: i * 0.05, duration: 1 }}
                  className="flex-1 bg-gradient-to-t from-secondary/20 to-secondary rounded-t-sm"
                />
              ))}
            </div>
          </GlassCard>
        </div>
      </div>
    </div>
  );
};

export default BlockchainTracker;
