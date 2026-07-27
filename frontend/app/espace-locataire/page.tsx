"use client";

import Link from "next/link";

import { ProtectedRoute } from "@/components/auth/protected-route";
import { Button } from "@/components/ui/button";

export default function TenantSpacePage() {
  return (
    <ProtectedRoute>
      <main className="mx-auto flex max-w-3xl flex-col gap-4 px-6 py-16 text-center">
        <h1 className="text-2xl font-bold">Espace locataire</h1>
        <p className="text-zinc-600">Consultez vos impayés et vos documents.</p>
        <div className="flex flex-col items-center gap-3 sm:flex-row sm:justify-center">
          <Button asChild>
            <Link href="/espace-locataire/impayes">Mes impayés</Link>
          </Button>
          <Button asChild variant="outline">
            <Link href="/dashboard/paiements">Mes paiements</Link>
          </Button>
          <Button asChild variant="outline">
            <Link href="/dashboard">Tableau de bord</Link>
          </Button>
        </div>
      </main>
    </ProtectedRoute>
  );
}
