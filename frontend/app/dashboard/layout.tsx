"use client";

import { AppHeader } from "@/components/layout/app-header";
import { ProtectedRoute } from "@/components/auth/protected-route";

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <ProtectedRoute>
      <AppHeader />
      {children}
    </ProtectedRoute>
  );
}
