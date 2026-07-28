"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";
import { Home, LogOut, Menu, User, X } from "lucide-react";

import { RoleBadge } from "@/components/auth/role-badge";
import { NotificationBell } from "@/components/notifications/notification-bell";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/contexts/auth-context";
import { getNavIcon } from "@/lib/nav-icons";
import { TENANT_NAV } from "@/lib/navigation";
import { cn } from "@/lib/utils";

function SidebarContent({ onNavigate }: { onNavigate?: () => void }) {
  const pathname = usePathname();
  const { user, logout } = useAuth();

  if (!user) return null;

  return (
    <div className="flex h-full flex-col p-4">
      <div className="mb-6 flex items-center gap-3 rounded-xl bg-sidebar-accent/60 p-4">
        <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-accent text-accent-foreground">
          <Home className="h-5 w-5" />
        </div>
        <div className="min-w-0">
          <p className="text-xs text-sidebar-foreground/70">Espace locataire</p>
          <p className="truncate font-semibold text-white">{user.first_name} {user.last_name}</p>
        </div>
      </div>

      <div className="mb-4 flex items-center justify-between gap-2">
        <RoleBadge code={user.role.code} label={user.role.label} />
        <div className="lg:hidden">
          <NotificationBell notificationsPath="/espace-locataire/notifications" />
        </div>
      </div>

      <nav className="flex-1 space-y-1 overflow-y-auto overscroll-contain">
        {TENANT_NAV.map((item) => {
          const Icon = getNavIcon(item.href);
          const active = pathname === item.href || pathname.startsWith(`${item.href}/`);
          return (
            <Link
              key={item.href}
              href={item.href}
              onClick={onNavigate}
              className={cn(
                "flex min-h-11 items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors",
                active
                  ? "bg-sidebar-active text-white"
                  : "text-sidebar-foreground/80 hover:bg-sidebar-accent hover:text-white",
              )}
            >
              <Icon className="h-4 w-4 shrink-0" />
              <span className="truncate">{item.label}</span>
            </Link>
          );
        })}
      </nav>

      <div className="mt-6 flex flex-col gap-2 border-t border-white/10 pt-4 safe-bottom">
        <Button asChild variant="ghost" className="min-h-11 justify-start text-sidebar-foreground hover:bg-sidebar-accent hover:text-white">
          <Link href="/profil">
            <User className="mr-2 h-4 w-4" />
            Profil
          </Link>
        </Button>
        <Button
          variant="ghost"
          className="min-h-11 justify-start text-sidebar-foreground hover:bg-sidebar-accent hover:text-white"
          onClick={() => logout()}
        >
          <LogOut className="mr-2 h-4 w-4" />
          Déconnexion
        </Button>
      </div>
    </div>
  );
}

export function TenantShell({ children }: { children: React.ReactNode }) {
  const [mobileOpen, setMobileOpen] = useState(false);

  return (
    <div className="min-h-screen bg-background lg:flex">
      {mobileOpen && (
        <button
          type="button"
          className="fixed inset-0 z-40 bg-black/50 lg:hidden"
          onClick={() => setMobileOpen(false)}
          aria-label="Fermer le menu"
        />
      )}

      <aside
        className={cn(
          "fixed inset-y-0 left-0 z-50 w-[min(85vw,16rem)] bg-sidebar text-sidebar-foreground transition-transform duration-300 lg:static lg:z-auto lg:w-64 lg:shrink-0 lg:translate-x-0 lg:border-r lg:border-border",
          mobileOpen ? "translate-x-0" : "-translate-x-full lg:translate-x-0",
        )}
      >
        <SidebarContent onNavigate={() => setMobileOpen(false)} />
      </aside>

      <div className="flex min-w-0 flex-1 flex-col">
        <header className="sticky top-0 z-30 flex items-center justify-between gap-3 border-b border-border bg-card/95 px-3 py-3 backdrop-blur-md safe-top lg:hidden">
          <button
            type="button"
            className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg border border-border"
            onClick={() => setMobileOpen(true)}
            aria-label="Ouvrir le menu"
          >
            <Menu className="h-5 w-5" />
          </button>
          <p className="truncate font-semibold">Espace locataire</p>
          <NotificationBell notificationsPath="/espace-locataire/notifications" />
        </header>

        <main className="page-container pb-safe">{children}</main>
      </div>

      {mobileOpen && (
        <button
          type="button"
          className="fixed right-4 top-4 z-[60] flex h-10 w-10 items-center justify-center rounded-full bg-card shadow-lg safe-top lg:hidden"
          onClick={() => setMobileOpen(false)}
          aria-label="Fermer le menu"
        >
          <X className="h-5 w-5" />
        </button>
      )}
    </div>
  );
}

export { TenantShell as TenantSidebar };
