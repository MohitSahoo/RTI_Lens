import React from 'react';
import { motion } from 'framer-motion';
import { Link } from 'react-router-dom';
import { 
  TrendingUp, 
  AlertCircle, 
  CheckCircle2, 
  Clock, 
  ExternalLink,
  ChevronRight,
  Zap,
  Info,
  FileEdit
} from 'lucide-react';
import { GlassCard } from '../ui/GlassCard';
import { 
  AreaChart, 
  Area, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer,
  BarChart,
  Bar,
  Cell
} from 'recharts';

const data = [
  { name: 'Jan', orders: 40, denials: 24 },
  { name: 'Feb', orders: 30, denials: 13 },
  { name: 'Mar', orders: 20, denials: 98 },
  { name: 'Apr', orders: 27, denials: 39 },
  { name: 'May', orders: 18, denials: 48 },
  { name: 'Jun', orders: 23, denials: 38 },
  { name: 'Jul', orders: 34, denials: 43 },
];

const barData = [
  { name: 'Ministry of Home', value: 85, color: '#FF5C8A' },
  { name: 'Min. of Finance', value: 72, color: '#7C3AED' },
  { name: 'Min. of Railways', value: 64, color: '#00D4FF' },
  { name: 'Min. of Defense', value: 58, color: '#00FF9D' },
  { name: 'Min. of Health', value: 45, color: '#FFC857' },
];

const StatCard = ({ title, value, trend, icon: Icon, color }: any) => (
  <GlassCard className="relative overflow-hidden">
    <div className="flex justify-between items-start">
      <div>
        <p className="text-white/40 text-xs font-bold uppercase tracking-wider mb-1">{title}</p>
        <h3 className="text-3xl font-bold font-display">{value}</h3>
        <div className={cn("flex items-center gap-1 text-xs mt-2 font-bold", trend.startsWith('+') ? 'text-success' : 'text-danger')}>
          {trend.startsWith('+') ? <TrendingUp size={12} /> : <AlertCircle size={12} />}
          {trend}
          <span className="text-white/30 font-normal ml-1">from last month</span>
        </div>
      </div>
      <div className={cn("p-3 rounded-xl bg-white/5", color)}>
        <Icon size={24} />
      </div>
    </div>
  </GlassCard>
);

function cn(...inputs: any[]) {
  return inputs.filter(Boolean).join(' ');
}

const Overview: React.FC = () => {
  const [exporting, setExporting] = React.useState(false);
  const [timeRange, setTimeRange] = React.useState('Last 30 Days');

  const handleExport = () => {
    setExporting(true);
    setTimeout(() => {
      setExporting(false);
      alert('RTI-Lens Intelligence Report exported successfully as PDF.');
    }, 2000);
  };

  return (
    <div className="space-y-8">
      <div className="flex justify-between items-end">
        <div>
          <h1 className="text-3xl font-bold font-display">Intelligence Overview</h1>
          <p className="text-white/50 text-sm">Real-time RTI analytics and CIC ruling intelligence.</p>
        </div>
        <div className="flex gap-3">
          <select 
            value={timeRange}
            onChange={(e) => setTimeRange(e.target.value)}
            className="px-4 py-2 rounded-lg bg-white/5 border border-white/10 text-xs font-bold uppercase tracking-widest hover:bg-white/10 transition-all outline-none"
          >
            <option className="bg-[#0B1020]">Last 7 Days</option>
            <option className="bg-[#0B1020]">Last 30 Days</option>
            <option className="bg-[#0B1020]">Last 90 Days</option>
          </select>
          <button 
            onClick={handleExport}
            disabled={exporting}
            className="px-6 py-2 rounded-lg bg-primary text-background text-xs font-bold uppercase tracking-widest neo-glow hover:scale-105 active:scale-95 transition-all flex items-center gap-2 min-w-[140px] justify-center"
          >
            {exporting ? (
              <>
                <div className="w-3 h-3 border-2 border-background border-t-transparent rounded-full animate-spin" />
                Processing...
              </>
            ) : (
              'Export Report'
            )}
          </button>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard title="Total Rulings" value="742" trend="+12.5%" icon={Zap} color="text-primary" />
        <StatCard title="Prediction Hit" value="89.2%" trend="+2.1%" icon={CheckCircle2} color="text-success" />
        <StatCard title="Denial Rate" value="34.1%" trend="-4.5%" icon={AlertCircle} color="text-danger" />
        <StatCard title="Avg. Response" value="22d" trend="-2 days" icon={Clock} color="text-warning" />
      </div>

      <div className="grid lg:grid-cols-3 gap-6">
        {/* Main Chart */}
        <GlassCard className="lg:col-span-2">
          <div className="flex justify-between items-center mb-8">
            <div>
              <h3 className="text-xl font-bold">RTI Submission vs Denial Trends</h3>
              <p className="text-white/40 text-xs">Monthly volume across all monitored ministries</p>
            </div>
            <div className="flex gap-4 text-[10px] font-bold uppercase tracking-widest">
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 rounded-full bg-primary" />
                <span className="text-white/60">Orders</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 rounded-full bg-secondary" />
                <span className="text-white/60">Denials</span>
              </div>
            </div>
          </div>
          <div className="h-[300px] w-full min-w-0 overflow-hidden">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={data}>
                <defs>
                  <linearGradient id="colorOrders" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#00D4FF" stopOpacity={0.3}/>
                    <stop offset="95%" stopColor="#00D4FF" stopOpacity={0}/>
                  </linearGradient>
                  <linearGradient id="colorDenials" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#7C3AED" stopOpacity={0.3}/>
                    <stop offset="95%" stopColor="#7C3AED" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" vertical={false} />
                <XAxis 
                  dataKey="name" 
                  axisLine={false} 
                  tickLine={false} 
                  tick={{fill: 'rgba(255,255,255,0.3)', fontSize: 12}}
                />
                <YAxis 
                  axisLine={false} 
                  tickLine={false} 
                  tick={{fill: 'rgba(255,255,255,0.3)', fontSize: 12}}
                />
                <Tooltip 
                  contentStyle={{ backgroundColor: '#0B1020', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '8px' }}
                  itemStyle={{ fontSize: '12px' }}
                />
                <Area type="monotone" dataKey="orders" stroke="#00D4FF" strokeWidth={3} fillOpacity={1} fill="url(#colorOrders)" />
                <Area type="monotone" dataKey="denials" stroke="#7C3AED" strokeWidth={3} fillOpacity={1} fill="url(#colorDenials)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </GlassCard>

        {/* Sidebar Analytics */}
        <GlassCard>
          <h3 className="text-xl font-bold mb-6">Ministry Denial Risk</h3>
          <div className="space-y-6">
            {barData.map((item, i) => (
              <div key={i} className="space-y-2">
                <div className="flex justify-between text-xs font-bold">
                  <span className="text-white/60">{item.name}</span>
                  <span>{item.value}%</span>
                </div>
                <div className="w-full bg-white/5 h-2 rounded-full overflow-hidden">
                  <motion.div 
                    initial={{ width: 0 }}
                    animate={{ width: `${item.value}%` }}
                    transition={{ duration: 1, delay: i * 0.1 }}
                    className="h-full rounded-full" 
                    style={{ backgroundColor: item.color, boxShadow: `0 0 10px ${item.color}66` }}
                  />
                </div>
              </div>
            ))}
          </div>
          <button className="w-full mt-8 py-3 rounded-xl bg-white/5 border border-white/10 text-xs font-bold uppercase tracking-widest hover:bg-white/10 transition-all flex items-center justify-center gap-2">
            View All Ministries <ChevronRight size={14} />
          </button>
        </GlassCard>
      </div>

      {/* Recent Rulings & AI Insights */}
      <div className="grid lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-4">
          <div className="flex justify-between items-center px-2">
            <h3 className="text-xl font-bold">Latest CIC Rulings</h3>
            <button className="text-primary text-xs font-bold uppercase tracking-widest flex items-center gap-1 hover:underline">
              View Feed <ExternalLink size={12} />
            </button>
          </div>
          {[1, 2, 3].map((item) => (
            <Link key={item} to="/dashboard/graph" className="block">
              <GlassCard className="flex gap-6 items-center group cursor-pointer hover:border-primary/30 transition-all">
                <div className="w-12 h-12 rounded-xl bg-white/5 flex items-center justify-center group-hover:bg-primary/20 transition-colors">
                  <FileEdit className="text-white/40 group-hover:text-primary transition-colors" />
                </div>
                <div className="flex-1">
                  <div className="flex justify-between items-start mb-1">
                    <h4 className="font-bold text-sm">CIC/MHOME/A/2024/000{item}</h4>
                    <span className="text-[10px] font-bold text-success px-2 py-0.5 rounded bg-success/10 border border-success/20">ALLOWED</span>
                  </div>
                  <p className="text-xs text-white/40 line-clamp-1">Ruling regarding the disclosure of annual confidential reports of senior police officials.</p>
                  <div className="flex items-center gap-4 mt-2 text-[10px] text-white/20 uppercase tracking-widest font-bold">
                    <span>Ministry of Home Affairs</span>
                    <span>•</span>
                    <span>May 0{item}, 2026</span>
                  </div>
                </div>
                <ChevronRight className="text-white/20 group-hover:text-primary transition-transform group-hover:translate-x-1" />
              </GlassCard>
            </Link>
          ))}
        </div>

        <div className="space-y-4">
          <h3 className="text-xl font-bold px-2">AI Insights</h3>
          <div className="space-y-4">
            <div className="p-5 rounded-2xl bg-primary/5 border border-primary/20 relative overflow-hidden group">
              <div className="absolute -top-4 -right-4 w-20 h-20 bg-primary/10 rounded-full blur-2xl" />
              <div className="flex items-center gap-2 mb-3">
                <Zap className="text-primary w-4 h-4" />
                <span className="text-xs font-bold text-primary uppercase tracking-widest">Section 8(1)(j) Warning</span>
              </div>
              <p className="text-xs text-white/70 leading-relaxed">
                We've detected a 34% increase in the misuse of personal privacy exemptions by the Finance Ministry this quarter.
              </p>
              <Link 
                to="/dashboard/analytics"
                className="mt-4 flex items-center gap-2 text-[10px] font-bold text-primary group-hover:translate-x-1 transition-transform cursor-pointer"
              >
                VIEW FULL ANALYSIS <ChevronRight size={10} />
              </Link>
            </div>

            <div className="p-5 rounded-2xl bg-secondary/5 border border-secondary/20 relative overflow-hidden group">
              <div className="absolute -top-4 -right-4 w-20 h-20 bg-secondary/10 rounded-full blur-2xl" />
              <div className="flex items-center gap-2 mb-3">
                <Info className="text-secondary w-4 h-4" />
                <span className="text-xs font-bold text-secondary uppercase tracking-widest">Precedent Alert</span>
              </div>
              <p className="text-xs text-white/70 leading-relaxed">
                New Supreme Court ruling clarifies Section 2(f) definitions. This affects 14 of your active pending appeals.
              </p>
              <Link 
                to="/dashboard/qa"
                className="mt-4 flex items-center gap-2 text-[10px] font-bold text-secondary group-hover:translate-x-1 transition-transform cursor-pointer"
              >
                UPDATE APPEALS <ChevronRight size={10} />
              </Link>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

const ArrowRight = ({ size, className }: any) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className}>
    <path d="M5 12h14m-7-7 7 7-7 7" />
  </svg>
);

export default Overview;
