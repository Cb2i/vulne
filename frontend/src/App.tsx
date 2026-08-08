import { BrowserRouter, Route, Routes } from "react-router-dom";
import { ProtectedRoute } from "./components/ProtectedRoute";
import { AuthProvider } from "./hooks/useAuth";
import { AppLayout } from "./layouts/AppLayout";
import { AssetsPage } from "./pages/AssetsPage";
import { DashboardPage } from "./pages/DashboardPage";
import { DecommissionPage } from "./pages/DecommissionPage";
import { ExceptionsPage } from "./pages/ExceptionsPage";
import { ExportsPage } from "./pages/ExportsPage";
import { FindingDetailPage } from "./pages/FindingDetailPage";
import { FindingsPage } from "./pages/FindingsPage";
import { ImportPage } from "./pages/ImportPage";
import { LoginPage } from "./pages/LoginPage";
import { RemediationPage } from "./pages/RemediationPage";
import { RulesPage } from "./pages/RulesPage";
import { ScanComparePage } from "./pages/ScanComparePage";
import { TeamsPage } from "./pages/TeamsPage";
import { UsersPage } from "./pages/UsersPage";

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route
            element={
              <ProtectedRoute>
                <AppLayout />
              </ProtectedRoute>
            }
          >
            <Route path="/" element={<DashboardPage />} />
            <Route path="/findings" element={<FindingsPage />} />
            <Route path="/findings/:id" element={<FindingDetailPage />} />
            <Route path="/assets" element={<AssetsPage />} />
            <Route path="/remediation" element={<RemediationPage />} />
            <Route path="/scans/compare" element={<ScanComparePage />} />
            <Route
              path="/import"
              element={
                <ProtectedRoute roles={["admin", "analyst"]}>
                  <ImportPage />
                </ProtectedRoute>
              }
            />
            <Route path="/exceptions" element={<ExceptionsPage />} />
            <Route path="/decommission" element={<DecommissionPage />} />
            <Route path="/teams" element={<TeamsPage />} />
            <Route
              path="/rules"
              element={
                <ProtectedRoute roles={["admin"]}>
                  <RulesPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/users"
              element={
                <ProtectedRoute roles={["admin"]}>
                  <UsersPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/exports"
              element={
                <ProtectedRoute roles={["admin", "analyst"]}>
                  <ExportsPage />
                </ProtectedRoute>
              }
            />
          </Route>
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}
