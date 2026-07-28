"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";

import { ProtectedRoute } from "@/components/auth/protected-route";
import { UnitStatusBadge } from "@/components/buildings/unit-status-badge";
import { AppHeader } from "@/components/layout/app-header";
import { Input } from "@/components/ui/input";
import {
  ApiError,
  fetchUnits,
  formatCurrency,
  UNIT_TYPE_LABELS,
  type UnitSummary,
} from "@/lib/api";
import { getAccessToken } from "@/lib/auth-storage";

export default function UnitsPage() {
  const [units, setUnits] = useState<UnitSummary[]>([]);
  const [search, setSearch] = useState("");
  const [error, setError] = useState<string | null>(null);

  const loadUnits = useCallback(async () => {
    const token = getAccessToken();
    if (!token) return;
    const data = await fetchUnits(token, { search, page_size: 100 });
    setUnits(data.items);
  }, [search]);

  useEffect(() => {
    loadUnits().catch((err) =>
      setError(err instanceof ApiError ? err.message : "Chargement impossible"),
    );
  }, [loadUnits]);

  return (
    <ProtectedRoute>
      <AppHeader />
      <main className="mx-auto flex w-full max-w-6xl flex-col gap-6 px-6 py-10">
        <div>
          <h1 className="text-3xl font-bold">Logements</h1>
          <p className="mt-2 text-muted-foreground">Vue globale du parc locatif.</p>
        </div>

        <Input
          placeholder="Rechercher par code ou numéro…"
          value={search}
          onChange={(event) => setSearch(event.target.value)}
        />

        {error && <p className="text-sm text-red-600">{error}</p>}

        <div className="overflow-x-auto rounded-xl border border-border bg-card shadow-sm">
          <table className="min-w-full text-left text-sm">
            <thead className="border-b border-border bg-muted/50">
              <tr>
                <th className="px-4 py-3">Code</th>
                <th className="px-4 py-3">Immeuble</th>
                <th className="px-4 py-3">Type</th>
                <th className="px-4 py-3">Loyer</th>
                <th className="px-4 py-3">Statut</th>
                <th className="px-4 py-3"></th>
              </tr>
            </thead>
            <tbody>
              {units.map((unit) => (
                <tr key={unit.id} className="border-b border-border">
                  <td className="px-4 py-3 font-medium">{unit.code}</td>
                  <td className="px-4 py-3">{unit.building_name ?? "—"}</td>
                  <td className="px-4 py-3">{UNIT_TYPE_LABELS[unit.type]}</td>
                  <td className="px-4 py-3">{formatCurrency(unit.rent_amount)}</td>
                  <td className="px-4 py-3">
                    <UnitStatusBadge status={unit.status} />
                  </td>
                  <td className="px-4 py-3">
                    <Link
                      href={`/dashboard/logements/${unit.id}`}
                      className="font-medium underline"
                    >
                      Détail
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {units.length === 0 && !error && (
            <p className="p-6 text-center text-muted-foreground">Aucun logement.</p>
          )}
        </div>
      </main>
    </ProtectedRoute>
  );
}
