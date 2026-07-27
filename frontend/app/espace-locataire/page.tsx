"use client";

import Link from "next/link";

import { ProtectedRoute } from "@/components/auth/protected-route";
import { Button } from "@/components/ui/button";

export default function TenantSpacePage() {
  return (
    <ProtectedRoute>
      <main className="mx-auto flex max-w-3xl flex-col gap-4 px-6 py-16 text-center">
        <h1 className="text-2xl font-bold">Espace locataire</h1>
        <p className="text-zinc-600">Disponible au Sprint 12.</p>
        <Button asChild variant="outline">
          <Link href="/dashboard">Retour au tableau de bord</Link>
        </Button>
      </main>
    </ProtectedRoute>
  );
}
