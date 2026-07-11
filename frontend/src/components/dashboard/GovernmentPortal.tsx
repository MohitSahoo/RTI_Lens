import React, { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Building2,
  CheckCircle,
  Clock,
  FileText,
  RefreshCw,
  Search,
  ShieldCheck,
  Terminal,
} from 'lucide-react';
import { GlassCard } from '../ui/GlassCard';

interface SolanaRecord {
  id: string;
  timestamp: number;
  dept: string;
  status: string;
  tx: string;
  content?: string;
}

const GovernmentPortal: React.FC = () => {
  const [inbox, setInbox] = useState<SolanaRecord[]>([]);
  const [selectedRTI, setSelectedRTI] = useState<SolanaRecord | null>(null);
  const [isRefreshing, setIsRefreshing] = useState(false);

  useEffect(() => {
    const loadLedger = async () => {
      try {
        const wallet = window.localStorage.getItem('solana_wallet');
        if (!wallet) {
          setInbox([]);
          return;
        }

        const response = await fetch(`/api/blockchain/history/${wallet}`);
        if (response.ok) {
          const data = await response.json();
          setInbox((data || []).map((item: any) => ({
            id: item.id,
            timestamp: item.timestamp,
            dept: item.dept,
            status: item.status || 'VERIFIED',
            tx: item.tx,
            content: item.content
          })));
        } else {
          setInbox([]);
        }
      } catch (e) {
        console.error('Failed to load Solana ledger history', e);
        setInbox([]);
      }
    };

    loadLedger();
    const interval = setInterval(loadLedger, 3000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="space-y-8 p-1">
      <div className="flex justify-between items-end">
        <div>
          <h1 className="text-3xl font-bold font-display flex items-center gap-3">
            <Building2 className="text-primary" /> Government Secure Portal
          </h1>
          <p className="text-white/50 text-sm italic">Reading the Solana filing ledger for verified RTI submissions.</p>
        </div>

        <div className="px-4 py-2 rounded-xl bg-success/10 border border-success/30 flex items-center gap-2">
          <ShieldCheck size={16} className="text-success" />
          <span className="text-[10px] font-bold text-success uppercase tracking-widest">Ledger Sync Active</span>
        </div>
      </div>

      <div className="grid lg:grid-cols-3 gap-8">
        <GlassCard className="lg:col-span-2">
          <div className="flex justify-between items-center mb-6">
            <h3 className="text-xl font-bold flex items-center gap-2">
              <Terminal size={18} className="text-primary" /> On-Chain Filings
            </h3>
            <button
              onClick={() => {
                setIsRefreshing(true);
                setTimeout(() => setIsRefreshing(false), 800);
              }}
              className="p-2 px-4 rounded-lg bg-white/5 hover:bg-white/10 transition-all text-white/50 flex items-center gap-2 text-[10px] font-bold uppercase tracking-widest"
            >
              <RefreshCw size={14} className={isRefreshing ? 'animate-spin text-primary' : ''} />
              {isRefreshing ? 'Syncing...' : 'Refresh Ledger'}
            </button>
          </div>

          <div className="space-y-4">
            {inbox.length === 0 ? (
              <div className="text-center py-12 text-white/30">
                <FileText size={48} className="mx-auto mb-4 opacity-20" />
                <p className="text-sm">No Solana submissions received yet.</p>
                <p className="text-xs mt-2">RTI filing hashes from the citizen portal will appear here.</p>
              </div>
            ) : (
              inbox.map((rti) => (
                <motion.div
                  key={rti.id}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  onClick={() => setSelectedRTI(rti)}
                  className={`p-5 rounded-2xl border transition-all cursor-pointer ${
                    selectedRTI?.id === rti.id
                      ? 'bg-primary/10 border-primary shadow-[0_0_20px_rgba(var(--primary-rgb),0.2)]'
                      : 'bg-white/5 border-white/10 hover:border-white/20'
                  }`}
                >
                  <div className="flex justify-between items-start mb-3">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 rounded-full bg-white/5 flex items-center justify-center border border-white/10">
                        <CheckCircle className="text-success" size={16} />
                      </div>
                      <div>
                        <h4 className="font-bold text-sm flex items-center gap-2">
                          {rti.id}
                          {rti.tx && (
                            <a
                              href={`https://explorer.solana.com/tx/${rti.tx}?cluster=devnet`}
                              target="_blank"
                              rel="noopener noreferrer"
                              onClick={(e) => e.stopPropagation()}
                              className="text-[8px] px-2 py-0.5 rounded bg-primary/20 text-primary hover:bg-primary/30 transition-all"
                              title="View on Solana Explorer"
                            >
                              SOLANA
                            </a>
                          )}
                        </h4>
                        <p className="text-[10px] text-white/40 uppercase tracking-tighter">TX: {rti.tx}</p>
                      </div>
                    </div>
                    <span className="text-[9px] font-bold px-2 py-1 rounded-md bg-success/20 text-success">
                      VERIFIED
                    </span>
                  </div>
                  <div className="flex justify-between items-center text-[10px] text-white/30">
                    <span className="flex items-center gap-1">
                      <Clock size={10} /> {new Date(rti.timestamp).toLocaleDateString()}
                    </span>
                    <span className="font-bold">{rti.dept}</span>
                  </div>
                </motion.div>
              ))
            )}
          </div>
        </GlassCard>

        <div className="space-y-6">
          <GlassCard className="bg-black/40 border-primary/20 min-h-[400px] flex flex-col">
            <h4 className="text-xs font-bold text-primary uppercase tracking-[0.2em] mb-6 flex items-center gap-2">
              <Search size={12} /> Ledger Inspector
            </h4>

            <AnimatePresence mode="wait">
              {!selectedRTI ? (
                <motion.div
                  key="empty"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  className="flex-1 flex flex-col items-center justify-center text-center p-8 opacity-30"
                >
                  <Search size={48} className="mb-4" />
                  <p className="text-sm">Select a filing to inspect its Solana transaction record.</p>
                </motion.div>
              ) : (
                <motion.div
                  key="content"
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="flex-1 flex flex-col gap-4"
                >
                  <div className="p-4 rounded-xl bg-primary/10 border border-primary/30">
                    <p className="text-[10px] text-primary font-bold mb-1">DEPARTMENT</p>
                    <p className="text-xs text-white/80">{selectedRTI.dept}</p>
                  </div>
                  <div className="p-4 rounded-xl bg-white/5 border border-white/10">
                    <p className="text-[10px] text-white/50 font-bold mb-1">TRANSACTION HASH</p>
                    <a
                      href={`https://explorer.solana.com/tx/${selectedRTI.tx}?cluster=devnet`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-[9px] font-mono text-primary/70 hover:underline break-all"
                    >
                      {selectedRTI.tx}
                    </a>
                  </div>
                  <div className="p-4 rounded-xl bg-black/50 border border-white/10">
                    <p className="text-[10px] text-white/50 font-bold mb-1">STATUS</p>
                    <p className="text-xs text-success">{selectedRTI.status}</p>
                  </div>
                  {selectedRTI.content && (
                    <div className="p-4 rounded-xl bg-white/5 border border-white/10 flex-1 flex flex-col min-h-[220px]">
                      <p className="text-[10px] text-white/50 font-bold mb-2">ANCHORED DOCUMENT DRAFT</p>
                      <div className="flex-1 overflow-y-auto max-h-[280px] bg-black/30 rounded-lg p-3 font-mono text-[11px] leading-relaxed text-white/70 whitespace-pre-wrap">
                        {selectedRTI.content}
                      </div>
                    </div>
                  )}
                  <div className="text-[10px] text-white/35 leading-5">
                    This portal reads the Solana ledger directly. The filing is represented by a memo-anchored transaction hash, which can be verified in the explorer.
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </GlassCard>
        </div>
      </div>
    </div>
  );
};

export default GovernmentPortal;
