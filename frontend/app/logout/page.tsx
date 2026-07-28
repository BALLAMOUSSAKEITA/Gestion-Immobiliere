"use client";

import { useEffect } from "react";

import { useAuth } from "@/contexts/auth-context";

export default function LogoutPage() {
  const { logout } = useAuth();

  useEffect(() => {
    logout();
  }, [logout]);

  return (
    <main className="flex flex-1 items-center justify-center py-16 text-muted-foreground">
      Déconnexion en cours...
    </main>
  );
}
