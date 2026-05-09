import React, { useState } from 'react';
import { Outlet, Link, useLocation } from 'react-router-dom';
import { 
  LayoutDashboard, 
  MessageSquare, 
  FileEdit, 
  LineChart, 
  BarChart3, 
  Network, 
  Link as LinkIcon, 
  Building2, 
  Settings,
  Scale,
  Menu,
  X,
  Bell,
  Search,
  User,
  Clock,
  Shield
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

const SidebarItem = ({ icon: Icon, label, path, active, collapsed }: any) => (
  <Link to={path}>
    <motion.div
      whileHover={{ x: 4 }}
      className={cn(
        'flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-300 mb-1 group',
        active 
          ? 'bg-primary/10 text-primary border border-primary/20 neo-glow' 
          : 'text-white/50 hover:text-white hover:bg-white/5'
      )}
    >
      <Icon className={cn('w-5 h-5 transition-transform duration-300', active && 'scale-110')} />
      {!collapsed && (
        <span className="font-medium text-sm tracking-wide">{label}</span>
      )}
      {active && !collapsed && (
        <motion.div 
          layoutId="active-indicator"
          className="ml-auto w-1.5 h-1.5 rounded-full bg-primary shadow-[0_0_8px_rgba(0,212,255,0.8)]" 
        />
      )}
    </motion.div>
  </Link>
);

const DashboardLayout: React.FC = () => {
  const [collapsed, setCollapsed] = useState(false);
  const [showNotifications, setShowNotifications] = useState(false);
  const location = useLocation();

  const notifications = [
    { id: 1, title: 'New CIC Ruling', desc: 'Case CIC/MHOME/A/2024/0004 approved.', time: '2m ago', type: 'success' },
    { id: 2, title: 'Compliance Alert', desc: 'Ministry of Finance misuse rate up by 34%.', time: '1h ago', type: 'warning' },
    { id: 3, title: 'System Update', desc: 'New ML models deployed for prediction.', time: '5h ago', type: 'info' },
  ];

  const menuItems = [
    { icon: LayoutDashboard, label: 'Overview', path: '/dashboard' },
    { icon: MessageSquare, label: 'AI Q&A Assistant', path: '/dashboard/qa' },
    { icon: FileEdit, label: 'Appeal Draft Generator', path: '/dashboard/draft' },
    { icon: LineChart, label: 'Outcome Predictor', path: '/dashboard/predictor' },
    { icon: Shield, label: 'Blockchain Integrity', path: '/dashboard/blockchain' },
    { icon: Building2, label: 'Government Portal', path: '/dashboard/gov' },
    { icon: BarChart3, label: 'Denial Analytics', path: '/dashboard/analytics' },
    { icon: Network, label: 'Knowledge Graph', path: '/dashboard/graph' },
  ];

  return (
    <div className="flex min-h-screen bg-background text-white font-sans selection:bg-primary/30">
      <div className="grid-background opacity-50" />
      
      {/* Sidebar */}
      <motion.aside
        animate={{ width: collapsed ? 80 : 280 }}
        className="fixed left-0 top-0 h-full bg-background/40 backdrop-blur-2xl border-r border-white/5 z-40 transition-all duration-300 overflow-hidden"
      >
        <div className="p-6 flex items-center justify-between">
          {!collapsed && (
            <Link to="/" className="flex items-center gap-2 group">
              <div className="w-8 h-8 bg-primary rounded-lg flex items-center justify-center neo-glow group-hover:scale-110 transition-transform">
                <Scale className="text-background w-5 h-5" />
              </div>
              <span className="text-xl font-bold font-display">RTI-<span className="text-primary">Lens</span></span>
            </Link>
          )}
          {collapsed && (
            <Link to="/" className="w-8 h-8 bg-primary rounded-lg flex items-center justify-center neo-glow mx-auto hover:scale-110 transition-transform">
              <Scale className="text-background w-5 h-5" />
            </Link>
          )}
        </div>

        <nav className="mt-8 px-4">
          <div className="text-[10px] font-bold text-white/30 uppercase tracking-[0.2em] px-4 mb-4">
            {!collapsed ? 'Primary Modules' : '•••'}
          </div>
          {menuItems.map((item) => (
            <SidebarItem
              key={item.path}
              {...item}
              active={location.pathname === item.path || (item.path === '/dashboard' && location.pathname === '/dashboard/')}
              collapsed={collapsed}
            />
          ))}
        </nav>

        <div className="absolute bottom-8 left-0 w-full px-4 text-center">
          <button 
            onClick={() => setCollapsed(!collapsed)}
            className="w-full flex items-center justify-center p-3 text-white/30 hover:text-white transition-colors"
          >
            {collapsed ? <Menu size={20} /> : <X size={20} />}
          </button>
        </div>
      </motion.aside>

      {/* Main Content */}
      <main 
        className="flex-1 transition-all duration-300"
        style={{ marginLeft: collapsed ? 80 : 280 }}
      >
        {/* Top Header */}
        <header className="h-20 border-b border-white/5 bg-background/20 backdrop-blur-md flex items-center justify-between px-8 sticky top-0 z-30">
          <div className="flex items-center gap-4 bg-white/5 px-4 py-2 rounded-xl border border-white/5 w-96">
            <Search className="w-4 h-4 text-white/30" />
            <input 
              type="text" 
              placeholder="Search rulings, precedents, or draft IDs..." 
              className="bg-transparent border-none outline-none text-sm w-full text-white placeholder:text-white/20"
            />
            <div className="px-1.5 py-0.5 rounded bg-white/10 text-[10px] text-white/40">⌘K</div>
          </div>

          <div className="flex items-center gap-6 relative">
            <button 
              onClick={() => setShowNotifications(!showNotifications)}
              className={cn(
                "relative p-2 transition-colors rounded-lg",
                showNotifications ? "bg-primary/10 text-primary" : "text-white/50 hover:text-white"
              )}
            >
              <Bell className="w-5 h-5" />
              <span className="absolute top-2 right-2 w-2 h-2 bg-primary rounded-full neo-glow" />
            </button>

            <AnimatePresence>
              {showNotifications && (
                <>
                  <motion.div 
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                    className="fixed inset-0 z-40"
                    onClick={() => setShowNotifications(false)}
                  />
                  <motion.div
                    initial={{ opacity: 0, y: 10, scale: 0.95 }}
                    animate={{ opacity: 1, y: 0, scale: 1 }}
                    exit={{ opacity: 0, y: 10, scale: 0.95 }}
                    className="absolute top-full right-0 mt-4 w-80 bg-background/80 backdrop-blur-2xl border border-white/10 rounded-2xl shadow-2xl z-50 overflow-hidden"
                  >
                    <div className="p-4 border-b border-white/5 flex justify-between items-center bg-white/5">
                      <span className="text-xs font-bold uppercase tracking-widest text-white/40">Notifications</span>
                      <span className="text-[10px] font-bold text-primary cursor-pointer hover:underline">Mark all read</span>
                    </div>
                    <div className="max-h-[400px] overflow-y-auto">
                      {notifications.map((n) => (
                        <div key={n.id} className="p-4 border-b border-white/5 hover:bg-white/5 transition-colors cursor-pointer group">
                          <div className="flex justify-between items-start mb-1">
                            <span className={cn(
                              "text-[10px] font-bold uppercase tracking-tighter",
                              n.type === 'success' ? 'text-success' : n.type === 'warning' ? 'text-warning' : 'text-primary'
                            )}>{n.title}</span>
                            <span className="text-[9px] text-white/20">{n.time}</span>
                          </div>
                          <p className="text-xs text-white/60 group-hover:text-white transition-colors">{n.desc}</p>
                        </div>
                      ))}
                    </div>
                    <div className="p-3 bg-white/5 text-center border-t border-white/5">
                      <Link to="/dashboard/analytics" className="text-[10px] font-bold text-white/30 hover:text-primary transition-colors uppercase tracking-widest">
                        View All Activity
                      </Link>
                    </div>
                  </motion.div>
                </>
              )}
            </AnimatePresence>
          </div>
        </header>

        {/* Page Content */}
        <div className="p-8">
          <Outlet />
        </div>
      </main>
    </div>
  );
};

export default DashboardLayout;
