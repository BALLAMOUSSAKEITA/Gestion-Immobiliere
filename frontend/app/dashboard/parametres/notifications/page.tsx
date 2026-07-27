"use client";

import { useEffect, useState } from "react";

import { Button } from "@/components/ui/button";
import {
  ApiError,
  fetchNotificationPreferences,
  updateNotificationPreferences,
  type NotificationPreferenceItem,
} from "@/lib/api";
import { getAccessToken } from "@/lib/auth-storage";

export default function NotificationPreferencesPage() {
  const [items, setItems] = useState<NotificationPreferenceItem[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    const token = getAccessToken();
    if (!token) return;
    fetchNotificationPreferences(token)
      .then((data) => setItems(data.items))
      .catch((err) =>
        setError(err instanceof ApiError ? err.message : "Chargement impossible"),
      );
  }, []);

  async function handleSave() {
    const token = getAccessToken();
    if (!token) return;
    setSaved(false);
    const data = await updateNotificationPreferences(
      token,
      items.map((item) => ({
        event_code: item.event_code,
        in_app_enabled: item.in_app_enabled,
        email_enabled: item.email_enabled,
        whatsapp_enabled: item.whatsapp_enabled,
      })),
    );
    setItems(data.items);
    setSaved(true);
  }

  function toggle(
    eventCode: string,
    field: "in_app_enabled" | "email_enabled" | "whatsapp_enabled",
  ) {
    setItems((current) =>
      current.map((item) =>
        item.event_code === eventCode ? { ...item, [field]: !item[field] } : item,
      ),
    );
  }

  return (
    <main className="mx-auto flex w-full max-w-3xl flex-col gap-6 px-6 py-10">
      <div>
        <h1 className="text-3xl font-bold">Préférences notifications</h1>
        <p className="mt-2 text-zinc-600">Choisissez comment vous souhaitez être alerté.</p>
      </div>

      {error && <p className="text-sm text-red-600">{error}</p>}
      {saved && (
        <p className="rounded-lg border border-green-200 bg-green-50 px-4 py-3 text-sm text-green-800">
          Préférences enregistrées.
        </p>
      )}

      <div className="space-y-3">
        {items.map((item) => (
          <div key={item.event_code} className="rounded-xl border border-zinc-200 bg-white p-4">
            <p className="font-medium">{item.label}</p>
            <div className="mt-3 flex flex-wrap gap-4 text-sm">
              <label className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={item.in_app_enabled}
                  onChange={() => toggle(item.event_code, "in_app_enabled")}
                />
                In-app
              </label>
              <label className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={item.email_enabled}
                  onChange={() => toggle(item.event_code, "email_enabled")}
                />
                Email
              </label>
              <label className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={item.whatsapp_enabled}
                  onChange={() => toggle(item.event_code, "whatsapp_enabled")}
                />
                WhatsApp
              </label>
            </div>
          </div>
        ))}
      </div>

      <Button onClick={handleSave} className="w-fit">
        Enregistrer
      </Button>
    </main>
  );
}
