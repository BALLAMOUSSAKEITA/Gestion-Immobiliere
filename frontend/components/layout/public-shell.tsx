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
    <div className="flex min-h-screen flex-col bg-background">
      <header className="sticky top-0 z-40 border-b border-border bg-card safe-top">
        <div className="mx-auto flex h-16 max-w-[1440px] items-center justify-between gap-4 px-5 sm:h-20 sm:px-10">
          <Link href="/" className="flex shrink-0 items-center gap-2">
            <Building2 className="h-7 w-7 text-accent" strokeWidth={2.5} />
            <span className="hidden text-lg font-semibold text-accent sm:inline">Gestion Immo</span>
          </Link>

          <nav className="hidden items-end gap-8 md:flex">
            {PUBLIC_NAV.map((item) => {
              const active = pathname === item.href || pathname.startsWith(`${item.href}/`);
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={cn(
                    "pb-1 text-base font-medium transition-colors",
                    active ? "nav-tab-active text-foreground" : "text-muted-foreground hover:text-foreground",
                  )}
                >
                  {item.label}
                </Link>
              );
            })}
            <Link
              href="/login"
              className={cn(
                "pb-1 text-base font-medium transition-colors",
                pathname === "/login" ? "nav-tab-active text-foreground" : "text-muted-foreground hover:text-foreground",
              )}
            >
              Connexion
            </Link>
          </nav>

          <div className="hidden items-center gap-3 md:flex">
            {user ? (
              <>
                <Link href={dashboardHref} className="text-sm font-medium text-foreground hover:underline">
                  Mon espace
                </Link>
                <button
                  type="button"
                  onClick={() => logout()}
                  className="flex h-10 w-10 items-center justify-center rounded-full bg-faint text-foreground hover:bg-[var(--bebe)]"
                  aria-label="Menu"
                >
                  <Menu className="h-4 w-4" />
                </button>
              </>
            ) : (
              <Button asChild variant="outline" size="sm" className="rounded-lg">
                <Link href="/login">Se connecter</Link>
              </Button>
            )}
          </div>

          <button
            type="button"
            className="flex h-10 w-10 items-center justify-center rounded-full bg-faint md:hidden"
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
            className="fixed inset-0 z-50 bg-black/40 md:hidden"
            onClick={() => setMobileOpen(false)}
            aria-label="Fermer le menu"
          />
          <div className="fixed inset-x-0 top-0 z-[60] bg-card p-5 shadow-[var(--shadow-dropdown)] safe-top md:hidden">
            <div className="mb-4 flex items-center justify-between">
              <span className="text-base font-semibold">Menu</span>
              <button type="button" onClick={() => setMobileOpen(false)} aria-label="Fermer">
                <X className="h-5 w-5" />
              </button>
            </div>
            <nav className="flex flex-col gap-1">
              {[...PUBLIC_NAV, { href: "/login", label: "Connexion" }].map((item) => (
                <Link
                  key={item.href}
                  href={item.href}
                  onClick={() => setMobileOpen(false)}
                  className="min-h-11 rounded-lg px-3 py-3 text-base font-medium hover:bg-faint"
                >
                  {item.label}
                </Link>
              ))}
            </nav>
          </div>
        </>
      )}

      <div className="flex-1 pb-20 md:pb-0">{children}</div>

      <nav className="fixed inset-x-0 bottom-0 z-40 flex border-t border-border bg-card pb-safe md:hidden">
        {[
          { href: "/annonces", icon: Search, label: "Annonces" },
          { href: "/contact", icon: MessageSquare, label: "Contact" },
          { href: user ? dashboardHref : "/login", icon: LogIn, label: user ? "Espace" : "Connexion" },
        ].map(({ href, icon: Icon, label }) => (
          <Link
            key={href}
            href={href}
            className={cn(
              "flex flex-1 flex-col items-center gap-0.5 py-2 text-[11px] font-medium",
              pathname.startsWith(href) ? "text-accent" : "text-muted-foreground",
            )}
          >
            <Icon className="h-5 w-5" />
            {label}
          </Link>
        ))}
      </nav>

      <footer className="hidden border-t border-border bg-background md:block">
        <div className="mx-auto grid max-w-[1440px] grid-cols-3 gap-8 px-10 py-12">
          {[
            { title: "Découvrir", links: [{ href: "/annonces", label: "Annonces" }, { href: "/contact", label: "Contact" }] },
            { title: "Compte", links: [{ href: "/login", label: "Connexion" }, { href: dashboardHref, label: "Mon espace" }] },
            { title: "Assistance", links: [{ href: "/contact", label: "Nous contacter" }] },
          ].map((col) => (
            <div key={col.title}>
              <p className="text-sm font-semibold text-foreground">{col.title}</p>
              <ul className="mt-3 space-y-3">
                {col.links.map((link) => (
                  <li key={link.href}>
                    <Link href={link.href} className="text-sm text-muted-foreground hover:text-foreground">
                      {link.label}
                    </Link>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
        <div className="border-t border-border">
          <div className="mx-auto flex max-w-[1440px] items-center justify-between px-10 py-5 text-sm text-muted-foreground">
            <p>© {new Date().getFullYear()} Gestion Immobilière</p>
            <p>Franc guinéen (FG)</p>
          </div>
        </div>
      </footer>
    </div>
  );
}
