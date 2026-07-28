"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";

import { RepairStatusBadge } from "@/components/repairs/repair-status-badge";
import { UrgencyBadge } from "@/components/repairs/urgency-badge";
import { Button } from "@/components/ui/button";
import { ApiError, fetchRepairs, type RepairSummary } from "@/lib/api";
import { getAccessToken } from "@/lib/auth-storage";

export default function TenantRepairsPage() {
  const [items, setItems] = useState<RepairSummary[]>([]);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    const token = getAccessToken();
    if (!token) return;
    const data = await fetchRepairs(token, { page_size: 50 });
    setItems(data.items);
  }, []);

  useEffect(() => {
    load().catch((err) =>
      setError(err instanceof ApiError ? err.message : "Chargement impossible"),
    );
  }, [load]);

  return (
    <main className="flex flex-col gap-6 px-6 py-10">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-3xl font-bold">Mes réparations</h1>
          <p className="mt-2 text-muted-foreground">Suivez vos signalements de pannes.</p>
        </div>
        <Button asChild>
          <Link href="/espace-locataire/reparations/nouvelle">Signaler une panne</Link>
        </Button>
      </div>

      {error && <p className="text-sm text-red-600">{error}</p>}

      <div className="space-y-3">
        {items.length === 0 ? (
          <p className="rounded-xl border border-border bg-card shadow-sm px-4 py-8 text-center text-muted-foreground">
            Aucun signalement pour le moment.
          </p>
        ) : (
          items.map((item) => (
            <div key={item.id} className="rounded-xl border border-border bg-card shadow-sm p-4">
              <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
                <div>
                  <p className="font-semibold">{item.title}</p>
                  <p className="text-sm text-muted-foreground">{item.unit_code}</p>
                </div>
                <div className="flex gap-2">
                  <UrgencyBadge urgency={item.urgency} />
                  <RepairStatusBadge status={item.status} />
                </div>
              </div>
            </div>
          ))
        )}
      </div>
    </main>
  );
}
