"use client";

import { useState } from "react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  PAYMENT_METHOD_LABELS,
  type PaymentCreatePayload,
  type PaymentMethod,
} from "@/lib/api";

type PaymentFormProps = {
  leases: { id: string; label: string }[];
  onSubmit: (values: PaymentCreatePayload) => Promise<void>;
};

export function PaymentForm({ leases, onSubmit }: PaymentFormProps) {
  const [leaseId, setLeaseId] = useState("");
  const [form, setForm] = useState({
    amount: "",
    payment_method: "cash" as PaymentMethod,
    payment_date: new Date().toISOString().slice(0, 10),
    reference: "",
    notes: "",
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    setLoading(true);
    setError(null);
    try {
      await onSubmit({
        lease_id: leaseId,
        amount: form.amount,
        payment_method: form.payment_method,
        payment_date: form.payment_date,
        reference: form.reference || undefined,
        notes: form.notes || undefined,
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
        onChange={(e) => setLeaseId(e.target.value)}
        required
      >
        <option value="">Sélectionner un bail actif</option>
        {leases.map((lease) => (
          <option key={lease.id} value={lease.id}>
            {lease.label}
          </option>
        ))}
      </select>

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
