"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";

import { SuperAdminRoute } from "@/components/auth/super-admin-route";
import { RoleBadge } from "@/components/auth/role-badge";
import { PasswordReveal } from "@/components/users/password-reveal";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  ApiError,
  deleteUser,
  fetchUsers,
  ROLE_OPTIONS,
  type UserSummary,
} from "@/lib/api";
import { getAccessToken } from "@/lib/auth-storage";
import { useConfirm } from "@/contexts/confirm-context";
import { dangerConfirm } from "@/lib/confirm-presets";

function UserStatus({ isActive }: { isActive: boolean }) {
  return (
    <span className={isActive ? "text-emerald-700" : "text-red-700"}>
      {isActive ? "Actif" : "Inactif"}
    </span>
  );
}

export default function UsersPage() {
  const confirm = useConfirm();
  const [users, setUsers] = useState<UserSummary[]>([]);
  const [search, setSearch] = useState("");
  const [role, setRole] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const loadUsers = useCallback(async () => {
    const token = getAccessToken();
    if (!token) return;
    setLoading(true);
    setError(null);
    try {
      const data = await fetchUsers(token, {
        search: search || undefined,
        role: role || undefined,
      });
      setUsers(data.items);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Chargement impossible");
    } finally {
      setLoading(false);
    }
  }, [search, role]);

  useEffect(() => {
    loadUsers();
  }, [loadUsers]);

  const handleDelete = async (user: UserSummary) => {
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
      const token = getAccessToken();
      if (!token) return;
      await deleteUser(token, user.id);
      await loadUsers();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Suppression impossible");
    }
  };

  const emptyState = loading ? (
    <p className="py-8 text-center text-muted-foreground">Chargement...</p>
  ) : (
    <p className="py-8 text-center text-muted-foreground">Aucun utilisateur trouvé</p>
  );

  return (
    <SuperAdminRoute>
      <div className="flex min-w-0 flex-col gap-6">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div className="min-w-0">
            <h1 className="text-2xl font-bold sm:text-3xl">Utilisateurs</h1>
            <p className="mt-2 text-sm text-muted-foreground sm:text-base">
              Gérez les comptes et les rôles de la plateforme.
            </p>
          </div>
          <Button asChild className="w-full shrink-0 sm:w-auto">
            <Link href="/dashboard/utilisateurs/nouveau">Nouvel utilisateur</Link>
          </Button>
        </div>

        <div className="flex flex-col gap-3 sm:flex-row">
          <Input
            className="w-full min-w-0"
            placeholder="Rechercher par nom ou email"
            value={search}
            onChange={(event) => setSearch(event.target.value)}
          />
          <select
            className="h-10 w-full min-w-0 rounded-md border border-border bg-card px-3 text-sm sm:max-w-xs"
            value={role}
            onChange={(event) => setRole(event.target.value)}
          >
            <option value="">Tous les rôles</option>
            {ROLE_OPTIONS.map((option) => (
              <option key={option.code} value={option.code}>
                {option.label}
              </option>
            ))}
          </select>
        </div>

        {error && (
          <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
            {error}
          </div>
        )}

        {/* Mobile : cartes */}
        <div className="flex flex-col gap-3 md:hidden">
          {!loading && users.length === 0
            ? emptyState
            : users.map((user) => (
                <article
                  key={user.id}
                  className="rounded-xl border border-border bg-card p-4 shadow-sm"
                >
                  <div className="flex flex-col gap-3">
                    <div className="flex flex-wrap items-start justify-between gap-2">
                      <div className="min-w-0 flex-1">
                        <p className="font-semibold">
                          {user.first_name} {user.last_name}
                        </p>
                        <p className="mt-1 break-all text-sm text-muted-foreground">
                          {user.email}
                        </p>
                      </div>
                      <RoleBadge code={user.role.code} label={user.role.label} />
                    </div>

                    <div>
                      <p className="mb-1 text-xs font-medium uppercase tracking-wide text-muted-foreground">
                        Mot de passe
                      </p>
                      <PasswordReveal
                        password={user.password}
                        defaultVisible={Boolean(user.password)}
                        emptyLabel="Réinitialiser ou définir"
                      />
                    </div>

                    <div className="flex flex-wrap items-center justify-between gap-3 border-t border-border pt-3">
                      <UserStatus isActive={user.is_active} />
                      <div className="flex w-full flex-col gap-2 sm:w-auto sm:flex-row sm:justify-end">
                        <Button asChild variant="outline" size="sm" className="w-full sm:w-auto">
                          <Link href={`/dashboard/utilisateurs/${user.id}`}>Voir</Link>
                        </Button>
                        <Button
                          variant="destructive"
                          size="sm"
                          className="w-full sm:w-auto"
                          onClick={() => handleDelete(user)}
                        >
                          Supprimer
                        </Button>
                      </div>
                    </div>
                  </div>
                </article>
              ))}
          {loading && users.length === 0 && emptyState}
        </div>

        {/* Desktop : tableau */}
        <div className="hidden overflow-x-auto rounded-xl border border-border bg-card shadow-sm md:block">
          <table className="min-w-[56rem] w-full divide-y divide-zinc-200 text-sm">
            <thead className="bg-muted/50">
              <tr>
                <th className="px-4 py-3 text-left font-medium">Nom</th>
                <th className="px-4 py-3 text-left font-medium">Email</th>
                <th className="px-4 py-3 text-left font-medium">Mot de passe</th>
                <th className="px-4 py-3 text-left font-medium">Rôle</th>
                <th className="px-4 py-3 text-left font-medium">Statut</th>
                <th className="px-4 py-3 text-right font-medium">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-zinc-200">
              {loading ? (
                <tr>
                  <td colSpan={6} className="px-4 py-8 text-center text-muted-foreground">
                    Chargement...
                  </td>
                </tr>
              ) : users.length === 0 ? (
                <tr>
                  <td colSpan={6} className="px-4 py-8 text-center text-muted-foreground">
                    Aucun utilisateur trouvé
                  </td>
                </tr>
              ) : (
                users.map((user) => (
                  <tr key={user.id}>
                    <td className="px-4 py-3 font-medium">
                      {user.first_name} {user.last_name}
                    </td>
                    <td className="max-w-[12rem] truncate px-4 py-3 text-muted-foreground">
                      {user.email}
                    </td>
                    <td className="px-4 py-3">
                      <PasswordReveal
                        password={user.password}
                        defaultVisible={Boolean(user.password)}
                        emptyLabel="Réinitialiser ou définir un mot de passe"
                      />
                    </td>
                    <td className="px-4 py-3">
                      <RoleBadge code={user.role.code} label={user.role.label} />
                    </td>
                    <td className="px-4 py-3">
                      <UserStatus isActive={user.is_active} />
                    </td>
                    <td className="px-4 py-3 text-right">
                      <div className="flex items-center justify-end gap-2">
                        <Button asChild variant="outline" size="sm">
                          <Link href={`/dashboard/utilisateurs/${user.id}`}>Voir</Link>
                        </Button>
                        <Button
                          variant="destructive"
                          size="sm"
                          onClick={() => handleDelete(user)}
                        >
                          Supprimer
                        </Button>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </SuperAdminRoute>
  );
}
