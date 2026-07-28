"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";

import { Button } from "@/components/ui/button";
import { ApiError, fetchReports, type ReportSummary } from "@/lib/api";
import { getAccessToken } from "@/lib/auth-storage";

export default function RapportsPage() {
  const [items, setItems] = useState<ReportSummary[]>([]);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    const token = getAccessToken();
    if (!token) return;
    const data = await fetchReports(token);
    setItems(data.items);
  }, []);

  useEffect(() => {
    load().catch((err) =>
      setError(err instanceof ApiError ? err.message : "Chargement impossible"),
    );
  }, [load]);

  return (
      <div className="flex flex-col gap-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold">Rapports</h1>
            <p className="mt-2 text-muted-foreground">Historique des rapports générés.</p>
          </div>
          <Button asChild>
            <Link href="/dashboard/rapports/generer">Générer un rapport</Link>
          </Button>
        </div>

        {error && <p className="text-sm text-red-600">{error}</p>}

        <div className="space-y-3">
          {items.length === 0 ? (
            <p className="rounded-xl border border-border bg-card shadow-sm px-4 py-8 text-center text-muted-foreground">
              Aucun rapport généré.
            </p>
          ) : (
            items.map((item) => (
              <div
                key={item.id}
                className="flex flex-col gap-2 rounded-xl border border-border bg-card shadow-sm p-4 sm:flex-row sm:items-center sm:justify-between"
              >
                <div>
                  <p className="font-semibold capitalize">{item.report_type}</p>
                  <p className="text-sm text-muted-foreground">
                    {item.period_start} → {item.period_end}
                  </p>
                  <p className="text-xs text-muted-foreground">
                    {new Date(item.generated_at).toLocaleString("fr-FR")}
                    {item.generated_by_name ? ` — ${item.generated_by_name}` : ""}
                  </p>
                </div>
                <Button asChild variant="outline">
                  <Link href={`/dashboard/rapports/${item.id}`}>Ouvrir</Link>
                </Button>
              </div>
            ))
          )}
        </div>
      </div>
  );
}
