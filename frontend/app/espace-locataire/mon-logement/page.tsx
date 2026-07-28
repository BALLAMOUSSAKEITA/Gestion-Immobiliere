"use client";

import { useEffect, useState } from "react";

import { ApiError, fetchTenantUnit, type TenantUnitInfo } from "@/lib/api";
import { getAccessToken } from "@/lib/auth-storage";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function TenantUnitPage() {
  const [unit, setUnit] = useState<TenantUnitInfo | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const token = getAccessToken();
    if (!token) return;
    fetchTenantUnit(token)
      .then(setUnit)
      .catch((err) =>
        setError(err instanceof ApiError ? err.message : "Chargement impossible"),
      );
  }, []);

  return (
    <main className="flex flex-col gap-6 px-6 py-10">
      <div>
        <h1 className="text-3xl font-bold">Mon logement</h1>
        <p className="mt-2 text-muted-foreground">Détails de votre logement actuel.</p>
      </div>

      {error && <p className="text-sm text-red-600">{error}</p>}

      {unit && (
        <div className="space-y-4 rounded-xl border border-border bg-card shadow-sm p-6">
          <div>
            <p className="text-sm text-muted-foreground">Code</p>
            <p className="text-xl font-bold">{unit.code}</p>
          </div>
          <div className="grid gap-4 sm:grid-cols-2">
            <div>
              <p className="text-sm text-muted-foreground">Type</p>
              <p>{unit.type}</p>
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Numéro</p>
              <p>{unit.number}</p>
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Immeuble</p>
              <p>{unit.building_name}</p>
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Commune</p>
              <p>
                {unit.commune}
                {unit.quartier ? ` · ${unit.quartier}` : ""}
              </p>
            </div>
          </div>
          {unit.description && (
            <p className="rounded-lg bg-muted/50 p-4 text-foreground">{unit.description}</p>
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
        </div>
      )}
    </main>
  );
}
