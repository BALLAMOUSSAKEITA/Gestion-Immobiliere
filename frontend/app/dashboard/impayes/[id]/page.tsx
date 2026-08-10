"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useCallback, useEffect, useState } from "react";

import { Button } from "@/components/ui/button";
import {
  ApiError,
  fetchOverdue,
  formatCurrency,
  type OverdueItem,
} from "@/lib/api";
import { getAccessToken } from "@/lib/auth-storage";

export default function OverdueDetailPage() {
  const params = useParams<{ id: string }>();
  const [item, setItem] = useState<OverdueItem | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    const token = getAccessToken();
    if (!token || !params.id) return;
    const data = await fetchOverdue(token, params.id);
    setItem(data);
  }, [params.id]);

  useEffect(() => {
    load().catch((err) =>
      setError(err instanceof ApiError ? err.message : "Chargement impossible"),
    );
  }, [load]);

  return (
    <div className="flex flex-col gap-6">
      <Button asChild variant="outline" className="w-fit">
        <Link href="/dashboard/impayes">← Retour aux impayés</Link>
      </Button>

      {error && <p className="text-sm text-red-600">{error}</p>}

      {item && (
        <>
          <div>
            <h1 className="text-3xl font-bold">Détail impayé</h1>
            <p className="mt-2 text-muted-foreground">
              {item.tenant.full_name} — {item.unit_code} ({item.building_name})
            </p>
          </div>

          <div className="grid gap-4 rounded-xl border border-border bg-card shadow-sm p-6 sm:grid-cols-2">
            <div>
              <p className="text-sm text-muted-foreground">Période</p>
              <p className="font-medium">{item.period}</p>
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Jours de retard</p>
              <p className="font-medium text-red-600">{item.days_overdue} jours</p>
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Montant dû</p>
              <p className="font-medium">{formatCurrency(item.amount_due)}</p>
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Montant payé</p>
              <p className="font-medium">{formatCurrency(item.amount_paid)}</p>
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Reste dû</p>
              <p className="font-medium text-red-600">
                {formatCurrency(item.amount_remaining)}
              </p>
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Total impayé locataire</p>
              <p className="font-medium">{formatCurrency(item.tenant_total_overdue)}</p>
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Statut</p>
              <p className="font-medium">{item.status}</p>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
