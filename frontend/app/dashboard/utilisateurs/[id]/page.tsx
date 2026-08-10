"use client";

import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { SuperAdminRoute } from "@/components/auth/super-admin-route";
import { RoleBadge } from "@/components/auth/role-badge";
import { UserForm } from "@/components/users/user-form";
import { Button } from "@/components/ui/button";
import {
  ApiError,
  deleteUser,
  fetchUser,
  resetUserPassword,
  updateUser,
  type UserDetail,
} from "@/lib/api";
import { getAccessToken } from "@/lib/auth-storage";
import { useConfirm } from "@/contexts/confirm-context";
import { dangerConfirm, modifyConfirm } from "@/lib/confirm-presets";

export default function UserDetailPage() {
  const params = useParams<{ id: string }>();
  const router = useRouter();
  const confirm = useConfirm();
  const [user, setUser] = useState<UserDetail | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const token = getAccessToken();
    if (!token || !params.id) return;
    fetchUser(token, params.id)
      .then(setUser)
      .catch((err) =>
        setError(err instanceof ApiError ? err.message : "Chargement impossible"),
      );
  }, [params.id]);

  const handleDelete = async () => {
    const token = getAccessToken();
    if (!token || !user) return;
    if (
      !(await confirm(
        dangerConfirm(
          "Supprimer l'utilisateur",
          `Cette action supprime définitivement le compte de ${user.first_name} ${user.last_name}. Cette opération est irréversible.`,
          "Supprimer définitivement",
        ),
      ))
    ) {
      return;
    }
    setError(null);
    try {
      await deleteUser(token, user.id);
      router.push("/dashboard/utilisateurs");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Suppression impossible");
    }
  };

  const handleResetPassword = async () => {
    const token = getAccessToken();
    if (!token || !user) return;
    if (
      !(await confirm(
        modifyConfirm(
          `Réinitialiser le mot de passe de ${user.first_name} ${user.last_name} ?`,
          "Réinitialiser",
        ),
      ))
    ) {
      return;
    }
    const result = await resetUserPassword(token, user.id);
    setMessage(`Mot de passe temporaire : ${result.temporary_password}`);
  };

  if (!user) {
    return (
      <SuperAdminRoute>
        <div className="py-16 text-center text-muted-foreground">
          {error ?? "Chargement..."}
        </div>
      </SuperAdminRoute>
    );
  }

  return (
    <SuperAdminRoute>
      <div className="flex flex-col gap-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold">
              {user.first_name} {user.last_name}
            </h1>
            <div className="mt-2">
              <RoleBadge code={user.role.code} label={user.role.label} />
            </div>
          </div>
          <Button asChild variant="outline">
            <Link href="/dashboard/utilisateurs">Retour</Link>
          </Button>
        </div>

        {message && (
          <div className="rounded-lg border border-emerald-200 bg-emerald-50 px-4 py-3 text-emerald-800">
            {message}
          </div>
        )}

        <UserForm
          submitLabel="Enregistrer les modifications"
          initialValues={{
            email: user.email,
            first_name: user.first_name,
            last_name: user.last_name,
            phone: user.phone ?? "",
            role_code: user.role.code,
            is_active: user.is_active,
            permissions: user.permissions,
            owner_profile_id: user.owner_profile_id ?? undefined,
          }}
          onSubmit={async (payload) => {
            const token = getAccessToken();
            if (!token) return;
            if (
              !(await confirm(
                modifyConfirm("Enregistrer les modifications de cet utilisateur ?"),
              ))
            ) {
              return;
            }
            const updated = await updateUser(token, user.id, payload);
            setUser(updated);
            setMessage("Utilisateur mis à jour");
          }}
        />

        <div className="flex flex-wrap gap-3">
          {user.role.code === "admin_familial" && (
            <Button asChild variant="outline">
              <Link href={`/dashboard/utilisateurs/${user.id}/permissions`}>
                Gérer les permissions
              </Link>
            </Button>
          )}
          <Button variant="outline" onClick={handleResetPassword}>
            Réinitialiser le mot de passe
          </Button>
          <Button variant="destructive" onClick={handleDelete}>
            Supprimer
          </Button>
        </div>
      </div>
    </SuperAdminRoute>
  );
}
