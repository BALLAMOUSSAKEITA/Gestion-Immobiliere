"use client";

import { ProtectedRoute } from "@/components/auth/protected-route";
import { TenantSidebar } from "@/components/layout/tenant-sidebar";

export default function TenantLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <ProtectedRoute>
      <div className="mx-auto flex min-h-screen max-w-6xl flex-col lg:flex-row">
        <TenantSidebar />
        <div className="flex-1">{children}</div>
      </div>
    </ProtectedRoute>
  );
}
