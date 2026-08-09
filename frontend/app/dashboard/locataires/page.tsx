"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  ApiError,
  deleteTenant,
  fetchTenants,
  type TenantSummary,
} from "@/lib/api";
import { getAccessToken } from "@/lib/auth-storage";
import { useAuth } from "@/contexts/auth-context";
import { useConfirm } from "@/contexts/confirm-context";
import { deleteConfirm } from "@/lib/confirm-presets";

export default function TenantsPage() {
  const { user } = useAuth();
  const confirm = useConfirm();
  const [tenants, setTenants] = useState<TenantSummary[]>([]);
  const [search, setSearch] = useState("");
  const [error, setError] = useState<string | null>(null);

  const canManage =
    user?.role.code === "super_admin" ||
    user?.role.code === "admin_familial" ||
    user?.role.code === "gestionnaire";
  const isSuperAdmin = user?.role.code === "super_admin";

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
      <div className="flex flex-col gap-6">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h1 className="text-3xl font-bold">Locataires</h1>
            <p className="mt-2 text-muted-foreground">Dossiers locataires et baux en cours.</p>
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

        <div className="overflow-x-auto rounded-xl border border-border bg-card shadow-sm">
          <table className="min-w-full text-left text-sm">
            <thead className="border-b border-border bg-muted/50">
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
                <tr key={tenant.id} className="border-b border-border">
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
                      <span className="rounded-full bg-muted px-2 py-0.5 text-xs">
                        Sans bail
                      </span>
                    )}
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex items-center justify-end gap-2">
                      <Link
                        href={`/dashboard/locataires/${tenant.id}`}
                        className="font-medium underline"
                      >
                        Voir
                      </Link>
                      {isSuperAdmin && (
                        <Button
                          variant="destructive"
                          size="sm"
                          onClick={async () => {
                            if (
                              !(await confirm(
                                deleteConfirm(
                                  `le locataire « ${tenant.first_name} ${tenant.last_name} »`,
                                ),
                              ))
                            ) {
                              return;
                            }
                            const token = getAccessToken();
                            if (!token) return;
                            setError(null);
                            try {
                              await deleteTenant(token, tenant.id);
                              await loadTenants();
                            } catch (err) {
                              setError(
                                err instanceof ApiError
                                  ? err.message
                                  : "Suppression impossible",
                              );
                            }
                          }}
                        >
                          Supprimer
                        </Button>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {tenants.length === 0 && !error && (
            <p className="p-6 text-center text-muted-foreground">Aucun locataire.</p>
          )}
        </div>
      </div>
  );
}
