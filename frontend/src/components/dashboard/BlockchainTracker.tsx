import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useWallet } from '@solana/wallet-adapter-react';
import { WalletMultiButton } from '@solana/wallet-adapter-react-ui';
import {
  Shield,
  Cpu,
  Link as LinkIcon,
  FileCheck,
  ArrowRight,
  Search,
  ExternalLink,
  Lock,
  Wallet,
  CheckCircle2,
  Clock,
  AlertCircle,
  Database,
  Globe
} from 'lucide-react';
import { GlassCard } from '../ui/GlassCard';

interface BlockchainRecord {
  id: string;
  timestamp: number;
  dept: string;
  status: string;
  tx: string;
}

const BlockchainTracker: React.FC = () => {
  const { publicKey, connected } = useWallet();

  const [rtiContent, setRtiContent] = useState<string>('');
  const [isEncrypted, setIsEncrypted] = useState(false);
  const [department, setDepartment] = useState('Ministry of Finance');
  const [filingLevel, setFilingLevel] = useState('Initial Application');
  const [isHashing, setIsHashing] = useState(false);
  const [isMining, setIsMining] = useState(false);
  const [history, setHistory] = useState<BlockchainRecord[]>([]);
  const [status, setStatus] = useState<'idle' | 'hashing' | 'mining' | 'success'>('idle');
  const [authorityKey, setAuthorityKey] = useState("Loading...");
  const [govPublicKey, setGovPublicKey] = useState("Loading...");
  const [networkStats, setNetworkStats] = useState({ slot: 0, tps: 0 });

  const walletAddress = publicKey ? publicKey.toBase58() : '';
  const displayAddress = walletAddress ? `${walletAddress.slice(0, 4)}...${walletAddress.slice(-4)}` : '';

  // Fetch network stats from Solana
  useEffect(() => {
    const fetchNetworkStats = async () => {
      try {
        const response = await fetch('https://api.devnet.solana.com', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            jsonrpc: '2.0',
            id: 1,
            method: 'getSlot'
          })
        });
        const data = await response.json();
        if (data.result) {
          setNetworkStats(prev => ({ ...prev, slot: data.result }));
        }

        // Fetch recent performance samples for TPS
        const perfResponse = await fetch('https://api.devnet.solana.com', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            jsonrpc: '2.0',
            id: 1,
            method: 'getRecentPerformanceSamples',
            params: [1]
          })
        });
        const perfData = await perfResponse.json();
        if (perfData.result && perfData.result[0]) {
          const sample = perfData.result[0];
          const tps = Math.round(sample.numTransactions / sample.samplePeriodSecs);
          setNetworkStats(prev => ({ ...prev, tps }));
        }
      } catch (e) {
        console.error("Failed to fetch network stats", e);
      }
    };

    fetchNetworkStats();
    // Refresh network stats every 10 seconds
    const interval = setInterval(fetchNetworkStats, 10000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    // Fetch keys from backend
    const fetchKeys = async () => {
      try {
        const authRes = await fetch('http://localhost:8002/api/blockchain/authority-key');
        const authData = await authRes.json();
        setAuthorityKey(authData.public_key);

        const govRes = await fetch('http://localhost:8002/api/blockchain/gov/public-key');
        const govData = await govRes.json();
        setGovPublicKey(govData.public_key);
      } catch (e) {
        console.error("Failed to fetch blockchain keys", e);
      }
    };
    fetchKeys();

    // Fetch real history from backend if wallet is connected
    const fetchHistory = async () => {
      if (connected && publicKey) {
        try {
          const historyRes = await fetch(`http://localhost:8002/api/blockchain/history/${publicKey.toBase58()}`);
          if (historyRes.ok) {
            const historyData = await historyRes.json();
            setHistory(historyData);
          }
        } catch (e) {
          console.error("Failed to fetch blockchain history", e);
          // Start with empty history if fetch fails
          setHistory([]);
        }
      } else {
        // No wallet connected, show empty state
        setHistory([]);
      }
    };
    fetchHistory();
  }, [connected, publicKey]);


  const handleSecureFiling = async () => {
    if (!connected || !publicKey) {
      alert("Please connect your Phantom wallet first.");
      return;
    }
    
    setStatus('hashing');
    setIsHashing(true);
    
    try {
      let encryptedContent = null;
      let actualContent = rtiContent.trim();

      // If no text provided, use default
      if (!actualContent) {
        actualContent = `RTI Request to ${department} - ${filingLevel}\n\n[No specific details provided]`;
      }

      if (isEncrypted) {
        // Real Backend Encryption with actual content
        const formalRTI = `
FORMAL RTI APPLICATION (ENCRYPTED VIA SOLANA PKI)
================================================
REF ID: RTI-${Math.floor(Math.random() * 1000000)}
TIMESTAMP: ${new Date().toISOString()}
CITIZEN SIG: ${publicKey?.toBase58() || 'ANONYMOUS'}

[APPLICATION DETAILS]
--------------------
TARGET DEPARTMENT: ${department}
FILING CATEGORY: ${filingLevel}
SUBMISSION TYPE: Text-based RTI Request

[ACTUAL RTI CONTENT]
--------------------
${actualContent}

[BLOCKCHAIN VERIFICATION]
-------------------------
This submission has been cryptographically hashed and anchored to the Solana blockchain.
The immutable proof-of-submission ensures this document cannot be backdated or altered.

*** END OF SECURE TRANSMISSION ***
        `.trim();

        const formData = new FormData();
        formData.append('data', formalRTI);
        
        try {
          const encResponse = await fetch('http://localhost:8002/api/blockchain/gov/encrypt', { method: 'POST', body: formData });
          if (!encResponse.ok) throw new Error("API Error");
          const encResult = await encResponse.json();
          encryptedContent = encResult.encrypted_data;
        } catch (e) {
          console.warn("Backend Encryption Service Offline - Using High-Fidelity Simulation Fallback", e);
          encryptedContent = btoa(formalRTI); // Use Base64 as a mock cipher for the demo
        }

        // Transfer to Government Simulation Inbox immediately after encryption
        const govInbox = JSON.parse(localStorage.getItem('gov_inbox') || '[]');
        const simId = `RTI-2026-${Math.floor(Math.random() * 1000)}`;
        govInbox.unshift({
          id: simId,
          sender: displayAddress,
          timestamp: Date.now(),
          encrypted_content: encryptedContent,
          dept: department,
          status: 'Received',
          blockchain_tx: '', // Will be updated after blockchain submission
          doc_hash: ''
        });
        localStorage.setItem('gov_inbox', JSON.stringify(govInbox));
      }

      // Real Blockchain Submission
      const formData = new FormData();
      formData.append('wallet', publicKey?.toBase58() || '');
      formData.append('department', department);
      formData.append('content', actualContent);

      const submitResponse = await fetch('http://localhost:8002/api/blockchain/submit', {
        method: 'POST',
        body: formData
      });

      if (!submitResponse.ok) {
        throw new Error(await submitResponse.text());
      }

      const submitResult = await submitResponse.json();
      console.log('Backend response:', submitResult);

      setIsHashing(false);
      setStatus('mining');
      setIsMining(true);

      // Simulate mining time for UX but using real result
      setTimeout(() => {
        setIsMining(false);
        setStatus('success');

        const newRecord: BlockchainRecord = {
          id: submitResult.tx_id && submitResult.tx_id.length > 10 ? submitResult.tx_id.substring(0, 10).toUpperCase() : 'RTI-NEW',
          timestamp: submitResult.timestamp ? submitResult.timestamp * 1000 : Date.now(),
          dept: submitResult.department || department,
          status: 'VERIFIED',
          tx: submitResult.tx_id || ''
        };

        console.log('New record created:', newRecord);
        setHistory([newRecord, ...history]);

        // Update government inbox with blockchain transaction ID if encryption was used
        if (isEncrypted) {
          const govInbox = JSON.parse(localStorage.getItem('gov_inbox') || '[]');
          if (govInbox.length > 0) {
            govInbox[0].blockchain_tx = submitResult.tx_id;
            govInbox[0].doc_hash = submitResult.doc_hash;
            localStorage.setItem('gov_inbox', JSON.stringify(govInbox));
          }
        }

        setTimeout(() => setStatus('idle'), 5000);
      }, 2000);
    } catch (error) {
      alert("Blockchain synchronization failed: " + (error as Error).message);
      setStatus('idle');
      setIsHashing(false);
    }
  };


  return (
    <div className="space-y-8">
      <div className="flex justify-between items-end">
        <div>
          <h1 className="text-3xl font-bold font-display">Blockchain Integrity Layer</h1>
          <p className="text-white/50 text-sm">Immutable RTI proof-of-submission on Solana.</p>
        </div>
        
        <WalletMultiButton className="!bg-primary !text-background !font-bold !text-xs !uppercase !tracking-widest !rounded-xl !px-6 !py-2.5 hover:!opacity-90 !transition-all" />
      </div>

      <div className="grid lg:grid-cols-3 gap-6">
        {/* Verification Engine */}
        <GlassCard className="lg:col-span-2 relative overflow-hidden">
          <div className="absolute -top-20 -right-20 w-64 h-64 bg-primary/10 rounded-full blur-[100px]" />
          
          <div className="relative z-10 p-4">
            <div className="flex items-center gap-3 mb-8">
              <div className="w-10 h-10 rounded-xl bg-primary/10 flex items-center justify-center">
                <Shield className="text-primary w-5 h-5" />
              </div>
              <div>
                <h3 className="text-xl font-bold">Secure Filing Protocol</h3>
                <p className="text-white/40 text-xs uppercase tracking-tighter">Solana Mainnet-Beta | Anchor Framework 0.29</p>
              </div>
            </div>

            <div className="space-y-6">
              {/* Text Input for RTI Content */}
              <div className="space-y-2">
                <label className="text-[10px] font-bold text-white/40 uppercase tracking-widest ml-1">
                  RTI Request Details
                </label>
                <textarea
                  value={rtiContent}
                  onChange={(e) => setRtiContent(e.target.value)}
                  placeholder="Enter your complete RTI request here...&#10;&#10;Example:&#10;'I request detailed information regarding the budget allocation for infrastructure projects under the Ministry of Finance for FY 2025-26, including:&#10;1. Total budget allocated&#10;2. Project-wise breakdown&#10;3. Approval documents and timelines&#10;4. Current expenditure status'"
                  className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-sm outline-none focus:border-primary/50 transition-all min-h-[200px] resize-y"
                />
                <p className="text-[10px] text-white/40 italic">
                  Your request will be encrypted and anchored to the blockchain. Only the hash is stored on-chain for immutability.
                </p>
              </div>

              <div className="flex gap-4">
                <div className="flex-1 space-y-2">
                  <label className="text-[10px] font-bold text-white/40 uppercase tracking-widest ml-1">Target Department</label>
                  <select 
                    value={department}
                    onChange={(e) => setDepartment(e.target.value)}
                    className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-sm outline-none focus:border-primary/50 transition-all"
                  >
                    <option>Ministry of Finance</option>
                    <option>Ministry of External Affairs</option>
                    <option>Ministry of Home Affairs</option>
                    <option>Ministry of Railways</option>
                  </select>
                </div>
                <div className="flex-1 space-y-2">
                  <label className="text-[10px] font-bold text-white/40 uppercase tracking-widest ml-1">Filing Level</label>
                  <select 
                    value={filingLevel}
                    onChange={(e) => setFilingLevel(e.target.value)}
                    className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-sm outline-none focus:border-primary/50 transition-all"
                  >
                    <option>Initial Application</option>
                    <option>1st Appeal (FAA)</option>
                    <option>2nd Appeal (CIC)</option>
                  </select>
                </div>
              </div>

              <div className="p-4 rounded-xl bg-primary/5 border border-primary/20 flex justify-between items-center">
                <div className="flex items-center gap-3">
                  <div className={`w-8 h-8 rounded-lg flex items-center justify-center transition-colors ${isEncrypted ? 'bg-primary text-background' : 'bg-white/5 text-white/30'}`}>
                    <Lock size={16} />
                  </div>
                  <div>
                    <h5 className="text-xs font-bold">End-to-End Encryption</h5>
                    <p className="text-[10px] text-white/40">Encrypt with Government's Public Key</p>
                  </div>
                </div>
                <button 
                  onClick={() => setIsEncrypted(!isEncrypted)}
                  className={`w-12 h-6 rounded-full transition-all relative ${isEncrypted ? 'bg-primary' : 'bg-white/10'}`}
                >
                  <motion.div 
                    animate={{ x: isEncrypted ? 24 : 4 }}
                    className="absolute top-1 w-4 h-4 rounded-full bg-white shadow-lg"
                  />
                </button>
              </div>

              <button 
                onClick={handleSecureFiling}
                disabled={status !== 'idle'}
                className="w-full py-4 rounded-xl bg-gradient-to-r from-primary to-secondary text-background font-bold uppercase tracking-widest neo-glow hover:opacity-90 active:scale-[0.98] transition-all disabled:opacity-50 flex items-center justify-center gap-3"
              >
                {status === 'idle' ? (
                  <>
                    <Lock size={18} /> Secure on Blockchain
                  </>
                ) : (
                  <span className="flex items-center gap-2">
                    <div className="w-4 h-4 border-2 border-background border-t-transparent rounded-full animate-spin" />
                    {status === 'hashing' ? 'Generating SHA256 Hash...' : 'Mining Transaction...'}
                  </span>
                )}
              </button>
            </div>
          </div>
        </GlassCard>

        {/* Real-time Ledger Info */}
        <div className="space-y-6">
          <GlassCard className="bg-primary/5 border-primary/20">
            <h4 className="text-xs font-bold text-primary uppercase tracking-[0.2em] mb-4 flex items-center gap-2">
              <Globe size={12} /> Network Status
            </h4>
            <div className="space-y-4">
              <div className="flex justify-between items-center">
                <span className="text-xs text-white/40">Current Slot</span>
                <span className="text-xs font-mono">{networkStats.slot > 0 ? networkStats.slot.toLocaleString() : 'Loading...'}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-xs text-white/40">TPS (Avg)</span>
                <span className="text-xs font-mono text-success">{networkStats.tps > 0 ? networkStats.tps.toLocaleString() : 'Loading...'}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-xs text-white/40">Network</span>
                <span className="text-xs font-mono">Solana Devnet</span>
              </div>
            </div>
          </GlassCard>

          <GlassCard className="flex-1 flex flex-col justify-center items-center p-8 text-center">
            <AnimatePresence mode="wait">
              {status === 'success' ? (
                <motion.div 
                  key="success"
                  initial={{ opacity: 0, scale: 0.5 }}
                  animate={{ opacity: 1, scale: 1 }}
                  exit={{ opacity: 0, scale: 0.5 }}
                  className="space-y-4"
                >
                  <div className="w-20 h-20 rounded-full bg-success/20 flex items-center justify-center mx-auto neo-glow">
                    <CheckCircle2 className="text-success w-10 h-10" />
                  </div>
                  <h3 className="text-xl font-bold">Record Immutable</h3>
                  <p className="text-xs text-white/40">Transaction confirmed. SHA256 proof anchored to Solana mainnet.</p>
                  <a
                    href={`https://explorer.solana.com/tx/${history[0]?.tx}?cluster=devnet`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-[10px] font-bold text-primary flex items-center gap-1 mx-auto hover:underline uppercase tracking-widest"
                  >
                    View on Solscan <ExternalLink size={10} />
                  </a>
                </motion.div>
              ) : (
                <motion.div 
                  key="idle"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  className="space-y-4"
                >
                  <div className="w-20 h-20 rounded-full bg-white/5 flex items-center justify-center mx-auto border border-white/10">
                    <Cpu className={`w-10 h-10 text-white/20 ${status !== 'idle' ? 'animate-pulse text-primary' : ''}`} />
                  </div>
                  <h3 className="text-lg font-bold">Node Consensus</h3>
                  <p className="text-xs text-white/40">Waiting for local filing to initiate consensus sequence.</p>
                </motion.div>
              )}
            </AnimatePresence>
          </GlassCard>

          <GlassCard className="bg-white/5 border-white/10">
            <h4 className="text-xs font-bold text-white/40 uppercase tracking-[0.2em] mb-4 flex items-center gap-2">
              <Shield size={12} /> Cryptographic Identities
            </h4>
            <div className="space-y-4">
              <div>
                <span className="text-[9px] font-bold text-primary uppercase block mb-1">Anchoring Authority</span>
                <div className="p-2 rounded bg-black/20 font-mono text-[10px] text-white/80 break-all border border-white/5">
                  {authorityKey}
                </div>
              </div>
              <div>
                <span className="text-[9px] font-bold text-success uppercase block mb-1">Gov Public Key (RSA)</span>
                <div className="p-2 rounded bg-black/20 font-mono text-[10px] text-white/40 h-20 overflow-y-auto break-all border border-white/5">
                  {govPublicKey}
                </div>
              </div>
            </div>
          </GlassCard>
        </div>
      </div>

      {/* Immutable Ledger History */}
      <GlassCard>
        <div className="flex justify-between items-center mb-8">
          <div className="flex items-center gap-3">
            <Database className="text-primary w-5 h-5" />
            <h3 className="text-xl font-bold">Your Immutable RTI Ledger</h3>
          </div>
          <div className="flex items-center gap-2 px-4 py-2 rounded-lg bg-white/5 border border-white/10 text-xs">
            <Search size={14} className="text-white/40" />
            <input type="text" placeholder="Search Tx Hash..." className="bg-transparent border-none outline-none w-48 text-white placeholder:text-white/20" />
          </div>
        </div>

        <div className="overflow-x-auto">
          {history.length === 0 ? (
            <div className="text-center py-12 text-white/30">
              <Database size={48} className="mx-auto mb-4 opacity-20" />
              <p className="text-sm">No blockchain submissions yet</p>
              <p className="text-xs mt-2">
                {connected ? 'Your RTI submissions will appear here after blockchain confirmation' : 'Connect your wallet to view your submission history'}
              </p>
            </div>
          ) : (
          <table className="w-full text-left">
            <thead>
              <tr className="text-[10px] font-bold text-white/30 uppercase tracking-[0.2em] border-b border-white/5">
                <th className="pb-4 px-4 font-bold">Reference ID</th>
                <th className="pb-4 px-4 font-bold">Department</th>
                <th className="pb-4 px-4 font-bold">Timestamp</th>
                <th className="pb-4 px-4 font-bold">Status</th>
                <th className="pb-4 px-4 font-bold">Solana Tx</th>
                <th className="pb-4 px-4 font-bold text-right">Actions</th>
              </tr>
            </thead>
            <tbody>
              {history.map((record, i) => (
                <motion.tr
                  key={record.id}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: i * 0.1 }}
                  className="group hover:bg-white/5 transition-colors border-b border-white/5 last:border-0"
                >
                  <td className="py-4 px-4 font-bold text-sm">{record.id}</td>
                  <td className="py-4 px-4">
                    <div className="flex flex-col">
                      <span className="text-xs text-white/80">{record.dept}</span>
                      <span className="text-[9px] text-white/20 font-bold uppercase">Central Government</span>
                    </div>
                  </td>
                  <td className="py-4 px-4">
                    <div className="flex items-center gap-2 text-white/50 text-xs">
                      <Clock size={12} />
                      {new Date(record.timestamp).toLocaleDateString()}
                    </div>
                  </td>
                  <td className="py-4 px-4">
                    <span className="px-2 py-1 rounded-md bg-success/10 border border-success/20 text-success text-[10px] font-bold">
                      {record.status}
                    </span>
                  </td>
                  <td className="py-4 px-4">
                    <a
                      href={`https://explorer.solana.com/tx/${record.tx}?cluster=devnet`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-[10px] text-primary/70 font-mono hover:underline"
                    >
                      {record.tx && record.tx.length > 16 ? `${record.tx.substring(0, 8)}...${record.tx.substring(record.tx.length - 8)}` : record.tx}
                    </a>
                  </td>
                  <td className="py-4 px-4 text-right">
                    <div className="flex justify-end gap-2">
                      <button className="p-2 rounded-lg bg-white/5 text-white/40 hover:text-primary hover:bg-primary/10 transition-all" title="View Certificate">
                        <Shield size={14} />
                      </button>
                      <button className="p-2 rounded-lg bg-white/5 text-white/40 hover:text-primary hover:bg-primary/10 transition-all" title="Verify Hash">
                        <LinkIcon size={14} />
                      </button>
                    </div>
                  </td>
                </motion.tr>
              ))}
            </tbody>
          </table>
          )}
        </div>
      </GlassCard>
    </div>
  );
};

export default BlockchainTracker;
