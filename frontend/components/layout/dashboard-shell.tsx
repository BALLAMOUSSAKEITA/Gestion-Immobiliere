"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";
import {
  Building2,
  ChevronLeft,
  ChevronRight,
  LogOut,
  Menu,
  User,
  X,
} from "lucide-react";

import { RoleBadge } from "@/components/auth/role-badge";
import { NotificationBell } from "@/components/notifications/notification-bell";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/contexts/auth-context";
import { getNavIcon } from "@/lib/nav-icons";
import { filterDashboardNav } from "@/lib/navigation";
import { cn } from "@/lib/utils";

export function DashboardShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const { user, logout } = useAuth();
  const [mobileOpen, setMobileOpen] = useState(false);
  const [collapsed, setCollapsed] = useState(false);

  if (!user) return null;

  const navGroups = filterDashboardNav(user.role.code);

  const sidebarContent = (
    <div className="flex h-full flex-col">
      <div className={cn("flex items-center gap-3 border-b border-white/10 px-4 py-4 safe-top", collapsed && "justify-center px-2")}>
        <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-accent text-accent-foreground">
          <Building2 className="h-5 w-5" />
        </div>
        {!collapsed && (
          <div className="min-w-0">
            <p className="truncate text-sm font-semibold text-white">Gestion Immo</p>
            <p className="text-xs text-sidebar-foreground/70">Tableau de bord</p>
          </div>
        )}
      </div>

      <nav className="flex-1 overflow-y-auto overscroll-contain px-3 py-4">
        {navGroups.map((group) => (
          <div key={group.title} className="mb-5">
            {!collapsed && (
              <p className="mb-2 px-3 text-[11px] font-semibold uppercase tracking-wider text-sidebar-foreground/50">
                {group.title}
              </p>
            )}
            <div className="space-y-1">
              {group.items.map((item) => {
                const Icon = getNavIcon(item.href);
                const active =
                  pathname === item.href ||
                  (item.href !== "/dashboard" && pathname.startsWith(`${item.href}/`));
                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    onClick={() => setMobileOpen(false)}
                    className={cn(
                      "flex min-h-11 items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors",
                      active
                        ? "bg-sidebar-active text-white shadow-sm"
                        : "text-sidebar-foreground/80 hover:bg-sidebar-accent hover:text-white",
                      collapsed && "justify-center px-2",
                    )}
                    title={collapsed ? item.label : undefined}
                  >
                    <Icon className="h-4 w-4 shrink-0" />
                    {!collapsed && <span className="truncate">{item.label}</span>}
                  </Link>
                );
              })}
            </div>
          </div>
        ))}
      </nav>

      <div className="border-t border-white/10 p-3 safe-bottom">
        {!collapsed && (
          <div className="mb-3 rounded-lg bg-sidebar-accent/60 px-3 py-3">
            <p className="truncate text-sm font-medium text-white">
              {user.first_name} {user.last_name}
            </p>
            <div className="mt-2">
              <RoleBadge code={user.role.code} label={user.role.label} />
            </div>
          </div>
        )}
        <div className={cn("flex flex-col gap-2", collapsed && "items-center")}>
          <Button asChild variant="ghost" size={collapsed ? "icon" : "default"} className="min-h-11 justify-start text-sidebar-foreground hover:bg-sidebar-accent hover:text-white">
            <Link href="/profil">
              <User className="h-4 w-4" />
              {!collapsed && "Profil"}
            </Link>
          </Button>
          <Button
            variant="ghost"
            size={collapsed ? "icon" : "default"}
            className="min-h-11 justify-start text-sidebar-foreground hover:bg-sidebar-accent hover:text-white"
            onClick={() => logout()}
          >
            <LogOut className="h-4 w-4" />
            {!collapsed && "Déconnexion"}
          </Button>
        </div>
      </div>
    </div>
  );

  return (
    <div className="min-h-screen bg-background">
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
          "fixed inset-y-0 left-0 z-50 bg-sidebar text-sidebar-foreground transition-all duration-300 lg:translate-x-0",
          collapsed ? "w-[72px]" : "w-[min(85vw,16rem)] lg:w-64",
          mobileOpen ? "translate-x-0" : "-translate-x-full lg:translate-x-0",
        )}
      >
        {sidebarContent}
        <button
          type="button"
          onClick={() => setCollapsed((v) => !v)}
          className="absolute -right-3 top-20 hidden h-6 w-6 items-center justify-center rounded-full border border-border bg-card text-muted-foreground shadow-sm lg:flex"
        >
          {collapsed ? <ChevronRight className="h-3 w-3" /> : <ChevronLeft className="h-3 w-3" />}
        </button>
      </aside>

      <div className={cn("transition-all duration-300", collapsed ? "lg:pl-[72px]" : "lg:pl-64")}>
        <header className="sticky top-0 z-30 flex items-center justify-between gap-3 border-b border-border bg-card/95 px-3 py-3 backdrop-blur-md safe-top sm:px-4">
          <div className="flex min-w-0 items-center gap-2 sm:gap-3">
            <button
              type="button"
              className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg border border-border lg:hidden"
              onClick={() => setMobileOpen(true)}
              aria-label="Ouvrir le menu"
            >
              <Menu className="h-5 w-5" />
            </button>
            <div className="min-w-0">
              <p className="truncate text-xs text-muted-foreground">Bienvenue</p>
              <p className="truncate font-semibold">{user.first_name} {user.last_name}</p>
            </div>
          </div>
          <div className="flex shrink-0 items-center gap-2">
            <NotificationBell />
            <Button asChild variant="outline" size="sm" className="hidden sm:inline-flex">
              <Link href="/annonces">Annonces</Link>
            </Button>
          </div>
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
