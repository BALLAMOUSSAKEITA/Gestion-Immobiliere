import Link from "next/link";

import { Button } from "@/components/ui/button";
import { fetchHealth } from "@/lib/api";

async function ApiStatus() {
  try {
    const health = await fetchHealth();
    return (
      <div className="flex items-center gap-2 rounded-lg border border-emerald-200 bg-emerald-50 px-4 py-3 text-emerald-800">
        <span className="h-2 w-2 rounded-full bg-emerald-500" />
        <span>API connectée — version {health.version}</span>
      </div>
    );
  } catch {
    return (
      <div className="flex items-center gap-2 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-red-800">
        <span className="h-2 w-2 rounded-full bg-red-500" />
        <span>API non disponible — démarrez le backend sur le port 8000</span>
      </div>
    );
  }
}

export default function Home() {
  return (
    <main className="mx-auto flex w-full max-w-3xl flex-1 flex-col items-center justify-center gap-8 px-6 py-16">
      <div className="text-center">
        <p className="mb-2 text-sm font-medium uppercase tracking-wider text-zinc-500">
          Plateforme
        </p>
        <h1 className="text-4xl font-bold tracking-tight">
          Gestion Immobilière
        </h1>
        <p className="mt-4 text-lg text-zinc-600">
          Gérez vos immeubles, locataires, loyers et documents en un seul
          endroit.
        </p>
      </div>

      <ApiStatus />

      <Button asChild size="lg">
        <Link href="/login">Connexion</Link>
      </Button>
    </main>
  );
}
