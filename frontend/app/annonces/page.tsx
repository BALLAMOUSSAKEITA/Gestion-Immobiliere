import Link from "next/link";

import { Button } from "@/components/ui/button";

export default function AnnoncesPage() {
  return (
    <main className="mx-auto flex max-w-3xl flex-col gap-4 px-6 py-16 text-center">
      <h1 className="text-2xl font-bold">Annonces</h1>
      <p className="text-zinc-600">Les annonces publiques seront disponibles au Sprint 12.</p>
      <Button asChild variant="outline">
        <Link href="/">Retour à l&apos;accueil</Link>
      </Button>
    </main>
  );
}
