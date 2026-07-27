"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";

import { ProtectedRoute } from "@/components/auth/protected-route";
import { AppHeader } from "@/components/layout/app-header";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  ApiError,
  fetchTenants,
  type TenantSummary,
} from "@/lib/api";
import { getAccessToken } from "@/lib/auth-storage";
import { useAuth } from "@/contexts/auth-context";

export default function TenantsPage() {
  const { user } = useAuth();
  const [tenants, setTenants] = useState<TenantSummary[]>([]);
  const [search, setSearch] = useState("");
  const [error, setError] = useState<string | null>(null);

  const canManage =
    user?.role.code === "super_admin" ||
    user?.role.code === "admin_familial" ||
    user?.role.code === "gestionnaire";

  const loadTenants = useCallback(async () => {
    const token = getAccessToken();
    if (!token) return;
    const data = await fetchTenants(token, { search, page_size: 50 });
    setTenants(data.items);
  }, [search]);

  useEffect(() => {
    loadTenants().catch((err) =>
      setError(err instanceof ApiError ? err.message : "Chargement impossible"),
    );
  }, [loadTenants]);

  return (
    <ProtectedRoute>
      <AppHeader />
      <main className="mx-auto flex w-full max-w-6xl flex-col gap-6 px-6 py-10">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h1 className="text-3xl font-bold">Locataires</h1>
            <p className="mt-2 text-zinc-600">Dossiers locataires et baux en cours.</p>
          </div>
          {canManage && (
            <div className="flex gap-2">
              <Button asChild variant="outline">
                <Link href="/dashboard/baux/nouveau">Nouveau bail</Link>
              </Button>
              <Button asChild>
                <Link href="/dashboard/locataires/nouveau">Nouveau locataire</Link>
              </Button>
            </div>
          )}
        </div>

        <Input
          placeholder="Rechercher par nom, téléphone ou pièce…"
          value={search}
          onChange={(event) => setSearch(event.target.value)}
        />

        {error && <p className="text-sm text-red-600">{error}</p>}

        <div className="overflow-x-auto rounded-xl border border-zinc-200 bg-white">
          <table className="min-w-full text-left text-sm">
            <thead className="border-b border-zinc-200 bg-zinc-50">
              <tr>
                <th className="px-4 py-3">Nom</th>
                <th className="px-4 py-3">Téléphone</th>
                <th className="px-4 py-3">Logement</th>
                <th className="px-4 py-3">Statut</th>
                <th className="px-4 py-3"></th>
              </tr>
            </thead>
            <tbody>
              {tenants.map((tenant) => (
                <tr key={tenant.id} className="border-b border-zinc-100">
                  <td className="px-4 py-3 font-medium">
                    {tenant.first_name} {tenant.last_name}
                  </td>
                  <td className="px-4 py-3">{tenant.phone_primary}</td>
                  <td className="px-4 py-3">{tenant.current_unit_code ?? "—"}</td>
                  <td className="px-4 py-3">
                    {tenant.has_active_lease ? (
                      <span className="rounded-full bg-emerald-100 px-2 py-0.5 text-xs text-emerald-800">
                        Bail actif
                      </span>
                    ) : (
                      <span className="rounded-full bg-zinc-100 px-2 py-0.5 text-xs">
                        Sans bail
                      </span>
                    )}
                  </td>
                  <td className="px-4 py-3">
                    <Link
                      href={`/dashboard/locataires/${tenant.id}`}
                      className="font-medium underline"
                    >
                      Voir
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {tenants.length === 0 && !error && (
            <p className="p-6 text-center text-zinc-500">Aucun locataire.</p>
          )}
        </div>
      </main>
    </ProtectedRoute>
  );
}
