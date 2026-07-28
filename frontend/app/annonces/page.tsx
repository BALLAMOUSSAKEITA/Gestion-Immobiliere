"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { Search } from "lucide-react";

import { PublicUnitCard } from "@/components/buildings/public-unit-card";
import { PageHeader } from "@/components/layout/page-header";
import { EmptyState } from "@/components/layout/empty-state";
import { Button } from "@/components/ui/button";
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
      <PageHeader
        title="Annonces immobilières"
        description="Découvrez les logements disponibles à la location."
        actions={
          <Button asChild variant="outline">
            <Link href="/contact">Nous contacter</Link>
          </Button>
        }
      />

      {error && <Alert variant="destructive" className="mb-6">{error}</Alert>}

      {units.length === 0 && !error ? (
        <EmptyState
          title="Aucune annonce disponible"
          description="Revenez bientôt pour découvrir de nouveaux logements."
          actionLabel="Retour à l'accueil"
          actionHref="/"
        />
      ) : (
        <div className="grid gap-6 sm:grid-cols-2 xl:grid-cols-3">
          {units.map((unit) => (
            <PublicUnitCard key={unit.id} unit={unit} />
          ))}
        </div>
      )}
    </div>
  );
}
