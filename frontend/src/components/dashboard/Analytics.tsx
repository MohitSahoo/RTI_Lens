import React from 'react';
import { 
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, 
  PieChart, Pie, Cell, LineChart, Line, AreaChart, Area 
} from 'recharts';
import { GlassCard } from '../ui/GlassCard';
import { TrendingUp, TrendingDown, Info, Zap } from 'lucide-react';

const COLORS = ['#00D4FF', '#7C3AED', '#00FF9D', '#FFC857', '#FF5C8A'];

const Analytics: React.FC = () => {
  const ministryData = [
    { name: 'Defence', denials: 85, appeals: 45 },
    { name: 'Finance', denials: 62, appeals: 38 },
    { name: 'Home', denials: 78, appeals: 52 },
    { name: 'Railways', denials: 45, appeals: 20 },
    { name: 'Health', denials: 30, appeals: 15 },
  ];

  const clauseData = [
    { name: 'Sec 8(1)(j)', value: 45 },
    { name: 'Sec 8(1)(a)', value: 25 },
    { name: 'Sec 8(1)(h)', value: 15 },
    { name: 'Sec 11', value: 10 },
    { name: 'Others', value: 5 },
  ];

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold font-display">Denial Pattern Analytics</h1>
        <p className="text-white/50 text-sm">Deep dive into systemic transparency failures and ministry-wise trends.</p>
      </div>

      <div className="grid lg:grid-cols-3 gap-6">
        <GlassCard className="lg:col-span-2">
          <h3 className="text-sm font-bold uppercase tracking-widest text-white/40 mb-6">Ministry Denial vs Appeal Success</h3>
          <div className="h-[350px] min-w-0 overflow-hidden">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={ministryData}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" vertical={false} />
                <XAxis dataKey="name" stroke="rgba(255,255,255,0.3)" fontSize={12} tickLine={false} axisLine={false} />
                <YAxis stroke="rgba(255,255,255,0.3)" fontSize={12} tickLine={false} axisLine={false} />
                <Tooltip 
                  contentStyle={{ backgroundColor: '#0B1020', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '8px' }}
                />
                <Bar dataKey="denials" name="Denials" fill="#FF5C8A" radius={[4, 4, 0, 0]} barSize={40} />
                <Bar dataKey="appeals" name="Approved Appeals" fill="#00D4FF" radius={[4, 4, 0, 0]} barSize={40} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </GlassCard>

        <GlassCard>
          <h3 className="text-sm font-bold uppercase tracking-widest text-white/40 mb-6">Misused Clauses Distribution</h3>
          <div className="h-[300px] min-w-0 overflow-hidden">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={clauseData}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={100}
                  paddingAngle={5}
                  dataKey="value"
                >
                  {clauseData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </div>
          <div className="space-y-2 mt-4">
            {clauseData.map((item, i) => (
              <div key={i} className="flex justify-between items-center text-xs">
                <div className="flex items-center gap-2">
                  <div className="w-2 h-2 rounded-full" style={{ backgroundColor: COLORS[i] }} />
                  <span className="text-white/60">{item.name}</span>
                </div>
                <span className="font-bold">{item.value}%</span>
              </div>
            ))}
          </div>
        </GlassCard>
      </div>

      <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
        {[
          { label: 'Avg Denial Duration', val: '28.4 Days', trend: '+4%', icon: TrendingUp, color: 'text-danger' },
          { label: 'CIC Overturn Rate', val: '42.1%', trend: '+12%', icon: Zap, color: 'text-success' },
          { label: 'Data Latency', val: '1.2ms', trend: '-2%', icon: TrendingDown, color: 'text-primary' },
        ].map((item, i) => (
          <GlassCard key={i} className="flex items-center gap-4">
            <div className={`p-4 rounded-xl bg-white/5 ${item.color}`}>
              <item.icon size={24} />
            </div>
            <div>
              <p className="text-[10px] font-bold text-white/30 uppercase tracking-widest">{item.label}</p>
              <div className="flex items-center gap-3">
                <h4 className="text-2xl font-bold">{item.val}</h4>
                <span className={`text-xs font-bold ${item.trend.startsWith('+') ? 'text-danger' : 'text-success'}`}>
                  {item.trend}
                </span>
              </div>
            </div>
          </GlassCard>
        ))}
      </div>
    </div>
  );
};

export default Analytics;
