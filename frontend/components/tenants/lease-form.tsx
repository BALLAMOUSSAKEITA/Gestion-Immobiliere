"use client";

import { useState } from "react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import type { LeaseCreatePayload } from "@/lib/api";

type LeaseFormProps = {
  tenants: { id: string; label: string }[];
  units: { id: string; label: string; rent_amount: string }[];
  submitLabel?: string;
  onSubmit: (values: LeaseCreatePayload) => Promise<void>;
};

export function LeaseForm({
  tenants,
  units,
  submitLabel = "Créer le bail",
  onSubmit,
}: LeaseFormProps) {
  const [form, setForm] = useState({
    tenant_id: "",
    unit_id: "",
    start_date: "",
    end_date: "",
    rent_amount: "",
    deposit_amount: "0",
    deposit_paid: false,
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleUnitChange = (unitId: string) => {
    const unit = units.find((item) => item.id === unitId);
    setForm({
      ...form,
      unit_id: unitId,
      rent_amount: unit?.rent_amount ?? form.rent_amount,
    });
  };

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    setLoading(true);
    setError(null);
    try {
      await onSubmit({
        tenant_id: form.tenant_id,
        unit_id: form.unit_id,
        start_date: form.start_date,
        end_date: form.end_date || undefined,
        rent_amount: form.rent_amount,
        deposit_amount: form.deposit_amount || "0",
        deposit_paid: form.deposit_paid,
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
      className="grid gap-4 rounded-xl border border-border bg-card shadow-sm p-6 sm:grid-cols-2"
    >
      <select
        className="rounded-md border border-border px-3 py-2 text-sm sm:col-span-2"
        value={form.tenant_id}
        onChange={(e) => setForm({ ...form, tenant_id: e.target.value })}
        required
      >
        <option value="">Sélectionner un locataire</option>
        {tenants.map((tenant) => (
          <option key={tenant.id} value={tenant.id}>
            {tenant.label}
          </option>
        ))}
      </select>
      <select
        className="rounded-md border border-border px-3 py-2 text-sm sm:col-span-2"
        value={form.unit_id}
        onChange={(e) => handleUnitChange(e.target.value)}
        required
      >
        <option value="">Sélectionner un logement libre</option>
        {units.map((unit) => (
          <option key={unit.id} value={unit.id}>
            {unit.label}
          </option>
        ))}
      </select>
      <Input
        type="date"
        value={form.start_date}
        onChange={(e) => setForm({ ...form, start_date: e.target.value })}
        required
      />
      <Input
        type="date"
        value={form.end_date}
        onChange={(e) => setForm({ ...form, end_date: e.target.value })}
      />
      <Input
        placeholder="Loyer (FG)"
        value={form.rent_amount}
        onChange={(e) => setForm({ ...form, rent_amount: e.target.value })}
        required
      />
      <Input
        placeholder="Caution (FG)"
        value={form.deposit_amount}
        onChange={(e) => setForm({ ...form, deposit_amount: e.target.value })}
      />
      <label className="flex items-center gap-2 text-sm sm:col-span-2">
        <input
          type="checkbox"
          checked={form.deposit_paid}
          onChange={(e) => setForm({ ...form, deposit_paid: e.target.checked })}
        />
        Caution payée
      </label>
      {error && <p className="text-sm text-red-600 sm:col-span-2">{error}</p>}
      <Button type="submit" disabled={loading} className="sm:col-span-2">
        {loading ? "Enregistrement…" : submitLabel}
      </Button>
    </form>
  );
}
