"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";

import { ProtectedRoute } from "@/components/auth/protected-route";
import { AppHeader } from "@/components/layout/app-header";
import { Button } from "@/components/ui/button";
import {
  ApiError,
  fetchReminders,
  REMINDER_CHANNEL_LABELS,
  REMINDER_TYPE_LABELS,
  type ReminderItem,
} from "@/lib/api";
import { getAccessToken } from "@/lib/auth-storage";

export default function RemindersPage() {
  const [items, setItems] = useState<ReminderItem[]>([]);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    const token = getAccessToken();
    if (!token) return;
    const data = await fetchReminders(token, { page_size: 50 });
    setItems(data.items);
  }, []);

  useEffect(() => {
    load().catch((err) =>
      setError(err instanceof ApiError ? err.message : "Chargement impossible"),
    );
  }, [load]);

  return (
    <ProtectedRoute>
      <AppHeader />
      <main className="mx-auto flex w-full max-w-6xl flex-col gap-6 px-6 py-10">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h1 className="text-3xl font-bold">Relances</h1>
            <p className="mt-2 text-muted-foreground">Historique des relances automatiques et manuelles.</p>
          </div>
          <Button asChild variant="outline">
            <Link href="/dashboard/impayes">Voir les impayés</Link>
          </Button>
        </div>

        {error && <p className="text-sm text-red-600">{error}</p>}

        <div className="overflow-x-auto rounded-xl border border-border bg-card shadow-sm">
          <table className="min-w-full text-left text-sm">
            <thead className="border-b border-border bg-muted/50">
              <tr>
                <th className="px-4 py-3">Date</th>
                <th className="px-4 py-3">Locataire</th>
                <th className="px-4 py-3">Type</th>
                <th className="px-4 py-3">Canal</th>
                <th className="px-4 py-3">Message</th>
                <th className="px-4 py-3">Envoyé par</th>
              </tr>
            </thead>
            <tbody>
              {items.length === 0 ? (
                <tr>
                  <td colSpan={6} className="px-4 py-8 text-center text-muted-foreground">
                    Aucune relance enregistrée.
                  </td>
                </tr>
              ) : (
                items.map((item) => (
                  <tr key={item.id} className="border-b border-border">
                    <td className="px-4 py-3 whitespace-nowrap">
                      {new Date(item.sent_at).toLocaleString("fr-FR")}
                    </td>
                    <td className="px-4 py-3">{item.tenant_name}</td>
                    <td className="px-4 py-3">{REMINDER_TYPE_LABELS[item.reminder_type]}</td>
                    <td className="px-4 py-3">{REMINDER_CHANNEL_LABELS[item.channel]}</td>
                    <td className="max-w-xs truncate px-4 py-3" title={item.message}>
                      {item.message}
                    </td>
                    <td className="px-4 py-3">{item.sent_by_name ?? "Automatique"}</td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </main>
    </ProtectedRoute>
  );
}
