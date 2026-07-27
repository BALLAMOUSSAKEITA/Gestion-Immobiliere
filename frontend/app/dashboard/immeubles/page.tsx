"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";

import { ProtectedRoute } from "@/components/auth/protected-route";
import { AppHeader } from "@/components/layout/app-header";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  ApiError,
  fetchBuildings,
  type BuildingSummary,
} from "@/lib/api";
import { getAccessToken } from "@/lib/auth-storage";
import { useAuth } from "@/contexts/auth-context";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function BuildingsPage() {
  const { user } = useAuth();
  const [buildings, setBuildings] = useState<BuildingSummary[]>([]);
  const [search, setSearch] = useState("");
  const [error, setError] = useState<string | null>(null);

  const canManage =
    user?.role.code === "super_admin" || user?.role.code === "admin_familial";

  const loadBuildings = useCallback(async () => {
    const token = getAccessToken();
    if (!token) return;
    const data = await fetchBuildings(token, { search, page_size: 50 });
    setBuildings(data.items);
  }, [search]);

  useEffect(() => {
    loadBuildings().catch((err) =>
      setError(err instanceof ApiError ? err.message : "Chargement impossible"),
    );
  }, [loadBuildings]);

  return (
    <ProtectedRoute>
      <AppHeader />
      <main className="mx-auto flex w-full max-w-6xl flex-col gap-6 px-6 py-10">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h1 className="text-3xl font-bold">Immeubles</h1>
            <p className="mt-2 text-zinc-600">Patrimoine immobilier de la famille.</p>
          </div>
          {canManage && (
            <Button asChild>
              <Link href="/dashboard/immeubles/nouveau">Nouvel immeuble</Link>
            </Button>
          )}
        </div>

        <Input
          placeholder="Rechercher par code, nom ou commune…"
          value={search}
          onChange={(event) => setSearch(event.target.value)}
        />

        {error && <p className="text-sm text-red-600">{error}</p>}

        <div className="grid gap-4 md:grid-cols-2">
          {buildings.map((building) => (
            <Link
              key={building.id}
              href={`/dashboard/immeubles/${building.id}`}
              className="overflow-hidden rounded-xl border border-zinc-200 bg-white shadow-sm transition hover:shadow-md"
            >
              <div className="aspect-[16/9] bg-zinc-100">
                {building.photo_url ? (
                  // eslint-disable-next-line @next/next/no-img-element
                  <img
                    src={`${API_URL}${building.photo_url}`}
                    alt={building.name}
                    className="h-full w-full object-cover"
                  />
                ) : (
                  <div className="flex h-full items-center justify-center text-sm text-zinc-400">
                    {building.code}
                  </div>
                )}
              </div>
              <div className="space-y-2 p-4">
                <div className="flex items-start justify-between gap-2">
                  <div>
                    <p className="font-semibold">{building.name}</p>
                    <p className="text-sm text-zinc-500">{building.code}</p>
                  </div>
                  <span className="rounded-full bg-zinc-100 px-2 py-0.5 text-xs">
                    {building.apartment_count + building.shop_count} logements
                  </span>
                </div>
                <p className="text-sm text-zinc-600">
                  {building.commune}
                  {building.quartier ? ` · ${building.quartier}` : ""}
                </p>
              </div>
            </Link>
          ))}
        </div>

        {buildings.length === 0 && !error && (
          <p className="text-center text-zinc-500">Aucun immeuble trouvé.</p>
        )}
      </main>
    </ProtectedRoute>
  );
}
