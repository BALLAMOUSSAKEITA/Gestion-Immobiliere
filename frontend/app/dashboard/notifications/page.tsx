"use client";

import { useEffect, useState } from "react";

import { Button } from "@/components/ui/button";
import {
  ApiError,
  fetchNotifications,
  markAllNotificationsRead,
  markNotificationRead,
  type NotificationSummary,
} from "@/lib/api";
import { getAccessToken } from "@/lib/auth-storage";

export default function NotificationsPage() {
  const [items, setItems] = useState<NotificationSummary[]>([]);
  const [error, setError] = useState<string | null>(null);

  async function load() {
    const token = getAccessToken();
    if (!token) return;
    const data = await fetchNotifications(token, 100);
    setItems(data.items);
  }

  useEffect(() => {
    load().catch((err) =>
      setError(err instanceof ApiError ? err.message : "Chargement impossible"),
    );
  }, []);

  async function handleMarkRead(id: string) {
    const token = getAccessToken();
    if (!token) return;
    await markNotificationRead(token, id);
    await load();
  }

  async function handleMarkAll() {
    const token = getAccessToken();
    if (!token) return;
    await markAllNotificationsRead(token);
    await load();
  }

  return (
    <main className="mx-auto flex w-full max-w-3xl flex-col gap-6 px-6 py-10">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Notifications</h1>
          <p className="mt-2 text-zinc-600">Historique de vos alertes.</p>
        </div>
        <Button variant="outline" onClick={handleMarkAll}>
          Tout marquer lu
        </Button>
      </div>

      {error && <p className="text-sm text-red-600">{error}</p>}

      <div className="space-y-3">
        {items.length === 0 ? (
          <p className="rounded-xl border border-zinc-200 bg-white px-4 py-8 text-center text-zinc-500">
            Aucune notification pour le moment.
          </p>
        ) : (
          items.map((item) => (
            <div
              key={item.id}
              className={`rounded-xl border border-zinc-200 bg-white p-4 ${!item.is_read ? "border-blue-200 bg-blue-50/40" : ""}`}
            >
              <div className="flex items-start justify-between gap-3">
                <div>
                  <p className="font-semibold">{item.title}</p>
                  <p className="mt-1 text-sm text-zinc-600">{item.body}</p>
                  <p className="mt-2 text-xs text-zinc-400">
                    {new Date(item.created_at).toLocaleString("fr-FR")}
                  </p>
                </div>
                {!item.is_read && (
                  <Button variant="outline" onClick={() => handleMarkRead(item.id)}>
                    Lu
                  </Button>
                )}
              </div>
            </div>
          ))
        )}
      </div>
    </main>
  );
}
