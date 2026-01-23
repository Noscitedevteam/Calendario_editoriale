import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { useAuthStore } from './store/authStore';
import { AppLayout } from './components/layout';

// Pages
import Login from './pages/Login';
import Register from './pages/Register';
import Dashboard from './pages/Dashboard';
import BrandDetail from './pages/BrandDetail';
import ProjectDetail from './pages/ProjectDetail';
import ProjectWizard from './pages/ProjectWizard';
import VoiceProfilingInterview from './pages/VoiceProfilingInterview';
import Profile from './pages/Profile';
import AdminDashboard from './pages/AdminDashboard';
import SaasAdmin from './pages/SaasAdmin';
import BrandsPage from './pages/BrandsPage';
import SocialPage from './pages/SocialPage';
import DocumentsPage from './pages/DocumentsPage';
import SettingsPage from './pages/SettingsPage';

// Protected Route wrapper
function ProtectedRoute({ children }) {
  const { isAuthenticated } = useAuthStore();
  return isAuthenticated ? children : <Navigate to="/login" />;
}

function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* Public routes */}
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />

        {/* Protected routes with layout */}
        <Route
          path="/"
          element={
            <ProtectedRoute>
              <AppLayout />
            </ProtectedRoute>
          }
        >
          {/* Dashboard */}
          <Route index element={<Navigate to="/dashboard" replace />} />
          <Route path="dashboard" element={<Dashboard />} />
          
          {/* Brands */}
          <Route path="brands" element={<BrandsPage />} />
          <Route path="brand/:id" element={<BrandDetail />} />
          
          {/* Projects/Calendars */}
          <Route path="calendars" element={<Navigate to="/brands" replace />} />
          <Route path="project/:id" element={<ProjectDetail />} />
          <Route path="brand/:brandId/new-project" element={<ProjectWizard />} />
          <Route path="brand/:brandId/voice-interview" element={<VoiceProfilingInterview />} />
          
          {/* Social */}
          <Route path="social" element={<SocialPage />} />
          
          {/* Documents */}
          <Route path="documents" element={<DocumentsPage />} />
          
          {/* AI Assistant */}
          <Route path="ai-assistant" element={<VoiceProfilingInterview />} />
          
          {/* Settings & Profile */}
          <Route path="settings" element={<SettingsPage />} />
          <Route path="profile" element={<Profile />} />
          
          {/* Admin */}
          <Route path="admin" element={<AdminDashboard />} />
          <Route path="admin/saas" element={<SaasAdmin />} />
        </Route>

        {/* Catch all */}
        <Route path="*" element={<Navigate to="/dashboard" replace />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
