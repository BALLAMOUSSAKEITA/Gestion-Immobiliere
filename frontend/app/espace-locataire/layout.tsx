"use client";

import { ProtectedRoute } from "@/components/auth/protected-route";
import { TenantShell } from "@/components/layout/tenant-sidebar";

export default function TenantLayout({ children }: { children: React.ReactNode }) {
  return (
    <ProtectedRoute>
      <TenantShell>{children}</TenantShell>
    </ProtectedRoute>
  );
}
