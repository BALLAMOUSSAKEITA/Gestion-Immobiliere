"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import { RoleBadge } from "@/components/auth/role-badge";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/contexts/auth-context";
import { cn } from "@/lib/utils";

const NAV_ITEMS = [
  { href: "/espace-locataire", label: "Tableau de bord" },
  { href: "/espace-locataire/mon-logement", label: "Mon logement" },
  { href: "/espace-locataire/mon-contrat", label: "Mon contrat" },
  { href: "/espace-locataire/paiements", label: "Paiements" },
  { href: "/espace-locataire/recus", label: "Reçus" },
  { href: "/espace-locataire/impayes", label: "Impayés" },
  { href: "/espace-locataire/reparations", label: "Réparations" },
  { href: "/espace-locataire/documents", label: "Documents" },
  { href: "/espace-locataire/messages", label: "Messages" },
];

export function TenantSidebar() {
  const pathname = usePathname();
  const { user, logout } = useAuth();

  if (!user) return null;

  return (
    <aside className="border-b border-zinc-200 bg-white lg:border-b-0 lg:border-r lg:min-w-56">
      <div className="flex flex-col gap-4 p-4">
        <div>
          <p className="text-sm text-zinc-500">Espace locataire</p>
          <p className="font-medium">
            {user.first_name} {user.last_name}
          </p>
          <RoleBadge code={user.role.code} label={user.role.label} />
        </div>

        <nav className="flex flex-col gap-1">
          {NAV_ITEMS.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "rounded-md px-3 py-2 text-sm font-medium transition-colors",
                pathname === item.href || pathname.startsWith(`${item.href}/`)
                  ? "bg-zinc-900 text-white"
                  : "text-zinc-700 hover:bg-zinc-100",
              )}
            >
              {item.label}
            </Link>
          ))}
        </nav>

        <div className="flex flex-col gap-2 pt-2">
          <Button asChild variant="outline">
            <Link href="/profil">Profil</Link>
          </Button>
          <Button variant="outline" onClick={() => logout()}>
            Déconnexion
          </Button>
        </div>
      </div>
    </aside>
  );
}
