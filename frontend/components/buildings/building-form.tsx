"use client";

import { useState } from "react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ImageUploadField } from "@/components/ui/image-upload-field";
import type { BuildingCreatePayload } from "@/lib/api";

type BuildingFormProps = {
  initialValues?: Partial<BuildingCreatePayload>;
  ownerProfiles: { id: string; label: string }[];
  managers: { id: string; label: string }[];
  submitLabel?: string;
  showPhotoField?: boolean;
  onSubmit: (values: BuildingCreatePayload, photo?: File | null) => Promise<void>;
};

export function BuildingForm({
  initialValues,
  ownerProfiles,
  managers,
  submitLabel = "Enregistrer",
  showPhotoField = false,
  onSubmit,
}: BuildingFormProps) {
  const [photoFile, setPhotoFile] = useState<File | null>(null);
  const [form, setForm] = useState({
    name: initialValues?.name ?? "",
    address: initialValues?.address ?? "",
    commune: initialValues?.commune ?? "",
    quartier: initialValues?.quartier ?? "",
    floor_count: String(initialValues?.floor_count ?? 0),
    owner_profile_id: initialValues?.owner_profile_id ?? "",
    manager_user_id: initialValues?.manager_user_id ?? "",
    observations: initialValues?.observations ?? "",
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    setLoading(true);
    setError(null);
    try {
      await onSubmit(
        {
          name: form.name,
          address: form.address,
          commune: form.commune,
          quartier: form.quartier || undefined,
          floor_count: Number(form.floor_count) || 0,
          owner_profile_id: form.owner_profile_id || undefined,
          manager_user_id: form.manager_user_id || undefined,
          observations: form.observations || undefined,
        },
        photoFile,
      );
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
        placeholder="Nom de l'immeuble"
        value={form.name}
        onChange={(e) => setForm({ ...form, name: e.target.value })}
        required
      />
      <Input
        placeholder="Commune"
        value={form.commune}
        onChange={(e) => setForm({ ...form, commune: e.target.value })}
        required
      />
      <Input
        placeholder="Quartier"
        value={form.quartier}
        onChange={(e) => setForm({ ...form, quartier: e.target.value })}
        className="sm:col-span-2"
      />
      <Input
        placeholder="Adresse complète"
        value={form.address}
        onChange={(e) => setForm({ ...form, address: e.target.value })}
        className="sm:col-span-2"
        required
      />
      <Input
        type="number"
        min={0}
        placeholder="Nombre d'étages"
        value={form.floor_count}
        onChange={(e) => setForm({ ...form, floor_count: e.target.value })}
      />
      <select
        className="rounded-md border border-border px-3 py-2 text-sm"
        value={form.owner_profile_id}
        onChange={(e) =>
          setForm({ ...form, owner_profile_id: e.target.value })
        }
      >
        <option value="">Propriétaire (optionnel)</option>
        {ownerProfiles.map((profile) => (
          <option key={profile.id} value={profile.id}>
            {profile.label}
          </option>
        ))}
      </select>
      <select
        className="rounded-md border border-border px-3 py-2 text-sm sm:col-span-2"
        value={form.manager_user_id}
        onChange={(e) =>
          setForm({ ...form, manager_user_id: e.target.value })
        }
      >
        <option value="">Gestionnaire (optionnel)</option>
        {managers.map((manager) => (
          <option key={manager.id} value={manager.id}>
            {manager.label}
          </option>
        ))}
      </select>
      <textarea
        placeholder="Observations"
        value={form.observations}
        onChange={(e) => setForm({ ...form, observations: e.target.value })}
        className="min-h-24 rounded-md border border-border px-3 py-2 text-sm sm:col-span-2"
      />
      {showPhotoField && (
        <div className="sm:col-span-2">
          <ImageUploadField
            embedded
            selectOnly
            label="Photo de l'immeuble (optionnel)"
            hint="Sera enregistrée automatiquement après la création."
            onFileSelect={(files) => setPhotoFile(files[0] ?? null)}
          />
        </div>
      )}
      {error && (
        <p className="text-sm text-red-600 sm:col-span-2">{error}</p>
      )}
      <Button type="submit" disabled={loading} className="sm:col-span-2">
        {loading ? "Enregistrement…" : submitLabel}
      </Button>
    </form>
  );
}
