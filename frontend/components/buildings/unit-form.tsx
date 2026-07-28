"use client";

import { useState } from "react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import type { UnitCreatePayload, UnitType } from "@/lib/api";

type UnitFormProps = {
  submitLabel?: string;
  onSubmit: (values: UnitCreatePayload) => Promise<void>;
};

const UNIT_TYPES: { value: UnitType; label: string }[] = [
  { value: "apartment", label: "Appartement" },
  { value: "shop", label: "Magasin" },
  { value: "office", label: "Bureau" },
];

export function UnitForm({ submitLabel = "Créer le logement", onSubmit }: UnitFormProps) {
  const [form, setForm] = useState({
    type: "apartment" as UnitType,
    number: "",
    floor: "",
    rent_amount: "",
    deposit_amount: "0",
    description: "",
    is_public_listing: false,
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    setLoading(true);
    setError(null);
    try {
      await onSubmit({
        type: form.type,
        number: form.number,
        floor: form.floor ? Number(form.floor) : undefined,
        rent_amount: form.rent_amount,
        deposit_amount: form.deposit_amount || "0",
        description: form.description || undefined,
        is_public_listing: form.is_public_listing,
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
        className="rounded-md border border-border px-3 py-2 text-sm"
        value={form.type}
        onChange={(e) =>
          setForm({ ...form, type: e.target.value as UnitType })
        }
      >
        {UNIT_TYPES.map((item) => (
          <option key={item.value} value={item.value}>
            {item.label}
          </option>
        ))}
      </select>
      <Input
        placeholder="Numéro"
        value={form.number}
        onChange={(e) => setForm({ ...form, number: e.target.value })}
        required
      />
      {form.type === "apartment" && (
        <Input
          type="number"
          min={0}
          placeholder="Étage"
          value={form.floor}
          onChange={(e) => setForm({ ...form, floor: e.target.value })}
        />
      )}
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
      <textarea
        placeholder="Description"
        value={form.description}
        onChange={(e) => setForm({ ...form, description: e.target.value })}
        className="min-h-24 rounded-md border border-border px-3 py-2 text-sm sm:col-span-2"
      />
      <label className="flex items-center gap-2 text-sm sm:col-span-2">
        <input
          type="checkbox"
          checked={form.is_public_listing}
          onChange={(e) =>
            setForm({ ...form, is_public_listing: e.target.checked })
          }
        />
        Visible sur les annonces publiques
      </label>
      {error && (
        <p className="text-sm text-red-600 sm:col-span-2">{error}</p>
      )}
      <Button type="submit" disabled={loading} className="sm:col-span-2">
        {loading ? "Enregistrement…" : submitLabel}
      </Button>
    </form>
  );
}
