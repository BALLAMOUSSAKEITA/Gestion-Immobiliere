"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Building2, Home, LogOut, User } from "lucide-react";

import { RoleBadge } from "@/components/auth/role-badge";
import { NotificationBell } from "@/components/notifications/notification-bell";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/contexts/auth-context";
import { TENANT_NAV } from "@/lib/navigation";
import { cn } from "@/lib/utils";

export function TenantSidebar() {
  const pathname = usePathname();
  const { user, logout } = useAuth();

  if (!user) return null;

  return (
    <aside className="w-full border-b border-border bg-sidebar text-sidebar-foreground lg:w-64 lg:min-h-screen lg:border-b-0 lg:border-r">
      <div className="flex h-full flex-col p-4">
        <div className="mb-6 flex items-center gap-3 rounded-xl bg-sidebar-accent/60 p-4">
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-accent text-accent-foreground">
            <Home className="h-5 w-5" />
          </div>
          <div>
            <p className="text-xs text-sidebar-foreground/70">Espace locataire</p>
            <p className="font-semibold text-white">{user.first_name} {user.last_name}</p>
          </div>
        </div>

        <div className="mb-4 flex items-center justify-between">
          <RoleBadge code={user.role.code} label={user.role.label} />
          <NotificationBell notificationsPath="/espace-locataire/notifications" />
        </div>

        <nav className="flex flex-1 flex-col gap-1 overflow-x-auto lg:overflow-visible">
          {TENANT_NAV.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "whitespace-nowrap rounded-lg px-3 py-2.5 text-sm font-medium transition-colors lg:whitespace-normal",
                pathname === item.href || pathname.startsWith(`${item.href}/`)
                  ? "bg-sidebar-active text-white"
                  : "text-sidebar-foreground/80 hover:bg-sidebar-accent hover:text-white",
              )}
            >
              {item.label}
            </Link>
          ))}
        </nav>

        <div className="mt-6 flex flex-col gap-2 border-t border-white/10 pt-4">
          <Button asChild variant="ghost" className="justify-start text-sidebar-foreground hover:bg-sidebar-accent hover:text-white">
            <Link href="/profil">
              <User className="mr-2 h-4 w-4" />
              Profil
            </Link>
          </Button>
          <Button
            variant="ghost"
            className="justify-start text-sidebar-foreground hover:bg-sidebar-accent hover:text-white"
            onClick={() => logout()}
          >
            <LogOut className="mr-2 h-4 w-4" />
            Déconnexion
          </Button>
        </div>
      </div>
    </aside>
  );
}

export function TenantShell({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen bg-background">
      <div className="mx-auto flex max-w-7xl flex-col lg:flex-row">
        <TenantSidebar />
        <main className="flex-1 page-container">{children}</main>
      </div>
    </div>
  );
}
