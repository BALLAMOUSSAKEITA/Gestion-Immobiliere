"use client";

import { useState } from "react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  fetchLeasePeriods,
  formatCurrency,
  PAYMENT_METHOD_LABELS,
  type PaymentCreatePayload,
  type PaymentMethod,
  type RentPeriod,
} from "@/lib/api";
import { getAccessToken } from "@/lib/auth-storage";

type PaymentFormProps = {
  leases: { id: string; label: string }[];
  onSubmit: (values: PaymentCreatePayload) => Promise<void>;
};

export function PaymentForm({ leases, onSubmit }: PaymentFormProps) {
  const [leaseId, setLeaseId] = useState("");
  const [periods, setPeriods] = useState<RentPeriod[]>([]);
  const [form, setForm] = useState({
    amount: "",
    payment_method: "cash" as PaymentMethod,
    payment_date: new Date().toISOString().slice(0, 10),
    reference: "",
    notes: "",
  });
  const [allocations, setAllocations] = useState<
    Record<string, string>
  >({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadPeriods = async (id: string) => {
    const token = getAccessToken();
    if (!token || !id) return;
    const data = await fetchLeasePeriods(token, id);
    setPeriods(data.filter((period) => period.remaining_amount !== "0.00" && Number(period.remaining_amount) > 0));
    setAllocations({});
  };

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const allocationList = Object.entries(allocations)
        .filter(([, amount]) => amount && Number(amount) > 0)
        .map(([key, amount]) => {
          const [year, month] = key.split("-");
          return {
            period_year: Number(year),
            period_month: Number(month),
            amount,
          };
        });

      await onSubmit({
        lease_id: leaseId,
        amount: form.amount,
        payment_method: form.payment_method,
        payment_date: form.payment_date,
        reference: form.reference || undefined,
        notes: form.notes || undefined,
        allocations: allocationList.length > 0 ? allocationList : undefined,
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erreur");
    } finally {
      setLoading(false);
    }
  };

  return (
    <form
      onSubmit={handleSubmit}
      className="grid gap-4 rounded-xl border border-border bg-card shadow-sm p-6"
    >
      <select
        className="rounded-md border border-border px-3 py-2 text-sm"
        value={leaseId}
        onChange={(e) => {
          setLeaseId(e.target.value);
          loadPeriods(e.target.value).catch(() => setPeriods([]));
        }}
        required
      >
        <option value="">Sélectionner un bail actif</option>
        {leases.map((lease) => (
          <option key={lease.id} value={lease.id}>
            {lease.label}
          </option>
        ))}
      </select>

      {periods.length > 0 && (
        <div className="space-y-2 rounded-lg bg-muted/50 p-4">
          <p className="text-sm font-medium">Répartition par mois (optionnel)</p>
          {periods.map((period) => {
            const key = `${period.period_year}-${period.period_month}`;
            return (
              <div key={period.id} className="flex items-center gap-3 text-sm">
                <span className="w-20">
                  {String(period.period_month).padStart(2, "0")}/{period.period_year}
                </span>
                <span className="text-muted-foreground">
                  Reste : {formatCurrency(period.remaining_amount)}
                </span>
                <Input
                  placeholder="Montant"
                  value={allocations[key] ?? ""}
                  onChange={(e) =>
                    setAllocations({ ...allocations, [key]: e.target.value })
                  }
                  className="max-w-[140px]"
                />
              </div>
            );
          })}
          <p className="text-xs text-muted-foreground">
            Laissez vide pour une répartition automatique sur les mois les plus anciens.
          </p>
        </div>
      )}

      <div className="grid gap-4 sm:grid-cols-2">
        <Input
          placeholder="Montant total (FG)"
          value={form.amount}
          onChange={(e) => setForm({ ...form, amount: e.target.value })}
          required
        />
        <select
          className="rounded-md border border-border px-3 py-2 text-sm"
          value={form.payment_method}
          onChange={(e) =>
            setForm({ ...form, payment_method: e.target.value as PaymentMethod })
          }
        >
          {Object.entries(PAYMENT_METHOD_LABELS).map(([value, label]) => (
            <option key={value} value={value}>
              {label}
            </option>
          ))}
        </select>
        <Input
          type="date"
          value={form.payment_date}
          onChange={(e) => setForm({ ...form, payment_date: e.target.value })}
          required
        />
        <Input
          placeholder="Référence transaction"
          value={form.reference}
          onChange={(e) => setForm({ ...form, reference: e.target.value })}
        />
      </div>
      <Input
        placeholder="Notes"
        value={form.notes}
        onChange={(e) => setForm({ ...form, notes: e.target.value })}
      />
      {error && <p className="text-sm text-red-600">{error}</p>}
      <Button type="submit" disabled={loading}>
        {loading ? "Enregistrement…" : "Enregistrer et générer le reçu"}
      </Button>
    </form>
  );
}
