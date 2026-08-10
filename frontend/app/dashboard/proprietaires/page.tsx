"use client";

import { useEffect, useState } from "react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  ApiError,
  createOwnerProfile,
  deleteOwnerProfile,
  fetchOwnerProfiles,
  type OwnerProfile,
} from "@/lib/api";
import { getAccessToken } from "@/lib/auth-storage";
import { useAuth } from "@/contexts/auth-context";
import { useConfirm } from "@/contexts/confirm-context";
import { deleteConfirm } from "@/lib/confirm-presets";

export default function OwnerProfilesPage() {
  const { user } = useAuth();
  const confirm = useConfirm();
  const [profiles, setProfiles] = useState<OwnerProfile[]>([]);
  const [form, setForm] = useState({
    first_name: "",
    last_name: "",
    phone: "",
    email: "",
    notes: "",
  });
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const loadProfiles = async () => {
    const token = getAccessToken();
    if (!token) return;
    const data = await fetchOwnerProfiles(token);
    setProfiles(data.items);
  };

  useEffect(() => {
    loadProfiles().catch((err) =>
      setError(err instanceof ApiError ? err.message : "Chargement impossible"),
    );
  }, []);

  const canManage = user?.role.code === "super_admin";

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    const token = getAccessToken();
    if (!token) return;
    setError(null);
    try {
      await createOwnerProfile(token, form);
      setForm({ first_name: "", last_name: "", phone: "", email: "", notes: "" });
      setMessage("Profil propriétaire créé");
      await loadProfiles();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Création impossible");
    }
  };

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-3xl font-bold">Propriétaires famille</h1>
        <p className="mt-2 text-muted-foreground">
          Membres de la famille propriétaires de biens.
        </p>
      </div>

      {canManage && (
        <form
          onSubmit={handleSubmit}
          className="grid gap-4 rounded-xl border border-border bg-card shadow-sm p-6 sm:grid-cols-2"
        >
          <Input
            placeholder="Prénom"
            value={form.first_name}
            onChange={(event) =>
              setForm((current) => ({ ...current, first_name: event.target.value }))
            }
            required
          />
          <Input
            placeholder="Nom"
            value={form.last_name}
            onChange={(event) =>
              setForm((current) => ({ ...current, last_name: event.target.value }))
            }
            required
          />
          <Input
            placeholder="Téléphone"
            value={form.phone}
            onChange={(event) =>
              setForm((current) => ({ ...current, phone: event.target.value }))
            }
          />
          <Input
            placeholder="Email"
            value={form.email}
            onChange={(event) =>
              setForm((current) => ({ ...current, email: event.target.value }))
            }
          />
          <Input
            className="sm:col-span-2"
            placeholder="Notes"
            value={form.notes}
            onChange={(event) =>
              setForm((current) => ({ ...current, notes: event.target.value }))
            }
          />
          <div className="sm:col-span-2">
            <Button type="submit">Ajouter un propriétaire</Button>
          </div>
        </form>
      )}

      {message && (
        <div className="rounded-lg border border-emerald-200 bg-emerald-50 px-4 py-3 text-emerald-800">
          {message}
        </div>
      )}
      {error && (
        <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-red-700">
          {error}
        </div>
      )}

      <div className="overflow-hidden rounded-xl border border-border bg-card shadow-sm">
        <table className="min-w-full divide-y divide-zinc-200">
          <thead className="bg-muted/50">
            <tr>
              <th className="px-4 py-3 text-left text-sm font-medium">Nom</th>
              <th className="px-4 py-3 text-left text-sm font-medium">Contact</th>
              <th className="px-4 py-3 text-left text-sm font-medium">Compte lié</th>
              {canManage && (
                <th className="px-4 py-3 text-right text-sm font-medium">Actions</th>
              )}
            </tr>
          </thead>
          <tbody className="divide-y divide-zinc-200">
            {profiles.map((profile) => (
              <tr key={profile.id}>
                <td className="px-4 py-3 font-medium">
                  {profile.first_name} {profile.last_name}
                </td>
                <td className="px-4 py-3 text-muted-foreground">
                  {profile.phone ?? "—"} · {profile.email ?? "—"}
                </td>
                <td className="px-4 py-3">{profile.user_id ? "Oui" : "Non"}</td>
                {canManage && (
                  <td className="px-4 py-3 text-right">
                    <Button
                      variant="destructive"
                      size="sm"
                      onClick={async () => {
                        if (
                          !(await confirm(
                            deleteConfirm(
                              `le propriétaire « ${profile.first_name} ${profile.last_name} »`,
                            ),
                          ))
                        ) {
                          return;
                        }
                        const token = getAccessToken();
                        if (!token) return;
                        setError(null);
                        setMessage(null);
                        try {
                          await deleteOwnerProfile(token, profile.id);
                          setMessage("Propriétaire supprimé");
                          await loadProfiles();
                        } catch (err) {
                          setError(
                            err instanceof ApiError
                              ? err.message
                              : "Suppression impossible",
                          );
                        }
                      }}
                    >
                      Supprimer
                    </Button>
                  </td>
                )}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
