"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";
import { Building2, LogIn, Menu, MessageSquare, Search, X } from "lucide-react";

import { Button } from "@/components/ui/button";
import { useAuth } from "@/contexts/auth-context";
import { PUBLIC_NAV } from "@/lib/navigation";
import { cn } from "@/lib/utils";

export function PublicShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const { user, logout } = useAuth();
  const [mobileOpen, setMobileOpen] = useState(false);

  const dashboardHref = user?.role.code === "locataire" ? "/espace-locataire" : "/dashboard";

  return (
    <div className="flex min-h-screen flex-col">
      <header className="sticky top-0 z-40 border-b border-border/60 bg-card/95 backdrop-blur-md safe-top">
        <div className="mx-auto flex max-w-7xl items-center justify-between gap-3 px-3 py-3 sm:px-6 sm:py-4">
          <Link href="/" className="flex min-w-0 items-center gap-2 sm:gap-3">
            <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-primary text-primary-foreground sm:h-10 sm:w-10">
              <Building2 className="h-5 w-5" />
            </div>
            <div className="min-w-0">
              <p className="truncate font-bold leading-tight">Gestion Immobilière</p>
              <p className="hidden text-xs text-muted-foreground sm:block">Patrimoine & location</p>
            </div>
          </Link>

          <nav className="hidden items-center gap-1 md:flex">
            {PUBLIC_NAV.map((item) => (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  "rounded-lg px-4 py-2 text-sm font-medium transition-colors",
                  pathname === item.href || pathname.startsWith(`${item.href}/`)
                    ? "bg-primary text-primary-foreground"
                    : "text-muted-foreground hover:bg-secondary hover:text-foreground",
                )}
              >
                {item.label}
              </Link>
            ))}
          </nav>

          <div className="hidden items-center gap-2 md:flex">
            {user ? (
              <>
                <Button asChild variant="outline" size="sm">
                  <Link href={dashboardHref}>Mon espace</Link>
                </Button>
                <Button variant="ghost" size="sm" onClick={() => logout()}>
                  Déconnexion
                </Button>
              </>
            ) : (
              <Button asChild size="sm">
                <Link href="/login">Connexion</Link>
              </Button>
            )}
          </div>

          <button
            type="button"
            className="flex h-10 w-10 items-center justify-center rounded-lg border border-border md:hidden"
            onClick={() => setMobileOpen(true)}
            aria-label="Ouvrir le menu"
          >
            <Menu className="h-5 w-5" />
          </button>
        </div>
      </header>

      {mobileOpen && (
        <>
          <button
            type="button"
            className="fixed inset-0 z-50 bg-black/50 md:hidden"
            onClick={() => setMobileOpen(false)}
            aria-label="Fermer le menu"
          />
          <div className="fixed inset-x-0 top-0 z-[60] border-b border-border bg-card p-4 shadow-lg safe-top md:hidden">
            <div className="mb-4 flex items-center justify-between">
              <p className="font-semibold">Menu</p>
              <button type="button" onClick={() => setMobileOpen(false)} aria-label="Fermer">
                <X className="h-5 w-5" />
              </button>
            </div>
            <nav className="flex flex-col gap-2">
              {PUBLIC_NAV.map((item) => (
                <Link
                  key={item.href}
                  href={item.href}
                  onClick={() => setMobileOpen(false)}
                  className={cn(
                    "min-h-11 rounded-lg px-4 py-3 text-sm font-medium",
                    pathname === item.href ? "bg-primary text-primary-foreground" : "bg-muted/50",
                  )}
                >
                  {item.label}
                </Link>
              ))}
              {user ? (
                <>
                  <Link href={dashboardHref} onClick={() => setMobileOpen(false)} className="min-h-11 rounded-lg bg-muted/50 px-4 py-3 text-sm font-medium">
                    Mon espace
                  </Link>
                  <button type="button" onClick={() => { logout(); setMobileOpen(false); }} className="min-h-11 rounded-lg bg-muted/50 px-4 py-3 text-left text-sm font-medium">
                    Déconnexion
                  </button>
                </>
              ) : (
                <Link href="/login" onClick={() => setMobileOpen(false)} className="min-h-11 rounded-lg bg-accent px-4 py-3 text-center text-sm font-medium text-accent-foreground">
                  Connexion
                </Link>
              )}
            </nav>
          </div>
        </>
      )}

      <div className="flex-1 pb-20 md:pb-0">{children}</div>

      <nav className="fixed inset-x-0 bottom-0 z-40 flex border-t border-border bg-card/95 backdrop-blur-md pb-safe md:hidden">
        <Link
          href="/annonces"
          className={cn(
            "flex flex-1 flex-col items-center gap-1 py-2 text-[11px] font-medium",
            pathname.startsWith("/annonces") ? "text-accent" : "text-muted-foreground",
          )}
        >
          <Search className="h-5 w-5" />
          Annonces
        </Link>
        <Link
          href="/contact"
          className={cn(
            "flex flex-1 flex-col items-center gap-1 py-2 text-[11px] font-medium",
            pathname.startsWith("/contact") ? "text-accent" : "text-muted-foreground",
          )}
        >
          <MessageSquare className="h-5 w-5" />
          Contact
        </Link>
        <Link
          href={user ? dashboardHref : "/login"}
          className={cn(
            "flex flex-1 flex-col items-center gap-1 py-2 text-[11px] font-medium",
            pathname === "/login" ? "text-accent" : "text-muted-foreground",
          )}
        >
          <LogIn className="h-5 w-5" />
          {user ? "Mon espace" : "Connexion"}
        </Link>
      </nav>

      <footer className="hidden border-t border-border bg-card md:block">
        <div className="mx-auto flex max-w-7xl flex-col gap-4 px-4 py-8 text-sm text-muted-foreground sm:flex-row sm:items-center sm:justify-between sm:px-6">
          <p>© {new Date().getFullYear()} Gestion Immobilière — Tous droits réservés</p>
          <div className="flex gap-4">
            <Link href="/annonces" className="hover:text-foreground">Annonces</Link>
            <Link href="/contact" className="hover:text-foreground">Contact</Link>
            <Link href="/login" className="hover:text-foreground">Connexion</Link>
          </div>
        </div>
      </footer>
    </div>
  );
}
