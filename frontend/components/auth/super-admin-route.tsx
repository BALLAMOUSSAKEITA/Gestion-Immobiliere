"use client";

import { useEffect } from "react";

import { useAuth } from "@/contexts/auth-context";

export function SuperAdminRoute({ children }: { children: React.ReactNode }) {
  const { user, isLoading, isAuthenticated } = useAuth();

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      window.location.href = "/login";
      return;
    }
    if (!isLoading && user && user.role.code !== "super_admin") {
      window.location.href = "/dashboard";
    }
  }, [isAuthenticated, isLoading, user]);

  if (isLoading || !user) {
    return (
      <div className="flex flex-1 items-center justify-center py-16 text-muted-foreground">
        Chargement...
      </div>
    );
  }

  if (user.role.code !== "super_admin") {
    return null;
  }

  return <>{children}</>;
}
