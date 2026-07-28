"use client";

import { useState } from "react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  ID_DOCUMENT_LABELS,
  PAYMENT_METHOD_LABELS,
  type IdDocumentType,
  type PaymentMethod,
  type TenantCreatePayload,
} from "@/lib/api";

type TenantFormProps = {
  submitLabel?: string;
  onSubmit: (values: TenantCreatePayload) => Promise<void>;
};

export function TenantForm({ submitLabel = "Enregistrer", onSubmit }: TenantFormProps) {
  const [form, setForm] = useState({
    first_name: "",
    last_name: "",
    phone_primary: "",
    phone_secondary: "",
    profession: "",
    previous_address: "",
    id_document_type: "cni" as IdDocumentType,
    id_document_number: "",
    emergency_contact_name: "",
    emergency_contact_phone: "",
    payment_method: "" as PaymentMethod | "",
    observations: "",
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    setLoading(true);
    setError(null);
    try {
      await onSubmit({
        first_name: form.first_name,
        last_name: form.last_name,
        phone_primary: form.phone_primary,
        phone_secondary: form.phone_secondary || undefined,
        profession: form.profession || undefined,
        previous_address: form.previous_address || undefined,
        id_document_type: form.id_document_type,
        id_document_number: form.id_document_number,
        emergency_contact_name: form.emergency_contact_name || undefined,
        emergency_contact_phone: form.emergency_contact_phone || undefined,
        payment_method: form.payment_method || undefined,
        observations: form.observations || undefined,
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
      <Input
        placeholder="Prénom"
        value={form.first_name}
        onChange={(e) => setForm({ ...form, first_name: e.target.value })}
        required
      />
      <Input
        placeholder="Nom"
        value={form.last_name}
        onChange={(e) => setForm({ ...form, last_name: e.target.value })}
        required
      />
      <Input
        placeholder="Téléphone principal"
        value={form.phone_primary}
        onChange={(e) => setForm({ ...form, phone_primary: e.target.value })}
        required
      />
      <Input
        placeholder="Téléphone secondaire"
        value={form.phone_secondary}
        onChange={(e) => setForm({ ...form, phone_secondary: e.target.value })}
      />
      <Input
        placeholder="Profession"
        value={form.profession}
        onChange={(e) => setForm({ ...form, profession: e.target.value })}
      />
      <select
        className="rounded-md border border-border px-3 py-2 text-sm"
        value={form.payment_method}
        onChange={(e) =>
          setForm({ ...form, payment_method: e.target.value as PaymentMethod })
        }
      >
        <option value="">Mode de paiement</option>
        {Object.entries(PAYMENT_METHOD_LABELS).map(([value, label]) => (
          <option key={value} value={value}>
            {label}
          </option>
        ))}
      </select>
      <select
        className="rounded-md border border-border px-3 py-2 text-sm"
        value={form.id_document_type}
        onChange={(e) =>
          setForm({ ...form, id_document_type: e.target.value as IdDocumentType })
        }
      >
        {Object.entries(ID_DOCUMENT_LABELS).map(([value, label]) => (
          <option key={value} value={value}>
            {label}
          </option>
        ))}
      </select>
      <Input
        placeholder="Numéro pièce d'identité"
        value={form.id_document_number}
        onChange={(e) => setForm({ ...form, id_document_number: e.target.value })}
        required
      />
      <Input
        placeholder="Contact urgence — nom"
        value={form.emergency_contact_name}
        onChange={(e) =>
          setForm({ ...form, emergency_contact_name: e.target.value })
        }
      />
      <Input
        placeholder="Contact urgence — téléphone"
        value={form.emergency_contact_phone}
        onChange={(e) =>
          setForm({ ...form, emergency_contact_phone: e.target.value })
        }
      />
      <Input
        placeholder="Ancienne adresse"
        value={form.previous_address}
        onChange={(e) => setForm({ ...form, previous_address: e.target.value })}
        className="sm:col-span-2"
      />
      <textarea
        placeholder="Observations"
        value={form.observations}
        onChange={(e) => setForm({ ...form, observations: e.target.value })}
        className="min-h-24 rounded-md border border-border px-3 py-2 text-sm sm:col-span-2"
      />
      {error && <p className="text-sm text-red-600 sm:col-span-2">{error}</p>}
      <Button type="submit" disabled={loading} className="sm:col-span-2">
        {loading ? "Enregistrement…" : submitLabel}
      </Button>
    </form>
  );
}
