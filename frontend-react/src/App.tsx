import { Routes, Route } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import Layout from './components/Layout';
import LoginPage from './pages/LoginPage';
import ProfilePage from './pages/ProfilePage';
import DigitalTwin from './pages/DigitalTwin';
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
import DrugInteractions from './pages/DrugInteractions';
import PatentExplorer from './pages/PatentExplorer';
import CommunitySubmit from './pages/CommunitySubmit';
import BatchUpload from './pages/BatchUpload';
import AuditLog from './pages/AuditLog';
import AdminDashboard from './pages/AdminDashboard';
import MFASetup from './pages/MFASetup';
import BillingPage from './pages/BillingPage';
import OrgManagement from './pages/OrgManagement';
import GenomicProfiler from './pages/GenomicProfiler';
import AdverseEvents from './pages/AdverseEvents';
import OutcomesTracker from './pages/OutcomesTracker';
import PopulationSimulator from './pages/PopulationSimulator';
import PatientWizard from './pages/PatientWizard';
import MultiOmics from './pages/MultiOmics';

function ProtectedApp() {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100vh', background: '#0a0a1a' }}>
        <div style={{ textAlign: 'center', color: '#a5b4fc' }}>
          <div style={{ fontSize: 48, marginBottom: 16 }}>🧬</div>
          <div style={{ fontSize: 14, letterSpacing: 2, textTransform: 'uppercase' }}>Loading CARVanta...</div>
        </div>
      </div>
    );
  }

  if (!user) {
    return <LoginPage />;
  }

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
        <Route path="/drugs" element={<DrugInteractions />} />
        <Route path="/patents" element={<PatentExplorer />} />
        <Route path="/community" element={<CommunitySubmit />} />
        <Route path="/batch" element={<BatchUpload />} />
        <Route path="/audit" element={<AuditLog />} />
        <Route path="/status" element={<SystemStatus />} />
        <Route path="/profile" element={<ProfilePage />} />
        <Route path="/twin" element={<DigitalTwin />} />
        <Route path="/admin" element={<AdminDashboard />} />
        <Route path="/mfa" element={<MFASetup />} />
        <Route path="/billing" element={<BillingPage />} />
        <Route path="/organizations" element={<OrgManagement />} />
        <Route path="/genomics" element={<GenomicProfiler />} />
        <Route path="/adverse-events" element={<AdverseEvents />} />
        <Route path="/outcomes" element={<OutcomesTracker />} />
        <Route path="/population" element={<PopulationSimulator />} />
        <Route path="/wizard" element={<PatientWizard />} />
        <Route path="/multi-omics" element={<MultiOmics />} />
      </Routes>
    </Layout>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <ProtectedApp />
    </AuthProvider>
  );
}
