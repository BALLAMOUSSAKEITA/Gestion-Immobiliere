"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";

import { ProtectedRoute } from "@/components/auth/protected-route";
import { KpiCard } from "@/components/dashboard/kpi-card";
import { OccupancyChart } from "@/components/dashboard/occupancy-chart";
import { RevenueExpenseChart } from "@/components/dashboard/revenue-expense-chart";
import { AppHeader } from "@/components/layout/app-header";
import { Button } from "@/components/ui/button";
import {
  ApiError,
  fetchDashboardAlerts,
  fetchDashboardExpiringLeases,
  fetchDashboardKpis,
  fetchDashboardTopOverdues,
  fetchOccupancyChart,
  fetchRevenueExpenseChart,
  formatCurrency,
  type DashboardAlert,
  type DashboardKpis,
  type MonthlySeriesPoint,
} from "@/lib/api";
import { getAccessToken } from "@/lib/auth-storage";
import { useAuth } from "@/contexts/auth-context";

export default function DashboardPage() {
  const { user } = useAuth();
  const [kpis, setKpis] = useState<DashboardKpis | null>(null);
  const [revenuePoints, setRevenuePoints] = useState<MonthlySeriesPoint[]>([]);
  const [occupancyPoints, setOccupancyPoints] = useState<{ label: string; occupancy_rate: number }[]>([]);
  const [alerts, setAlerts] = useState<DashboardAlert[]>([]);
  const [overdues, setOverdues] = useState<
    { tenant_name: string; unit_code: string; amount_remaining: number; days_overdue: number }[]
  >([]);
  const [leases, setLeases] = useState<
    { tenant_name: string; unit_code: string; building_name: string; days_remaining: number }[]
  >([]);
  const [error, setError] = useState<string | null>(null);
  const [year, setYear] = useState(new Date().getFullYear());

  const canViewDashboard =
    user?.role.code === "super_admin" ||
    user?.role.code === "admin_familial" ||
    user?.role.code === "proprietaire" ||
    user?.role.code === "gestionnaire";

  const load = useCallback(async () => {
    const token = getAccessToken();
    if (!token) return;
    const [kpiData, revenue, occupancy, alertData, overdueData, leaseData] = await Promise.all([
      fetchDashboardKpis(token, { year }),
      fetchRevenueExpenseChart(token, { year }),
      fetchOccupancyChart(token, { year }),
      fetchDashboardAlerts(token),
      fetchDashboardTopOverdues(token),
      fetchDashboardExpiringLeases(token),
    ]);
    setKpis(kpiData);
    setRevenuePoints(revenue.points);
    setOccupancyPoints(occupancy.points);
    setAlerts(alertData.items);
    setOverdues(overdueData.items);
    setLeases(leaseData.items);
  }, [year]);

  useEffect(() => {
    if (!canViewDashboard) return;
    load().catch((err) =>
      setError(err instanceof ApiError ? err.message : "Chargement impossible"),
    );
  }, [load, canViewDashboard]);

  if (user && !canViewDashboard) {
    return (
      <ProtectedRoute>
        <AppHeader />
        <main className="mx-auto max-w-4xl px-6 py-10">
          <p className="text-zinc-600">Tableau de bord non disponible pour votre rôle.</p>
        </main>
      </ProtectedRoute>
    );
  }

  return (
    <ProtectedRoute>
      <AppHeader />
      <main className="mx-auto flex w-full max-w-6xl flex-col gap-6 px-6 py-10">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <h1 className="text-3xl font-bold">Tableau de bord</h1>
            <p className="mt-2 text-zinc-600">
              Bienvenue, {user?.first_name}. Vue d&apos;ensemble de l&apos;activité.
            </p>
          </div>
          <div className="flex items-center gap-2">
            <label className="text-sm text-zinc-500">Année</label>
            <select
              value={year}
              onChange={(e) => setYear(Number(e.target.value))}
              className="rounded-md border border-zinc-300 px-3 py-2 text-sm"
            >
              {[year - 1, year, year + 1].map((y) => (
                <option key={y} value={y}>
                  {y}
                </option>
              ))}
            </select>
            {(user?.role.code === "super_admin" ||
              user?.role.code === "admin_familial" ||
              user?.role.code === "proprietaire") && (
              <Button asChild variant="outline">
                <Link href="/dashboard/rapports">Rapports</Link>
              </Button>
            )}
          </div>
        </div>

        {error && <p className="text-sm text-red-600">{error}</p>}

        {kpis && (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <KpiCard label="Immeubles" value={String(kpis.total_buildings)} />
            <KpiCard label="Appartements" value={String(kpis.total_apartments)} />
            <KpiCard label="Magasins" value={String(kpis.total_shops)} />
            <KpiCard label="Occupés / Libres" value={`${kpis.occupied_units} / ${kpis.free_units}`} />
            {kpis.show_financials && (
              <>
                <KpiCard
                  label="Loyers attendus"
                  value={formatCurrency(Number(kpis.expected_rent_month ?? 0))}
                />
                <KpiCard
                  label="Loyers encaissés"
                  value={formatCurrency(Number(kpis.collected_rent_month ?? 0))}
                />
                <KpiCard
                  label="Dépenses du mois"
                  value={formatCurrency(Number(kpis.expenses_month ?? 0))}
                />
                <KpiCard
                  label="Bénéfice net"
                  value={formatCurrency(Number(kpis.net_profit_month ?? 0))}
                />
              </>
            )}
            <KpiCard label="Impayés" value={formatCurrency(Number(kpis.overdue_amount))} />
            <KpiCard label="Baux expirants" value={String(kpis.expiring_leases_count)} />
            <KpiCard label="Réparations en cours" value={String(kpis.repairs_in_progress)} />
          </div>
        )}

        <div className="grid gap-6 lg:grid-cols-3">
          <div className="rounded-xl border border-zinc-200 bg-white p-5 lg:col-span-2">
            <h2 className="mb-4 text-lg font-semibold">Revenus vs Dépenses</h2>
            {kpis?.show_financials ? (
              <RevenueExpenseChart points={revenuePoints} />
            ) : (
              <p className="text-sm text-zinc-500">Données financières non disponibles pour votre rôle.</p>
            )}
          </div>
          <div className="rounded-xl border border-zinc-200 bg-white p-5">
            <h2 className="mb-4 text-lg font-semibold">Taux d&apos;occupation</h2>
            <OccupancyChart points={occupancyPoints} />
          </div>
        </div>

        <div className="grid gap-6 lg:grid-cols-2">
          <div className="rounded-xl border border-zinc-200 bg-white p-5">
            <h2 className="mb-4 text-lg font-semibold">Alertes</h2>
            {alerts.length === 0 ? (
              <p className="text-sm text-zinc-500">Aucune alerte.</p>
            ) : (
              <ul className="space-y-3">
                {alerts.map((alert, index) => (
                  <li key={`${alert.type}-${index}`} className="rounded-lg border border-zinc-100 p-3">
                    <p className="font-medium">{alert.title}</p>
                    <p className="text-sm text-zinc-600">{alert.message}</p>
                    {alert.href && (
                      <Link href={alert.href} className="mt-1 inline-block text-sm underline">
                        Voir
                      </Link>
                    )}
                  </li>
                ))}
              </ul>
            )}
          </div>
          <div className="rounded-xl border border-zinc-200 bg-white p-5">
            <h2 className="mb-4 text-lg font-semibold">Top impayés</h2>
            {overdues.length === 0 ? (
              <p className="text-sm text-zinc-500">Aucun impayé.</p>
            ) : (
              <ul className="space-y-2 text-sm">
                {overdues.map((item) => (
                  <li key={`${item.tenant_name}-${item.unit_code}`} className="flex justify-between">
                    <span>
                      {item.tenant_name} — {item.unit_code}
                    </span>
                    <span className="font-medium">
                      {formatCurrency(Number(item.amount_remaining))} ({item.days_overdue}j)
                    </span>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </div>

        <div className="rounded-xl border border-zinc-200 bg-white p-5">
          <h2 className="mb-4 text-lg font-semibold">Baux expirants (30 jours)</h2>
          {leases.length === 0 ? (
            <p className="text-sm text-zinc-500">Aucun bail n&apos;expire prochainement.</p>
          ) : (
            <ul className="space-y-2 text-sm">
              {leases.map((item) => (
                <li key={`${item.tenant_name}-${item.unit_code}`} className="flex justify-between">
                  <span>
                    {item.tenant_name} — {item.unit_code} ({item.building_name})
                  </span>
                  <span>{item.days_remaining} jour(s)</span>
                </li>
              ))}
            </ul>
          )}
        </div>
      </main>
    </ProtectedRoute>
  );
}
