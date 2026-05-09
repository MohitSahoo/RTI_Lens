import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { WalletProvider } from './contexts/WalletProvider';
import Landing from './pages/Landing';
import DashboardLayout from './components/layout/DashboardLayout';
import Overview from './components/dashboard/Overview';
import AIQA from './components/dashboard/AIQA';
import AppealGenerator from './components/dashboard/AppealGenerator';
import Predictor from './components/dashboard/Predictor';
import Analytics from './components/dashboard/Analytics';
import KnowledgeGraph from './components/dashboard/KnowledgeGraph';
import BlockchainTracker from './components/dashboard/BlockchainTracker';
import GovernmentPortal from './components/dashboard/GovernmentPortal';

function App() {
  return (
    <WalletProvider>
      <Router>
        <Routes>
          <Route path="/" element={<Landing />} />

          <Route path="/dashboard" element={<DashboardLayout />}>
            <Route index element={<Overview />} />
            <Route path="qa" element={<AIQA />} />
            <Route path="draft" element={<AppealGenerator />} />
            <Route path="predictor" element={<Predictor />} />
            <Route path="analytics" element={<Analytics />} />
            <Route path="graph" element={<KnowledgeGraph />} />
            <Route path="blockchain" element={<BlockchainTracker />} />
            <Route path="gov" element={<GovernmentPortal />} />
          </Route>
        </Routes>
      </Router>
    </WalletProvider>
  );
}

export default App;
