"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import { RoleBadge } from "@/components/auth/role-badge";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/contexts/auth-context";
import { cn } from "@/lib/utils";

const NAV_ITEMS = [
  { href: "/dashboard", label: "Tableau de bord", roles: ["all"] },
  {
    href: "/dashboard/immeubles",
    label: "Immeubles",
    roles: ["super_admin", "admin_familial", "proprietaire", "gestionnaire"],
  },
  {
    href: "/dashboard/logements",
    label: "Logements",
    roles: ["super_admin", "admin_familial", "proprietaire", "gestionnaire"],
  },
  {
    href: "/dashboard/locataires",
    label: "Locataires",
    roles: ["super_admin", "admin_familial", "gestionnaire", "proprietaire"],
  },
  {
    href: "/dashboard/baux",
    label: "Baux",
    roles: ["super_admin", "admin_familial", "gestionnaire", "proprietaire"],
  },
  {
    href: "/dashboard/paiements",
    label: "Paiements",
    roles: ["super_admin", "admin_familial", "gestionnaire", "proprietaire", "locataire"],
  },
  {
    href: "/dashboard/impayes",
    label: "Impayés",
    roles: ["super_admin", "admin_familial", "gestionnaire", "proprietaire"],
  },
  {
    href: "/dashboard/relances",
    label: "Relances",
    roles: ["super_admin", "admin_familial", "gestionnaire"],
  },
  {
    href: "/dashboard/depenses",
    label: "Dépenses",
    roles: ["super_admin", "admin_familial", "gestionnaire", "proprietaire"],
  },
  {
    href: "/dashboard/reparations",
    label: "Réparations",
    roles: ["super_admin", "admin_familial", "gestionnaire", "proprietaire", "locataire"],
  },
  {
    href: "/dashboard/recus",
    label: "Reçus",
    roles: ["super_admin", "admin_familial", "gestionnaire", "locataire"],
  },
  {
    href: "/dashboard/utilisateurs",
    label: "Utilisateurs",
    roles: ["super_admin"],
  },
  {
    href: "/dashboard/proprietaires",
    label: "Propriétaires",
    roles: ["super_admin", "admin_familial"],
  },
];

export function AppHeader() {
  const pathname = usePathname();
  const { user, logout } = useAuth();

  if (!user) return null;

  const links = NAV_ITEMS.filter(
    (item) =>
      item.roles.includes("all") || item.roles.includes(user.role.code),
  );

  return (
    <header className="border-b border-zinc-200 bg-white">
      <div className="mx-auto flex max-w-6xl flex-col gap-4 px-6 py-4 lg:flex-row lg:items-center lg:justify-between">
        <div>
          <p className="text-sm text-zinc-500">Connecté en tant que</p>
          <p className="font-medium">
            {user.first_name} {user.last_name}
          </p>
        </div>

        <nav className="flex flex-wrap gap-2">
          {links.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "rounded-md px-3 py-2 text-sm font-medium transition-colors",
                pathname === item.href || pathname.startsWith(`${item.href}/`)
                  ? "bg-zinc-900 text-white"
                  : "bg-zinc-100 text-zinc-700 hover:bg-zinc-200",
              )}
            >
              {item.label}
            </Link>
          ))}
        </nav>

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
