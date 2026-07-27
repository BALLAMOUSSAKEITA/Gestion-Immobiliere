"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";

import { Button } from "@/components/ui/button";
import {
  ApiError,
  fetchPublicUnit,
  formatCurrency,
  UNIT_TYPE_LABELS,
  type PublicUnitDetail,
} from "@/lib/api";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function PublicUnitPage() {
  const params = useParams<{ id: string }>();
  const [unit, setUnit] = useState<PublicUnitDetail | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!params.id) return;
    fetchPublicUnit(params.id)
      .then(setUnit)
      .catch((err) =>
        setError(err instanceof ApiError ? err.message : "Annonce introuvable"),
      );
  }, [params.id]);

  return (
    <main className="mx-auto flex max-w-4xl flex-col gap-6 px-6 py-16">
      {!unit ? (
        <p className="text-center text-zinc-500">{error ?? "Chargement…"}</p>
      ) : (
        <>
          <div>
            <p className="text-sm text-zinc-500">{unit.code}</p>
            <h1 className="text-3xl font-bold">{UNIT_TYPE_LABELS[unit.type]}</h1>
            <p className="mt-2 text-zinc-600">
              {unit.commune}
              {unit.quartier ? ` · ${unit.quartier}` : ""}
            </p>
          </div>

          <p className="text-2xl font-bold">{formatCurrency(unit.rent_amount)} / mois</p>

          {unit.description && (
            <p className="rounded-xl border border-zinc-200 bg-white p-4 text-zinc-700">
              {unit.description}
            </p>
          )}

          {unit.photos.length > 0 && (
            <div className="grid gap-3 sm:grid-cols-2">
              {unit.photos.map((photo) => (
                // eslint-disable-next-line @next/next/no-img-element
                <img
                  key={photo.id}
                  src={`${API_URL}${photo.url}`}
                  alt={unit.code}
                  className="aspect-video rounded-lg object-cover"
                />
              ))}
            </div>
          )}
        </>
      )}

      <Button asChild variant="outline" className="self-center">
        <Link href="/annonces">Retour aux annonces</Link>
      </Button>
    </main>
  );
}
