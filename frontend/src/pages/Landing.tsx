import React from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Shield, Brain, Scale, FileText, Database, Lock, ArrowRight, Activity, Users, CheckCircle } from 'lucide-react';
import { GlowButton } from '../components/ui/GlowButton';
import { GlassCard } from '../components/ui/GlassCard';

const Landing: React.FC = () => {
  const navigate = useNavigate();
  return (
    <div className="min-h-screen relative overflow-hidden">
      <div className="grid-background" />
      
      {/* Navbar */}
      <nav className="fixed top-0 w-full z-50 px-6 py-4 flex justify-between items-center glass-card rounded-none border-t-0 border-x-0 bg-background/60 backdrop-blur-xl">
        <div className="flex items-center gap-2">
          <div className="w-10 h-10 bg-primary rounded-lg flex items-center justify-center neo-glow">
            <Scale className="text-background w-6 h-6" />
          </div>
          <span className="text-2xl font-bold font-display tracking-tight">RTI-<span className="text-primary">Lens</span></span>
        </div>
        <div className="hidden md:flex items-center gap-8 text-sm font-medium text-white/70">
          <a href="#features" className="hover:text-primary transition-colors">Features</a>
          <a href="#analytics" className="hover:text-primary transition-colors">Analytics</a>
          <a href="#about" className="hover:text-primary transition-colors">Intelligence</a>
          <GlowButton onClick={() => navigate('/dashboard')}>Get Started</GlowButton>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="relative pt-32 pb-20 px-6 max-w-7xl mx-auto">
        <div className="grid lg:grid-cols-2 gap-12 items-center">
          <motion.div
            initial={{ opacity: 0, x: -50 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.8 }}
          >
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-primary/10 border border-primary/20 text-primary text-xs font-bold uppercase tracking-wider mb-6">
              <Activity className="w-3 h-3" />
              Next-Gen Legal Intelligence
            </div>
            <h1 className="text-5xl lg:text-7xl font-bold leading-tight mb-6 font-display">
              Decode RTI Decisions with <span className="text-gradient">AI Intelligence</span>
            </h1>
            <p className="text-xl text-white/60 mb-10 max-w-xl leading-relaxed">
              Analyze CIC rulings, predict appeal outcomes, draft appeals, and uncover denial patterns using AI-powered legal analytics for Indian transparency laws.
            </p>
            <div className="flex flex-wrap gap-4">
              <GlowButton onClick={() => navigate('/dashboard')} className="px-8 py-4 text-lg">
                Start Analysis <ArrowRight className="ml-2 w-5 h-5" />
              </GlowButton>
              <GlowButton onClick={() => navigate('/dashboard')} variant="outline" className="px-8 py-4 text-lg">
                Explore Dashboard
              </GlowButton>
            </div>

            <div className="mt-12 grid grid-cols-3 gap-8 border-t border-white/10 pt-8">
              <div>
                <div className="text-3xl font-bold font-display text-primary">700+</div>
                <div className="text-sm text-white/50">Orders Analyzed</div>
              </div>
              <div>
                <div className="text-3xl font-bold font-display text-secondary">89%</div>
                <div className="text-sm text-white/50">Prediction Accuracy</div>
              </div>
              <div>
                <div className="text-3xl font-bold font-display text-success">1200+</div>
                <div className="text-sm text-white/50">Appeals Drafted</div>
              </div>
            </div>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 1, delay: 0.2 }}
            className="relative"
          >
            {/* Main Visual */}
            <div className="relative z-10 w-full aspect-square rounded-2xl overflow-hidden glass-card border-primary/20 p-2">
              <div className="absolute inset-0 bg-hero-glow animate-pulse-glow" />
              <div className="relative h-full bg-background/40 rounded-xl flex items-center justify-center border border-white/5">
                <Brain className="w-32 h-32 text-primary animate-float" />
                
                {/* Floating Cards */}
                <motion.div 
                  animate={{ y: [0, -10, 0] }}
                  transition={{ duration: 4, repeat: Infinity, ease: "easeInOut" }}
                  className="absolute top-10 right-10 w-48 h-24 glass-card p-4 border-success/30"
                >
                  <div className="flex items-center gap-2 mb-2">
                    <CheckCircle className="text-success w-4 h-4" />
                    <span className="text-xs font-bold text-success">SUCCESS PREDICTION</span>
                  </div>
                  <div className="text-xl font-bold">92.4%</div>
                  <div className="w-full bg-white/10 h-1 mt-2 rounded-full overflow-hidden">
                    <div className="bg-success h-full w-[92%]" />
                  </div>
                </motion.div>

                <motion.div 
                  animate={{ y: [0, 10, 0] }}
                  transition={{ duration: 5, repeat: Infinity, ease: "easeInOut", delay: 1 }}
                  className="absolute bottom-10 left-10 w-56 h-28 glass-card p-4 border-primary/30"
                >
                  <div className="flex items-center gap-2 mb-2">
                    <FileText className="text-primary w-4 h-4" />
                    <span className="text-xs font-bold text-primary">DRAFT GENERATED</span>
                  </div>
                  <div className="text-xs text-white/50 space-y-1">
                    <div className="h-2 bg-white/10 rounded w-full" />
                    <div className="h-2 bg-white/10 rounded w-5/6" />
                    <div className="h-2 bg-white/10 rounded w-4/6" />
                  </div>
                </motion.div>
              </div>
            </div>
            
            {/* Background elements */}
            <div className="absolute -top-20 -right-20 w-64 h-64 bg-primary/20 rounded-full blur-[100px]" />
            <div className="absolute -bottom-20 -left-20 w-64 h-64 bg-secondary/20 rounded-full blur-[100px]" />
          </motion.div>
        </div>
      </section>

      {/* Features Grid */}
      <section className="py-20 px-6 max-w-7xl mx-auto" id="features">
        <div className="text-center mb-16">
          <h2 className="text-4xl font-bold font-display mb-4">Enterprise-Grade Intelligence</h2>
          <p className="text-white/50 max-w-2xl mx-auto">
            Advanced AI models trained on thousands of CIC orders to provide unprecedented visibility into the RTI process.
          </p>
        </div>
        
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
          {[
            { icon: Brain, title: "Outcome Prediction", desc: "AI-driven success probability for second appeals based on historical ruling patterns.", color: "text-primary" },
            { icon: FileText, title: "Appeal Drafting", desc: "Automatically generate legally-sound appeals with automated citation of relevant precedents.", color: "text-secondary" },
            { icon: Database, title: "Pattern Detection", desc: "Identify systemic denial patterns across ministries and specific public information officers.", color: "text-success" },
            { icon: Shield, title: "Legal Citation", desc: "Context-aware RAG system that finds the exact Section 8 exemptions and relevant case law.", color: "text-warning" },
            { icon: Activity, title: "Knowledge Graph", desc: "Visualize connections between ministries, exemptions, and legal precedents.", color: "text-primary" },
            { icon: Database, title: "Semantic Search", desc: "Deep-search through thousands of PDF rulings to find matching legal scenarios.", color: "text-success" }
          ].map((feature, i) => (
            <GlassCard key={i} className="flex flex-col gap-4">
              <div className={`w-12 h-12 rounded-lg bg-white/5 flex items-center justify-center ${feature.color}`}>
                <feature.icon className="w-6 h-6" />
              </div>
              <h3 className="text-xl font-bold">{feature.title}</h3>
              <p className="text-white/50 text-sm leading-relaxed">{feature.desc}</p>
            </GlassCard>
          ))}
        </div>
      </section>
    </div>
  );
};

export default Landing;
