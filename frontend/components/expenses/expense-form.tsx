"use client";

import { useState } from "react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  PAYMENT_METHOD_LABELS,
  type ExpenseCategory,
  type ExpenseCreatePayload,
  type PaymentMethod,
} from "@/lib/api";

type ExpenseFormProps = {
  categories: ExpenseCategory[];
  buildings: { id: string; label: string }[];
  onSubmit: (values: ExpenseCreatePayload) => Promise<void>;
};

export function ExpenseForm({ categories, buildings, onSubmit }: ExpenseFormProps) {
  const [form, setForm] = useState({
    category_id: categories[0]?.id ?? "",
    building_id: buildings[0]?.id ?? "",
    supplier_name: "",
    description: "",
    amount: "",
    payment_method: "cash" as PaymentMethod,
    expense_date: new Date().toISOString().slice(0, 10),
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    setLoading(true);
    setError(null);
    try {
      await onSubmit({
        category_id: form.category_id,
        building_id: form.building_id || undefined,
        supplier_name: form.supplier_name || undefined,
        description: form.description,
        amount: form.amount,
        payment_method: form.payment_method,
        expense_date: form.expense_date,
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
      className="grid gap-4 rounded-xl border border-zinc-200 bg-white p-6"
    >
      {error && <p className="text-sm text-red-600">{error}</p>}

      <div>
        <label htmlFor="category_id" className="mb-1 block text-sm text-zinc-600">
          Catégorie
        </label>
        <select
          id="category_id"
          value={form.category_id}
          onChange={(e) => setForm({ ...form, category_id: e.target.value })}
          className="w-full rounded-md border border-zinc-300 px-3 py-2 text-sm"
          required
        >
          {categories.map((category) => (
            <option key={category.id} value={category.id}>
              {category.label}
            </option>
          ))}
        </select>
      </div>

      <div>
        <label htmlFor="building_id" className="mb-1 block text-sm text-zinc-600">
          Immeuble
        </label>
        <select
          id="building_id"
          value={form.building_id}
          onChange={(e) => setForm({ ...form, building_id: e.target.value })}
          className="w-full rounded-md border border-zinc-300 px-3 py-2 text-sm"
          required
        >
          {buildings.map((building) => (
            <option key={building.id} value={building.id}>
              {building.label}
            </option>
          ))}
        </select>
      </div>

      <div>
        <label htmlFor="supplier_name" className="mb-1 block text-sm text-zinc-600">
          Fournisseur
        </label>
        <Input
          id="supplier_name"
          value={form.supplier_name}
          onChange={(e) => setForm({ ...form, supplier_name: e.target.value })}
        />
      </div>

      <div>
        <label htmlFor="description" className="mb-1 block text-sm text-zinc-600">
          Description
        </label>
        <textarea
          id="description"
          value={form.description}
          onChange={(e) => setForm({ ...form, description: e.target.value })}
          rows={3}
          required
          className="w-full rounded-md border border-zinc-300 px-3 py-2 text-sm"
        />
      </div>

      <div className="grid gap-4 sm:grid-cols-2">
        <div>
          <label htmlFor="amount" className="mb-1 block text-sm text-zinc-600">
            Montant (FCFA)
          </label>
          <Input
            id="amount"
            type="number"
            min="1"
            step="1"
            value={form.amount}
            onChange={(e) => setForm({ ...form, amount: e.target.value })}
            required
          />
        </div>
        <div>
          <label htmlFor="expense_date" className="mb-1 block text-sm text-zinc-600">
            Date
          </label>
          <Input
            id="expense_date"
            type="date"
            value={form.expense_date}
            onChange={(e) => setForm({ ...form, expense_date: e.target.value })}
            required
          />
        </div>
      </div>

      <div>
        <label htmlFor="payment_method" className="mb-1 block text-sm text-zinc-600">
          Mode de paiement
        </label>
        <select
          id="payment_method"
          value={form.payment_method}
          onChange={(e) =>
            setForm({ ...form, payment_method: e.target.value as PaymentMethod })
          }
          className="w-full rounded-md border border-zinc-300 px-3 py-2 text-sm"
        >
          {Object.entries(PAYMENT_METHOD_LABELS).map(([value, label]) => (
            <option key={value} value={value}>
              {label}
            </option>
          ))}
        </select>
      </div>

      <Button type="submit" disabled={loading}>
        {loading ? "Enregistrement…" : "Enregistrer la dépense"}
      </Button>
    </form>
  );
}
