"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";

import { ProtectedRoute } from "@/components/auth/protected-route";
import { LeaseStatusBadge } from "@/components/tenants/lease-status-badge";
import { AppHeader } from "@/components/layout/app-header";
import { Button } from "@/components/ui/button";
import {
  ApiError,
  fetchExpiringLeases,
  fetchLeases,
  formatCurrency,
  type LeaseSummary,
} from "@/lib/api";
import { getAccessToken } from "@/lib/auth-storage";
import { useAuth } from "@/contexts/auth-context";

export default function LeasesPage() {
  const { user } = useAuth();
  const [leases, setLeases] = useState<LeaseSummary[]>([]);
  const [expiring, setExpiring] = useState<LeaseSummary[]>([]);
  const [statusFilter, setStatusFilter] = useState<string>("active");
  const [error, setError] = useState<string | null>(null);

  const canManage =
    user?.role.code === "super_admin" ||
    user?.role.code === "admin_familial" ||
    user?.role.code === "gestionnaire";

  const loadLeases = useCallback(async () => {
    const token = getAccessToken();
    if (!token) return;
    const params: Record<string, string> = { page_size: "100" };
    if (statusFilter) params.status = statusFilter;
    const [data, expiringData] = await Promise.all([
      fetchLeases(token, params),
      user?.role.code !== "gestionnaire"
        ? fetchExpiringLeases(token, 30)
        : Promise.resolve({ items: [] }),
    ]);
    setLeases(data.items);
    setExpiring(expiringData.items);
  }, [statusFilter, user?.role.code]);

  useEffect(() => {
    loadLeases().catch((err) =>
      setError(err instanceof ApiError ? err.message : "Chargement impossible"),
    );
  }, [loadLeases]);

  return (
    <ProtectedRoute>
      <AppHeader />
      <main className="mx-auto flex w-full max-w-6xl flex-col gap-6 px-6 py-10">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h1 className="text-3xl font-bold">Baux</h1>
            <p className="mt-2 text-zinc-600">Contrats de location actifs et historiques.</p>
          </div>
          {canManage && (
            <Button asChild>
              <Link href="/dashboard/baux/nouveau">Nouveau bail</Link>
            </Button>
          )}
        </div>

        {expiring.length > 0 && (
          <div className="rounded-xl border border-amber-200 bg-amber-50 p-4">
            <p className="font-medium text-amber-900">
              {expiring.length} bail(s) expirent dans les 30 prochains jours
            </p>
          </div>
        )}

        <select
          className="w-full max-w-xs rounded-md border border-zinc-200 px-3 py-2 text-sm"
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
        >
          <option value="active">Actifs</option>
          <option value="terminated">Résiliés</option>
          <option value="expired">Expirés</option>
          <option value="">Tous</option>
        </select>

        {error && <p className="text-sm text-red-600">{error}</p>}

        <div className="overflow-x-auto rounded-xl border border-zinc-200 bg-white">
          <table className="min-w-full text-left text-sm">
            <thead className="border-b border-zinc-200 bg-zinc-50">
              <tr>
                <th className="px-4 py-3">Locataire</th>
                <th className="px-4 py-3">Logement</th>
                <th className="px-4 py-3">Loyer</th>
                <th className="px-4 py-3">Période</th>
                <th className="px-4 py-3">Statut</th>
                <th className="px-4 py-3"></th>
              </tr>
            </thead>
            <tbody>
              {leases.map((lease) => (
                <tr key={lease.id} className="border-b border-zinc-100">
                  <td className="px-4 py-3">{lease.tenant_name}</td>
                  <td className="px-4 py-3">
                    {lease.building_name} — {lease.unit_code}
                  </td>
                  <td className="px-4 py-3">{formatCurrency(lease.rent_amount)}</td>
                  <td className="px-4 py-3">
                    {lease.start_date}
                    {lease.end_date ? ` → ${lease.end_date}` : ""}
                  </td>
                  <td className="px-4 py-3">
                    <LeaseStatusBadge status={lease.status} />
                  </td>
                  <td className="px-4 py-3">
                    <Link
                      href={`/dashboard/baux/${lease.id}`}
                      className="font-medium underline"
                    >
                      Détail
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {leases.length === 0 && !error && (
            <p className="p-6 text-center text-zinc-500">Aucun bail.</p>
          )}
        </div>
      </main>
    </ProtectedRoute>
  );
}
