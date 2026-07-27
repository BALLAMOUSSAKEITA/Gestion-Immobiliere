"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useCallback, useEffect, useState } from "react";

import { ProtectedRoute } from "@/components/auth/protected-route";
import { AppHeader } from "@/components/layout/app-header";
import { Button } from "@/components/ui/button";
import {
  ApiError,
  fetchOverdue,
  formatCurrency,
  REMINDER_CHANNEL_LABELS,
  sendReminder,
  type OverdueItem,
} from "@/lib/api";
import { getAccessToken } from "@/lib/auth-storage";
import { useAuth } from "@/contexts/auth-context";

export default function OverdueDetailPage() {
  const params = useParams<{ id: string }>();
  const { user } = useAuth();
  const [item, setItem] = useState<OverdueItem | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState("");
  const [channel, setChannel] = useState("email");
  const [sending, setSending] = useState(false);
  const [sent, setSent] = useState(false);

  const canSend =
    user?.role.code === "super_admin" ||
    user?.role.code === "admin_familial" ||
    user?.role.code === "gestionnaire";

  const load = useCallback(async () => {
    const token = getAccessToken();
    if (!token || !params.id) return;
    const data = await fetchOverdue(token, params.id);
    setItem(data);
    setMessage(
      `Bonjour ${data.tenant.full_name}, votre loyer de ${data.period} d'un montant de ${formatCurrency(data.amount_remaining)} reste impayé (${data.days_overdue} jours de retard). Merci de régulariser.`,
    );
  }, [params.id]);

  useEffect(() => {
    load().catch((err) =>
      setError(err instanceof ApiError ? err.message : "Chargement impossible"),
    );
  }, [load]);

  async function handleSend(e: React.FormEvent) {
    e.preventDefault();
    if (!item) return;
    const token = getAccessToken();
    if (!token) return;
    setSending(true);
    setError(null);
    try {
      await sendReminder(token, {
        tenant_id: item.tenant.id,
        overdue_record_ids: [item.id],
        reminder_type: "manual",
        channel,
        message,
      });
      setSent(true);
      await load();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Envoi impossible");
    } finally {
      setSending(false);
    }
  }

  return (
    <ProtectedRoute>
      <AppHeader />
      <main className="mx-auto flex w-full max-w-3xl flex-col gap-6 px-6 py-10">
        <Button asChild variant="outline" className="w-fit">
          <Link href="/dashboard/impayes">← Retour aux impayés</Link>
        </Button>

        {error && <p className="text-sm text-red-600">{error}</p>}
        {sent && (
          <p className="rounded-md bg-green-50 px-4 py-3 text-sm text-green-700">
            Relance enregistrée avec succès.
          </p>
        )}

        {item && (
          <>
            <div>
              <h1 className="text-3xl font-bold">Détail impayé</h1>
              <p className="mt-2 text-zinc-600">
                {item.tenant.full_name} — {item.unit_code} ({item.building_name})
              </p>
            </div>

            <div className="grid gap-4 rounded-xl border border-zinc-200 bg-white p-6 sm:grid-cols-2">
              <div>
                <p className="text-sm text-zinc-500">Période</p>
                <p className="font-medium">{item.period}</p>
              </div>
              <div>
                <p className="text-sm text-zinc-500">Jours de retard</p>
                <p className="font-medium text-red-600">{item.days_overdue} jours</p>
              </div>
              <div>
                <p className="text-sm text-zinc-500">Montant dû</p>
                <p className="font-medium">{formatCurrency(item.amount_due)}</p>
              </div>
              <div>
                <p className="text-sm text-zinc-500">Montant payé</p>
                <p className="font-medium">{formatCurrency(item.amount_paid)}</p>
              </div>
              <div>
                <p className="text-sm text-zinc-500">Reste dû</p>
                <p className="font-medium text-red-600">{formatCurrency(item.amount_remaining)}</p>
              </div>
              <div>
                <p className="text-sm text-zinc-500">Total impayé locataire</p>
                <p className="font-medium">{formatCurrency(item.tenant_total_overdue)}</p>
              </div>
              <div>
                <p className="text-sm text-zinc-500">Relances envoyées</p>
                <p className="font-medium">{item.reminders_count}</p>
              </div>
              <div>
                <p className="text-sm text-zinc-500">Statut</p>
                <p className="font-medium">{item.status}</p>
              </div>
            </div>

            {canSend && (
              <form
                onSubmit={handleSend}
                className="flex flex-col gap-4 rounded-xl border border-zinc-200 bg-white p-6"
              >
                <h2 className="text-lg font-semibold">Envoyer une relance</h2>
                <div>
                  <label htmlFor="channel" className="mb-1 block text-sm text-zinc-600">
                    Canal
                  </label>
                  <select
                    id="channel"
                    value={channel}
                    onChange={(e) => setChannel(e.target.value)}
                    className="w-full rounded-md border border-zinc-300 px-3 py-2 text-sm"
                  >
                    {Object.entries(REMINDER_CHANNEL_LABELS).map(([value, label]) => (
                      <option key={value} value={value}>
                        {label}
                      </option>
                    ))}
                  </select>
                </div>
                <div>
                  <label htmlFor="message" className="mb-1 block text-sm text-zinc-600">
                    Message
                  </label>
                  <textarea
                    id="message"
                    value={message}
                    onChange={(e) => setMessage(e.target.value)}
                    rows={4}
                    required
                    className="w-full rounded-md border border-zinc-300 px-3 py-2 text-sm"
                  />
                </div>
                <Button type="submit" disabled={sending}>
                  {sending ? "Envoi…" : "Enregistrer la relance"}
                </Button>
              </form>
            )}
          </>
        )}
      </main>
    </ProtectedRoute>
  );
}
