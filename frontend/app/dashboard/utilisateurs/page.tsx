"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";

import { SuperAdminRoute } from "@/components/auth/super-admin-route";
import { RoleBadge } from "@/components/auth/role-badge";
import { AppHeader } from "@/components/layout/app-header";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ApiError, fetchUsers, ROLE_OPTIONS, type UserSummary } from "@/lib/api";
import { getAccessToken } from "@/lib/auth-storage";

export default function UsersPage() {
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

  return (
    <SuperAdminRoute>
      <AppHeader />
      <main className="mx-auto flex w-full max-w-6xl flex-col gap-6 px-6 py-10">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h1 className="text-3xl font-bold">Utilisateurs</h1>
            <p className="mt-2 text-zinc-600">
              Gérez les comptes et les rôles de la plateforme.
            </p>
          </div>
          <Button asChild>
            <Link href="/dashboard/utilisateurs/nouveau">Nouvel utilisateur</Link>
          </Button>
        </div>

        <div className="flex flex-col gap-3 sm:flex-row">
          <Input
            placeholder="Rechercher par nom ou email"
            value={search}
            onChange={(event) => setSearch(event.target.value)}
          />
          <select
            className="h-10 rounded-md border border-zinc-200 bg-white px-3 text-sm"
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
          <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-red-700">
            {error}
          </div>
        )}

        <div className="overflow-hidden rounded-xl border border-zinc-200 bg-white">
          <table className="min-w-full divide-y divide-zinc-200">
            <thead className="bg-zinc-50">
              <tr>
                <th className="px-4 py-3 text-left text-sm font-medium">Nom</th>
                <th className="px-4 py-3 text-left text-sm font-medium">Email</th>
                <th className="px-4 py-3 text-left text-sm font-medium">Rôle</th>
                <th className="px-4 py-3 text-left text-sm font-medium">Statut</th>
                <th className="px-4 py-3 text-right text-sm font-medium">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-zinc-200">
              {loading ? (
                <tr>
                  <td colSpan={5} className="px-4 py-8 text-center text-zinc-500">
                    Chargement...
                  </td>
                </tr>
              ) : users.length === 0 ? (
                <tr>
                  <td colSpan={5} className="px-4 py-8 text-center text-zinc-500">
                    Aucun utilisateur trouvé
                  </td>
                </tr>
              ) : (
                users.map((user) => (
                  <tr key={user.id}>
                    <td className="px-4 py-3 font-medium">
                      {user.first_name} {user.last_name}
                    </td>
                    <td className="px-4 py-3 text-zinc-600">{user.email}</td>
                    <td className="px-4 py-3">
                      <RoleBadge code={user.role.code} label={user.role.label} />
                    </td>
                    <td className="px-4 py-3">
                      <span
                        className={
                          user.is_active
                            ? "text-emerald-700"
                            : "text-red-700"
                        }
                      >
                        {user.is_active ? "Actif" : "Inactif"}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-right">
                      <Button asChild variant="outline" size="default">
                        <Link href={`/dashboard/utilisateurs/${user.id}`}>
                          Voir
                        </Link>
                      </Button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </main>
    </SuperAdminRoute>
  );
}
