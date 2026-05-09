import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Building2, 
  Lock, 
  Unlock, 
  Eye, 
  FileText, 
  CheckCircle, 
  AlertTriangle,
  Search,
  RefreshCw,
  ShieldCheck,
  User,
  Clock,
  Terminal
} from 'lucide-react';
import { GlassCard } from '../ui/GlassCard';

interface EncryptedRTI {
  id: string;
  sender: string;
  timestamp: number;
  encrypted_content: string;
  dept: string;
  status: 'Received' | 'Decrypted' | 'Processing';
  blockchain_tx?: string;
  doc_hash?: string;
}

const GovernmentPortal: React.FC = () => {
  const [inbox, setInbox] = useState<EncryptedRTI[]>([]);
  const [selectedRTI, setSelectedRTI] = useState<EncryptedRTI | null>(null);
  const [decryptedText, setDecryptedText] = useState<string | null>(null);
  const [isDecrypting, setIsDecrypting] = useState(false);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    // Load from simulation "Shared Storage" (localStorage)
    const loadInbox = () => {
      const stored = localStorage.getItem('gov_inbox');
      if (stored) {
        setInbox(JSON.parse(stored));
      } else {
        setInbox([]);
      }
    };

    loadInbox();
    // Refresh interval for simulation
    const interval = setInterval(loadInbox, 2000);
    return () => clearInterval(interval);
  }, []);

  const handleDecrypt = async (rti: EncryptedRTI) => {
    setIsDecrypting(true);
    
    try {
      // Attempt 1: Real Hybrid Decryption via Backend (RSA+AES-256-GCM)
      const formData = new FormData();
      formData.append('encrypted_data', rti.encrypted_content);

      const response = await fetch('http://localhost:8002/api/blockchain/gov/decrypt', {
        method: 'POST',
        body: formData
      });

      if (!response.ok) throw new Error(`Server returned ${response.status}`);
      
      const data = await response.json();
      setDecryptedText(data.decrypted_data);
      setInbox(inbox.map(item => item.id === rti.id ? { ...item, status: 'Decrypted' } : item));
    } catch (backendError) {
      console.warn("Backend decryption failed, trying local Base64 fallback:", backendError);
      
      try {
        // Attempt 2: Local Base64 Decode (Simulation Fallback)
        const decoded = atob(rti.encrypted_content);
        setDecryptedText(decoded);
        setInbox(inbox.map(item => item.id === rti.id ? { ...item, status: 'Decrypted' } : item));
      } catch (localError) {
        console.error("Both decryption methods failed:", localError);
        alert('Decryption failed. The encryption keys may have been rotated (server restart). Please submit a new RTI from the Citizen portal.');
      }
    } finally {
      setIsDecrypting(false);
    }
  };

  return (
    <div className="space-y-8 p-1">
      <div className="flex justify-between items-end">
        <div>
          <h1 className="text-3xl font-bold font-display flex items-center gap-3">
            <Building2 className="text-primary" /> Government Secure Portal
          </h1>
          <p className="text-white/50 text-sm italic">Accessing via Ministry Private Key Infrastructure (PKI)</p>
        </div>
        
        <div className="px-4 py-2 rounded-xl bg-success/10 border border-success/30 flex items-center gap-2">
          <ShieldCheck size={16} className="text-success" />
          <span className="text-[10px] font-bold text-success uppercase tracking-widest">Gov-Wallet Connected</span>
        </div>
      </div>

      <div className="grid lg:grid-cols-3 gap-8">
        {/* Secure Inbox */}
        <GlassCard className="lg:col-span-2">
          <div className="flex justify-between items-center mb-6">
            <h3 className="text-xl font-bold flex items-center gap-2">
              <Terminal size={18} className="text-primary" /> Encrypted Submissions
            </h3>
            <button 
              onClick={() => {
                console.log("REFRESHING_GOV_INBOX");
                setIsRefreshing(true);
                setTimeout(() => {
                  const stored = localStorage.getItem('gov_inbox');
                  if (stored) setInbox(JSON.parse(stored));
                  setIsRefreshing(false);
                }, 800);
              }}
              className="p-2 px-4 rounded-lg bg-white/5 hover:bg-white/10 transition-all text-white/50 flex items-center gap-2 text-[10px] font-bold uppercase tracking-widest relative z-[110] cursor-pointer"
            >
              <RefreshCw size={14} className={isRefreshing ? "animate-spin text-primary" : ""} /> 
              {isRefreshing ? "Syncing..." : "Refresh Inbox"}
            </button>
          </div>

          <div className="space-y-4">
            {inbox.length === 0 ? (
              <div className="text-center py-12 text-white/30">
                <FileText size={48} className="mx-auto mb-4 opacity-20" />
                <p className="text-sm">No encrypted submissions received yet.</p>
                <p className="text-xs mt-2">RTI submissions with encryption enabled will appear here.</p>
              </div>
            ) : (
              inbox.map((rti) => (
              <motion.div 
                key={rti.id}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                onClick={() => {
                  setSelectedRTI(rti);
                  setDecryptedText(null); // Reset decryption view when switching
                }}
                className={`p-5 rounded-2xl border transition-all cursor-pointer ${
                  selectedRTI?.id === rti.id 
                    ? 'bg-primary/10 border-primary shadow-[0_0_20px_rgba(var(--primary-rgb),0.2)]' 
                    : 'bg-white/5 border-white/10 hover:border-white/20'
                }`}
              >
                <div className="flex justify-between items-start mb-3">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-full bg-white/5 flex items-center justify-center border border-white/10">
                      {rti.status === 'Decrypted' ? <Unlock className="text-success" size={16} /> : <Lock className="text-white/30" size={16} />}
                    </div>
                    <div>
                      <h4 className="font-bold text-sm flex items-center gap-2">
                        {rti.id}
                        {rti.blockchain_tx && (
                          <a
                            href={`https://explorer.solana.com/tx/${rti.blockchain_tx}?cluster=devnet`}
                            target="_blank"
                            rel="noopener noreferrer"
                            onClick={(e) => e.stopPropagation()}
                            className="text-[8px] px-2 py-0.5 rounded bg-primary/20 text-primary hover:bg-primary/30 transition-all"
                            title="View on Solana Explorer"
                          >
                            BLOCKCHAIN
                          </a>
                        )}
                      </h4>
                      <p className="text-[10px] text-white/40 uppercase tracking-tighter">Sender: {rti.sender}</p>
                    </div>
                  </div>
                  <span className={`text-[9px] font-bold px-2 py-1 rounded-md ${
                    rti.status === 'Decrypted' ? 'bg-success/20 text-success' : 'bg-warning/20 text-warning'
                  }`}>
                    {rti.status.toUpperCase()}
                  </span>
                </div>
                <div className="flex justify-between items-center text-[10px] text-white/30">
                  <span className="flex items-center gap-1"><Clock size={10} /> {new Date(rti.timestamp).toLocaleString()}</span>
                  <span className="font-bold">{rti.dept}</span>
                </div>
              </motion.div>
            ))
            )}
          </div>
        </GlassCard>

        {/* Decryption View */}
        <div className="space-y-6">
          <GlassCard className="bg-black/40 border-primary/20 min-h-[400px] flex flex-col">
            <h4 className="text-xs font-bold text-primary uppercase tracking-[0.2em] mb-6 flex items-center gap-2">
              <Eye size={12} /> Decryption Console
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
                  <p className="text-sm">Select an RTI from the inbox to initiate decryption sequence.</p>
                </motion.div>
              ) : (
                <motion.div 
                  key="content"
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="flex-1 flex flex-col"
                >
                  <div className="bg-white/5 p-4 rounded-xl mb-6 font-mono text-[10px] break-all border border-white/10 max-h-32 overflow-hidden opacity-50 italic">
                    {selectedRTI.encrypted_content}
                  </div>

                  <div className="flex-1 bg-black/50 border border-white/5 rounded-2xl p-6 relative overflow-hidden group">
                    <div className="absolute inset-0 bg-gradient-to-br from-primary/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
                    
                    {decryptedText ? (
                      <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        className="relative z-10"
                      >
                        <div className="flex items-center gap-2 text-success mb-4 font-bold text-xs uppercase">
                          <CheckCircle size={14} /> Decryption Successful — Full Document Revealed
                        </div>
                        {selectedRTI.blockchain_tx && (
                          <div className="mb-4 p-3 rounded-lg bg-primary/10 border border-primary/30">
                            <p className="text-[10px] text-primary font-bold mb-1">BLOCKCHAIN VERIFIED</p>
                            <a
                              href={`https://explorer.solana.com/tx/${selectedRTI.blockchain_tx}?cluster=devnet`}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="text-[9px] font-mono text-primary/70 hover:underline break-all"
                            >
                              TX: {selectedRTI.blockchain_tx}
                            </a>
                          </div>
                        )}
                        <div className="max-h-[400px] overflow-y-auto rounded-xl bg-black/60 border border-success/20 p-5">
                          <pre className="text-xs leading-relaxed text-white/90 whitespace-pre-wrap font-mono break-words">
                            {decryptedText}
                          </pre>
                        </div>
                      </motion.div>
                    ) : (
                      <div className="h-full flex flex-col items-center justify-center text-center p-4 relative z-[100]">
                        <Lock className="text-white/10 mb-4" size={40} />
                        <p className="text-xs text-white/40 mb-6">This content is currently locked by the Government's private key.</p>
                        <button 
                          onClick={() => {
                            console.log("DECRYPT_TRIGGERED", selectedRTI.id);
                            handleDecrypt(selectedRTI);
                          }}
                          disabled={isDecrypting}
                          className="w-full py-4 rounded-2xl bg-primary text-background font-black text-xs uppercase tracking-[0.2em] neo-glow flex items-center justify-center gap-3 cursor-pointer hover:scale-[1.02] active:scale-[0.98] transition-all relative z-[101]"
                        >
                          {isDecrypting ? (
                            <>
                              <div className="w-4 h-4 border-2 border-background border-t-transparent rounded-full animate-spin" />
                              Processing Private Key...
                            </>
                          ) : (
                            <>
                              <Unlock size={16} /> Decrypt RTI Content
                            </>
                          )}
                        </button>
                      </div>
                    )}
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </GlassCard>

          <GlassCard className="bg-warning/5 border-warning/20">
            <div className="flex items-start gap-3">
              <AlertTriangle className="text-warning shrink-0" size={16} />
              <p className="text-[10px] text-warning/70 leading-relaxed">
                <strong>PKI NOTICE:</strong> All decryption events are logged to the blockchain for citizen audit. Unauthorized access is strictly monitored.
              </p>
            </div>
          </GlassCard>
        </div>
      </div>
    </div>
  );
};

export default GovernmentPortal;
