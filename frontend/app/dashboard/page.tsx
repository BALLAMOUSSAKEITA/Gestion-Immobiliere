"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";

import { KpiCard } from "@/components/dashboard/kpi-card";
import { OccupancyChart } from "@/components/dashboard/occupancy-chart";
import { RevenueExpenseChart } from "@/components/dashboard/revenue-expense-chart";
import { PageHeader } from "@/components/layout/page-header";
import { Alert } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
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
      <Alert className="max-w-lg">
        Tableau de bord non disponible pour votre rôle.
      </Alert>
    );
  }

  return (
    <>
      <PageHeader
        title="Tableau de bord"
        description={`Bienvenue, ${user?.first_name}. Vue d'ensemble de l'activité.`}
        actions={
          <div className="flex items-center gap-2">
            <Label className="sr-only">Année</Label>
            <select
              value={year}
              onChange={(e) => setYear(Number(e.target.value))}
              className="h-10 rounded-lg border border-input bg-card px-3 text-sm"
            >
              {[year - 1, year, year + 1].map((y) => (
                <option key={y} value={y}>{y}</option>
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
        }
      />

      {error && <Alert variant="destructive">{error}</Alert>}

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
          <Card className="lg:col-span-2">
            <CardHeader>
              <CardTitle>Revenus vs Dépenses</CardTitle>
            </CardHeader>
            <CardContent>
              {kpis?.show_financials ? (
                <RevenueExpenseChart points={revenuePoints} />
              ) : (
                <p className="text-sm text-muted-foreground">Données financières non disponibles pour votre rôle.</p>
              )}
            </CardContent>
          </Card>
          <Card>
            <CardHeader>
              <CardTitle>Taux d&apos;occupation</CardTitle>
            </CardHeader>
            <CardContent>
              <OccupancyChart points={occupancyPoints} />
            </CardContent>
          </Card>
        </div>

        <div className="grid gap-6 lg:grid-cols-2">
          <Card>
            <CardHeader><CardTitle>Alertes</CardTitle></CardHeader>
            <CardContent>
              {alerts.length === 0 ? (
                <p className="text-sm text-muted-foreground">Aucune alerte.</p>
              ) : (
                <ul className="space-y-3">
                  {alerts.map((alert, index) => (
                    <li key={`${alert.type}-${index}`} className="rounded-lg border border-border bg-background p-3">
                      <p className="font-medium">{alert.title}</p>
                      <p className="text-sm text-muted-foreground">{alert.message}</p>
                      {alert.href && (
                        <Link href={alert.href} className="mt-1 inline-block text-sm text-accent hover:underline">
                          Voir
                        </Link>
                      )}
                    </li>
                  ))}
                </ul>
              )}
            </CardContent>
          </Card>
          <Card>
            <CardHeader><CardTitle>Top impayés</CardTitle></CardHeader>
            <CardContent>
              {overdues.length === 0 ? (
                <p className="text-sm text-muted-foreground">Aucun impayé.</p>
              ) : (
                <ul className="space-y-2 text-sm">
                  {overdues.map((item) => (
                    <li key={`${item.tenant_name}-${item.unit_code}`} className="flex justify-between gap-4">
                      <span>{item.tenant_name} — {item.unit_code}</span>
                      <span className="font-medium text-destructive">
                        {formatCurrency(Number(item.amount_remaining))} ({item.days_overdue}j)
                      </span>
                    </li>
                  ))}
                </ul>
              )}
            </CardContent>
          </Card>
        </div>

        <Card>
          <CardHeader><CardTitle>Baux expirants (30 jours)</CardTitle></CardHeader>
          <CardContent>
            {leases.length === 0 ? (
              <p className="text-sm text-muted-foreground">Aucun bail n&apos;expire prochainement.</p>
            ) : (
              <ul className="space-y-2 text-sm">
                {leases.map((item) => (
                  <li key={`${item.tenant_name}-${item.unit_code}`} className="flex justify-between gap-4">
                    <span>{item.tenant_name} — {item.unit_code} ({item.building_name})</span>
                    <span className="font-medium">{item.days_remaining} jour(s)</span>
                  </li>
                ))}
              </ul>
            )}
          </CardContent>
        </Card>
    </>
  );
}
