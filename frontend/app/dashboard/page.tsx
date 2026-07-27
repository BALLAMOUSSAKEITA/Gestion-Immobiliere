"use client";

import { RoleBadge } from "@/components/auth/role-badge";
import { useAuth } from "@/contexts/auth-context";

export default function DashboardPage() {
  const { user } = useAuth();

  if (!user) return null;

  return (
    <main className="mx-auto flex w-full max-w-6xl flex-col gap-6 px-6 py-10">
      <div>
        <h1 className="text-3xl font-bold">Tableau de bord</h1>
        <p className="mt-2 text-zinc-600">
          Bienvenue, {user.first_name}. Votre espace est prêt.
        </p>
      </div>

      <div className="rounded-xl border border-zinc-200 bg-white p-6 shadow-sm">
        <p className="text-sm text-zinc-500">Rôle actuel</p>
        <div className="mt-3">
          <RoleBadge code={user.role.code} label={user.role.label} />
        </div>
        <p className="mt-4 text-sm text-zinc-600">
          Les modules métier seront ajoutés dans les prochains sprints.
        </p>
        {user.role.code === "super_admin" && (
          <div className="mt-6 flex flex-wrap gap-3">
            <a
              href="/dashboard/utilisateurs"
              className="rounded-md bg-zinc-900 px-4 py-2 text-sm font-medium text-white"
            >
              Gérer les utilisateurs
            </a>
            <a
              href="/dashboard/proprietaires"
              className="rounded-md border border-zinc-200 px-4 py-2 text-sm font-medium"
            >
              Voir les propriétaires
            </a>
          </div>
        )}
      </div>
    </main>
  );
}
