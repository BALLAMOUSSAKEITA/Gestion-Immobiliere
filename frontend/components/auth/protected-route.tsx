"use client";

import { useEffect } from "react";

import { useAuth } from "@/contexts/auth-context";

export function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, isLoading } = useAuth();

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      window.location.href = "/login";
    }
  }, [isAuthenticated, isLoading]);

  if (isLoading) {
    return (
      <div className="flex flex-1 items-center justify-center py-16 text-zinc-500">
        Chargement...
      </div>
    );
  }

  if (!isAuthenticated) {
    return null;
  }

  return <>{children}</>;
}
