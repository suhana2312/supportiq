import React from "react";
import { Routes, Route, Navigate } from "react-router-dom";
import { useAuth } from "./context/AuthContext";
import { AppLayout } from "./layouts/AppLayout";
import { Login } from "./pages/Login";
import { Register } from "./pages/Register";
import { ChatPage } from "./pages/customer/ChatPage";
import { OrdersPage } from "./pages/customer/OrdersPage";
import { TicketsPage } from "./pages/customer/TicketsPage";
import { AdminDashboard } from "./pages/admin/AdminDashboard";
import { DocumentsPage } from "./pages/admin/DocumentsPage";
import { AdminTicketsPage } from "./pages/admin/AdminTicketsPage";
import { AdminConversationsPage } from "./pages/admin/AdminConversationsPage";
import { AdminOrdersPage } from "./pages/admin/AdminOrdersPage";
import { AdminFAQsPage } from "./pages/admin/AdminFAQsPage";
import { AdminSettingsPage } from "./pages/admin/AdminSettingsPage";
import { AdminUsersPage } from "./pages/admin/AdminUsersPage";
import { UserRole } from "./types";
import { RefreshCw } from "lucide-react";

interface ProtectedRouteProps {
  children: React.ReactElement;
  allowedRoles?: UserRole[];
}

const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ children, allowedRoles }) => {
  const { user, isLoading } = useAuth();

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50">
        <div className="flex flex-col items-center gap-3">
          <RefreshCw className="w-8 h-8 text-indigo-600 animate-spin" />
          <p className="text-sm font-medium text-slate-600">Initializing SupportIQ Workspace...</p>
        </div>
      </div>
    );
  }

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  if (allowedRoles && !allowedRoles.includes(user.role)) {
    // If unauthorized for admin page, route customer to chat
    return <Navigate to="/chat" replace />;
  }

  return children;
};

const RootRedirect: React.FC = () => {
  const { user, isLoading } = useAuth();

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50">
        <RefreshCw className="w-8 h-8 text-indigo-600 animate-spin" />
      </div>
    );
  }

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  if (user.role === "CUSTOMER") {
    return <Navigate to="/chat" replace />;
  }

  return <Navigate to="/admin" replace />;
};

export const App: React.FC = () => {
  const adminAgentRoles: UserRole[] = ["SUPER_ADMIN", "ORGANIZATION_ADMIN", "SUPPORT_AGENT"];

  return (
    <Routes>
      {/* Public Authentication routes */}
      <Route path="/login" element={<Login />} />
      <Route path="/register" element={<Register />} />

      {/* Main Workspace (Protected Layout) */}
      <Route
        path="/"
        element={
          <ProtectedRoute>
            <AppLayout />
          </ProtectedRoute>
        }
      >
        <Route index element={<RootRedirect />} />

        {/* Customer accessible routes */}
        <Route path="chat" element={<ChatPage />} />
        <Route path="orders" element={<OrdersPage />} />
        <Route path="tickets" element={<TicketsPage />} />

        {/* Admin & Support Agent routes */}
        <Route
          path="admin"
          element={
            <ProtectedRoute allowedRoles={adminAgentRoles}>
              <AdminDashboard />
            </ProtectedRoute>
          }
        />
        <Route
          path="admin/analytics"
          element={
            <ProtectedRoute allowedRoles={adminAgentRoles}>
              <AdminDashboard />
            </ProtectedRoute>
          }
        />
        <Route
          path="admin/documents"
          element={
            <ProtectedRoute allowedRoles={adminAgentRoles}>
              <DocumentsPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="admin/faqs"
          element={
            <ProtectedRoute allowedRoles={adminAgentRoles}>
              <AdminFAQsPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="admin/tickets"
          element={
            <ProtectedRoute allowedRoles={adminAgentRoles}>
              <AdminTicketsPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="admin/conversations"
          element={
            <ProtectedRoute allowedRoles={adminAgentRoles}>
              <AdminConversationsPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="admin/orders"
          element={
            <ProtectedRoute allowedRoles={adminAgentRoles}>
              <AdminOrdersPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="admin/users"
          element={
            <ProtectedRoute allowedRoles={["SUPER_ADMIN", "ORGANIZATION_ADMIN"]}>
              <AdminUsersPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="admin/settings"
          element={
            <ProtectedRoute allowedRoles={["SUPER_ADMIN", "ORGANIZATION_ADMIN"]}>
              <AdminSettingsPage />
            </ProtectedRoute>
          }
        />
      </Route>

      {/* Catch-all */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
};
