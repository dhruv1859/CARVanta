import { Routes, Route } from 'react-router-dom';
import Layout from './components/Layout';
import SingleAnalysis from './pages/SingleAnalysis';
import Comparison from './pages/Comparison';
import TissueHeatmap from './pages/TissueHeatmap';
import MultiTarget from './pages/MultiTarget';
import Stratification from './pages/Stratification';
import NLPSearch from './pages/NLPSearch';
import ClinicalTrials from './pages/ClinicalTrials';
import Leaderboard from './pages/Leaderboard';
import DatasetIntel from './pages/DatasetIntel';
import SystemStatus from './pages/SystemStatus';

export default function App() {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<SingleAnalysis />} />
        <Route path="/compare" element={<Comparison />} />
        <Route path="/heatmap" element={<TissueHeatmap />} />
        <Route path="/synergy" element={<MultiTarget />} />
        <Route path="/stratify" element={<Stratification />} />
        <Route path="/search" element={<NLPSearch />} />
        <Route path="/trials" element={<ClinicalTrials />} />
        <Route path="/leaderboard" element={<Leaderboard />} />
        <Route path="/dataset" element={<DatasetIntel />} />
        <Route path="/status" element={<SystemStatus />} />
      </Routes>
    </Layout>
  );
}
