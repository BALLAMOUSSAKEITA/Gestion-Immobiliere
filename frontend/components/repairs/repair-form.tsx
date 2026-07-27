"use client";

import { useState } from "react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { type RepairCreatePayload, type UrgencyLevel } from "@/lib/api";

type RepairFormProps = {
  units?: { id: string; label: string }[];
  showUnitSelect?: boolean;
  onSubmit: (values: RepairCreatePayload) => Promise<void>;
};

export function RepairForm({ units = [], showUnitSelect = true, onSubmit }: RepairFormProps) {
  const [form, setForm] = useState({
    unit_id: units[0]?.id ?? "",
    title: "",
    description: "",
    urgency: "medium" as UrgencyLevel,
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    setLoading(true);
    setError(null);
    try {
      await onSubmit({
        unit_id: showUnitSelect ? form.unit_id : undefined,
        title: form.title,
        description: form.description,
        urgency: form.urgency,
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

      {showUnitSelect && units.length > 0 && (
        <div>
          <label htmlFor="unit_id" className="mb-1 block text-sm text-zinc-600">
            Logement
          </label>
          <select
            id="unit_id"
            value={form.unit_id}
            onChange={(e) => setForm({ ...form, unit_id: e.target.value })}
            className="w-full rounded-md border border-zinc-300 px-3 py-2 text-sm"
            required
          >
            {units.map((unit) => (
              <option key={unit.id} value={unit.id}>
                {unit.label}
              </option>
            ))}
          </select>
        </div>
      )}

      <div>
        <label htmlFor="title" className="mb-1 block text-sm text-zinc-600">
          Titre
        </label>
        <Input
          id="title"
          value={form.title}
          onChange={(e) => setForm({ ...form, title: e.target.value })}
          required
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
          rows={4}
          required
          className="w-full rounded-md border border-zinc-300 px-3 py-2 text-sm"
        />
      </div>

      <div>
        <label htmlFor="urgency" className="mb-1 block text-sm text-zinc-600">
          Urgence
        </label>
        <select
          id="urgency"
          value={form.urgency}
          onChange={(e) => setForm({ ...form, urgency: e.target.value as UrgencyLevel })}
          className="w-full rounded-md border border-zinc-300 px-3 py-2 text-sm"
        >
          <option value="low">Faible</option>
          <option value="medium">Moyen</option>
          <option value="high">Élevé</option>
        </select>
      </div>

      <Button type="submit" disabled={loading}>
        {loading ? "Envoi…" : "Signaler la réparation"}
      </Button>
    </form>
  );
}
