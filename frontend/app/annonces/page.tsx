"use client";

import { useEffect, useState } from "react";

import { PublicUnitCard } from "@/components/buildings/public-unit-card";
import { Button } from "@/components/ui/button";
import Link from "next/link";
import {
  ApiError,
  fetchPublicUnits,
  type PublicUnitSummary,
} from "@/lib/api";

export default function AnnoncesPage() {
  const [units, setUnits] = useState<PublicUnitSummary[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchPublicUnits({ page_size: 50 })
      .then((data) => setUnits(data.items))
      .catch((err) =>
        setError(err instanceof ApiError ? err.message : "Chargement impossible"),
      );
  }, []);

  return (
    <main className="mx-auto flex max-w-6xl flex-col gap-8 px-6 py-16">
      <div className="text-center">
        <h1 className="text-3xl font-bold">Annonces</h1>
        <p className="mt-2 text-zinc-600">
          Logements disponibles à la location.
        </p>
      </div>

      {error && <p className="text-center text-sm text-red-600">{error}</p>}

      <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
        {units.map((unit) => (
          <PublicUnitCard key={unit.id} unit={unit} />
        ))}
      </div>

      {units.length === 0 && !error && (
        <p className="text-center text-zinc-500">
          Aucune annonce publique pour le moment.
        </p>
      )}

      <div className="flex justify-center gap-3">
        <Button asChild variant="outline">
          <Link href="/contact">Contact</Link>
        </Button>
        <Button asChild variant="outline">
          <Link href="/">Retour à l&apos;accueil</Link>
        </Button>
      </div>
    </main>
  );
}
