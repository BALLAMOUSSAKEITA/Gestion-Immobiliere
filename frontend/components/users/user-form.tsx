"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  ApiError,
  createUser,
  fetchOwnerProfiles,
  PERMISSION_LABELS,
  ROLE_OPTIONS,
  type CreateUserPayload,
  type OwnerProfile,
  type PermissionItem,
} from "@/lib/api";
import { getAccessToken } from "@/lib/auth-storage";

type UserFormProps = {
  initialValues?: Partial<CreateUserPayload>;
  submitLabel: string;
  onSubmit: (payload: CreateUserPayload) => Promise<void>;
};

export function UserForm({ initialValues, submitLabel, onSubmit }: UserFormProps) {
  const [form, setForm] = useState<CreateUserPayload>({
    email: initialValues?.email ?? "",
    password: initialValues?.password ?? "",
    first_name: initialValues?.first_name ?? "",
    last_name: initialValues?.last_name ?? "",
    phone: initialValues?.phone ?? "",
    role_code: initialValues?.role_code ?? "gestionnaire",
    is_active: initialValues?.is_active ?? true,
    permissions: initialValues?.permissions ?? [],
    owner_profile_id: initialValues?.owner_profile_id,
  });
  const [autoPassword, setAutoPassword] = useState(!initialValues?.password);
  const [ownerProfiles, setOwnerProfiles] = useState<OwnerProfile[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const token = getAccessToken();
    if (!token) return;
    fetchOwnerProfiles(token)
      .then((data) => setOwnerProfiles(data.items.filter((item) => !item.user_id)))
      .catch(() => setOwnerProfiles([]));
  }, []);

  const togglePermission = (code: string) => {
    setForm((current) => {
      const existing = current.permissions ?? [];
      const found = existing.find((item) => item.permission_code === code);
      if (found) {
        return {
          ...current,
          permissions: existing.map((item) =>
            item.permission_code === code
              ? { ...item, granted: !item.granted }
              : item,
          ),
        };
      }
      return {
        ...current,
        permissions: [...existing, { permission_code: code, granted: true }],
      };
    });
  };

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const payload: CreateUserPayload = {
        ...form,
        password: autoPassword ? undefined : form.password,
      };
      await onSubmit(payload);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Enregistrement impossible");
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6 rounded-xl border border-zinc-200 bg-white p-6">
      <div className="grid gap-4 sm:grid-cols-2">
        <div>
          <label className="text-sm font-medium">Prénom</label>
          <Input
            value={form.first_name}
            onChange={(event) =>
              setForm((current) => ({ ...current, first_name: event.target.value }))
            }
            required
          />
        </div>
        <div>
          <label className="text-sm font-medium">Nom</label>
          <Input
            value={form.last_name}
            onChange={(event) =>
              setForm((current) => ({ ...current, last_name: event.target.value }))
            }
            required
          />
        </div>
        <div>
          <label className="text-sm font-medium">Email</label>
          <Input
            type="email"
            value={form.email}
            onChange={(event) =>
              setForm((current) => ({ ...current, email: event.target.value }))
            }
            required
          />
        </div>
        <div>
          <label className="text-sm font-medium">Téléphone</label>
          <Input
            value={form.phone ?? ""}
            onChange={(event) =>
              setForm((current) => ({ ...current, phone: event.target.value }))
            }
          />
        </div>
        <div>
          <label className="text-sm font-medium">Rôle</label>
          <select
            className="mt-1 h-10 w-full rounded-md border border-zinc-200 bg-white px-3 text-sm"
            value={form.role_code}
            onChange={(event) =>
              setForm((current) => ({ ...current, role_code: event.target.value }))
            }
          >
            {ROLE_OPTIONS.map((option) => (
              <option key={option.code} value={option.code}>
                {option.label}
              </option>
            ))}
          </select>
        </div>
        <div className="flex items-end">
          <label className="flex items-center gap-2 text-sm">
            <input
              type="checkbox"
              checked={form.is_active}
              onChange={(event) =>
                setForm((current) => ({ ...current, is_active: event.target.checked }))
              }
            />
            Compte actif
          </label>
        </div>
      </div>

      {!initialValues && (
        <div className="space-y-3">
          <label className="flex items-center gap-2 text-sm">
            <input
              type="checkbox"
              checked={autoPassword}
              onChange={(event) => setAutoPassword(event.target.checked)}
            />
            Générer un mot de passe automatiquement
          </label>
          {!autoPassword && (
            <Input
              type="password"
              placeholder="Mot de passe"
              value={form.password ?? ""}
              onChange={(event) =>
                setForm((current) => ({ ...current, password: event.target.value }))
              }
            />
          )}
        </div>
      )}

      {form.role_code === "proprietaire" && (
        <div>
          <label className="text-sm font-medium">Profil propriétaire</label>
          <select
            className="mt-1 h-10 w-full rounded-md border border-zinc-200 bg-white px-3 text-sm"
            value={form.owner_profile_id ?? ""}
            onChange={(event) =>
              setForm((current) => ({
                ...current,
                owner_profile_id: event.target.value || undefined,
              }))
            }
            required
          >
            <option value="">Sélectionner un profil</option>
            {ownerProfiles.map((profile) => (
              <option key={profile.id} value={profile.id}>
                {profile.first_name} {profile.last_name}
              </option>
            ))}
          </select>
        </div>
      )}

      {form.role_code === "admin_familial" && (
        <div className="space-y-3">
          <p className="text-sm font-medium">Permissions</p>
          <div className="grid gap-2 sm:grid-cols-2">
            {Object.entries(PERMISSION_LABELS).map(([code, label]) => {
              const granted = (form.permissions ?? []).some(
                (item) => item.permission_code === code && item.granted,
              );
              return (
                <label key={code} className="flex items-center gap-2 text-sm">
                  <input
                    type="checkbox"
                    checked={granted}
                    onChange={() => togglePermission(code)}
                  />
                  {label}
                </label>
              );
            })}
          </div>
        </div>
      )}

      {error && (
        <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          {error}
        </div>
      )}

      <Button type="submit" disabled={loading}>
        {loading ? "Enregistrement..." : submitLabel}
      </Button>
    </form>
  );
}

export function CreateUserForm() {
  const router = useRouter();

  return (
    <UserForm
      submitLabel="Créer l'utilisateur"
      onSubmit={async (payload) => {
        const token = getAccessToken();
        if (!token) return;
        const user = await createUser(token, payload);
        router.push(`/dashboard/utilisateurs/${user.id}`);
      }}
    />
  );
}
