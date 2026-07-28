"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { ArrowRight } from "lucide-react";

import { PublicUnitCard } from "@/components/buildings/public-unit-card";
import { EmptyState } from "@/components/layout/empty-state";
import { Alert } from "@/components/ui/alert";
import { ApiError, fetchPublicUnits, type PublicUnitSummary } from "@/lib/api";

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
    <div className="page-container">
      <div className="section-gap flex items-end justify-between gap-4">
        <div>
          <h1 className="heading-section">Logements disponibles</h1>
          <p className="mt-2 text-sm text-muted-foreground">
            {units.length > 0
              ? `${units.length} annonce${units.length > 1 ? "s" : ""} à la location`
              : "Découvrez les logements disponibles à la location."}
          </p>
        </div>
        <Link href="/contact" className="hidden items-center gap-1 text-sm font-medium text-foreground hover:underline sm:flex">
          Nous contacter
          <ArrowRight className="h-4 w-4" />
        </Link>
      </div>

      {error && <Alert variant="destructive" className="mb-6">{error}</Alert>}

      {units.length === 0 && !error ? (
        <EmptyState
          title="Aucune annonce disponible"
          description="Revenez bientôt pour découvrir de nouveaux logements."
          actionLabel="Retour à l'accueil"
          actionHref="/"
        />
      ) : (
        <div className="grid gap-x-6 gap-y-10 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
          {units.map((unit) => (
            <PublicUnitCard key={unit.id} unit={unit} />
          ))}
        </div>
      )}
    </div>
  );
}
