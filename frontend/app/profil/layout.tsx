"use client";

import { ProtectedRoute } from "@/components/auth/protected-route";
import { DashboardShell } from "@/components/layout/dashboard-shell";
import { TenantShell } from "@/components/layout/tenant-sidebar";
import { useAuth } from "@/contexts/auth-context";

function AuthShell({ children }: { children: React.ReactNode }) {
  const { user } = useAuth();
  if (!user) return null;
  if (user.role.code === "locataire") {
    return <TenantShell>{children}</TenantShell>;
  }
  return <DashboardShell>{children}</DashboardShell>;
}

export default function ProfilLayout({ children }: { children: React.ReactNode }) {
  return (
    <ProtectedRoute>
      <AuthShell>{children}</AuthShell>
    </ProtectedRoute>
  );
}
