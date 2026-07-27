"use client";

import Link from "next/link";

import { RoleBadge } from "@/components/auth/role-badge";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/contexts/auth-context";

export function AppHeader() {
  const { user, logout } = useAuth();

  if (!user) return null;

  return (
    <header className="border-b border-zinc-200 bg-white">
      <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
        <div>
          <p className="text-sm text-zinc-500">Connecté en tant que</p>
          <p className="font-medium">
            {user.first_name} {user.last_name}
          </p>
        </div>
        <div className="flex items-center gap-3">
          <RoleBadge code={user.role.code} label={user.role.label} />
          <Button asChild variant="outline">
            <Link href="/profil">Profil</Link>
          </Button>
          <Button variant="outline" onClick={() => logout()}>
            Déconnexion
          </Button>
        </div>
      </div>
    </header>
  );
}
