import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Landing from './pages/Landing';
import DashboardLayout from './components/layout/DashboardLayout';
import Overview from './components/dashboard/Overview';
import AIQA from './components/dashboard/AIQA';
import AppealGenerator from './components/dashboard/AppealGenerator';
import Predictor from './components/dashboard/Predictor';
import Analytics from './components/dashboard/Analytics';
import KnowledgeGraph from './components/dashboard/KnowledgeGraph';

function App() {
  return (
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
        </Route>
      </Routes>
    </Router>
  );
}

export default App;
