"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";

import { SuperAdminRoute } from "@/components/auth/super-admin-route";
import { AppHeader } from "@/components/layout/app-header";
import { Button } from "@/components/ui/button";
import {
  ApiError,
  fetchUserPermissions,
  PERMISSION_LABELS,
  updateUserPermissions,
  type PermissionItem,
} from "@/lib/api";
import { getAccessToken } from "@/lib/auth-storage";

export default function UserPermissionsPage() {
  const params = useParams<{ id: string }>();
  const [permissions, setPermissions] = useState<PermissionItem[]>([]);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const token = getAccessToken();
    if (!token || !params.id) return;
    fetchUserPermissions(token, params.id)
      .then(setPermissions)
      .catch((err) =>
        setError(err instanceof ApiError ? err.message : "Chargement impossible"),
      );
  }, [params.id]);

  const toggle = (code: string) => {
    setPermissions((current) =>
      current.map((item) =>
        item.permission_code === code
          ? { ...item, granted: !item.granted }
          : item,
      ),
    );
  };

  const handleSave = async () => {
    const token = getAccessToken();
    if (!token || !params.id) return;
    setError(null);
    try {
      const updated = await updateUserPermissions(
        token,
        params.id,
        permissions.filter((item) => item.granted),
      );
      setPermissions(updated);
      setMessage("Permissions mises à jour");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Sauvegarde impossible");
    }
  };

  return (
    <SuperAdminRoute>
      <AppHeader />
      <main className="mx-auto w-full max-w-3xl px-6 py-10">
        <div className="mb-6 flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold">Permissions</h1>
            <p className="mt-2 text-muted-foreground">
              Définissez les autorisations de l&apos;administrateur familial.
            </p>
          </div>
          <Button asChild variant="outline">
            <Link href={`/dashboard/utilisateurs/${params.id}`}>Retour</Link>
          </Button>
        </div>

        <div className="space-y-4 rounded-xl border border-border bg-card shadow-sm p-6">
          {permissions.map((item) => (
            <label
              key={item.permission_code}
              className="flex items-center gap-3 text-sm"
            >
              <input
                type="checkbox"
                checked={item.granted}
                onChange={() => toggle(item.permission_code)}
              />
              {PERMISSION_LABELS[item.permission_code] ?? item.permission_code}
            </label>
          ))}

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

          <Button onClick={handleSave}>Enregistrer</Button>
        </div>
      </main>
    </SuperAdminRoute>
  );
}
