import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { DashboardLayout } from "@/layouts/DashboardLayout";
import DashboardPage from "@/pages/DashboardPage";
import LiveViewPage from "@/pages/LiveViewPage";
import CameraManagementPage from "@/pages/CameraManagementPage";
import AlertManagementPage from "@/pages/AlertManagementPage";
import HistoryPage from "@/pages/HistoryPage";

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<DashboardLayout />}>
          <Route path="/" element={<DashboardPage />} />
          <Route path="/live" element={<LiveViewPage />} />
          <Route path="/cameras" element={<CameraManagementPage />} />
          <Route path="/alerts" element={<AlertManagementPage />} />
          <Route path="/history" element={<HistoryPage />} />
        </Route>
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}
