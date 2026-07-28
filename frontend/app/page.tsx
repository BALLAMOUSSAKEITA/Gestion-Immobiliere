import Link from "next/link";
import { ArrowRight, Building2, Search, Shield, Wallet } from "lucide-react";

import { PublicShell } from "@/components/layout/public-shell";
import { Button } from "@/components/ui/button";
import { fetchHealth } from "@/lib/api";

async function ApiStatus() {
  try {
    const health = await fetchHealth();
    return (
      <span className="inline-flex items-center gap-2 text-sm text-muted-foreground">
        <span className="h-2 w-2 rounded-full bg-[var(--success)]" />
        Service en ligne — v{health.version}
      </span>
    );
  } catch {
    return (
      <span className="inline-flex items-center gap-2 text-sm text-muted-foreground">
        <span className="h-2 w-2 rounded-full bg-accent" />
        Service temporairement indisponible
      </span>
    );
  }
}

export default function Home() {
  return (
    <PublicShell>
      <section className="border-b border-border bg-background">
        <div className="mx-auto flex max-w-[1440px] flex-col items-center px-5 py-16 sm:px-10 sm:py-20">
          <h1 className="heading-page max-w-2xl text-center">
            Trouvez et gérez vos logements en toute simplicité
          </h1>
          <p className="mt-4 max-w-xl text-center text-sm text-muted-foreground">
            Annonces, locataires, loyers et documents — une plateforme claire pour votre patrimoine immobilier en Guinée.
          </p>

          <Link href="/annonces" className="search-capsule mt-10 transition-shadow hover:shadow-[var(--shadow-subtle)]">
            <div className="hidden flex-1 flex-col justify-center border-r border-border px-6 py-4 sm:flex">
              <span className="text-ui text-foreground">Où</span>
              <span className="text-sm text-muted-foreground">Rechercher une commune</span>
            </div>
            <div className="hidden flex-1 flex-col justify-center border-r border-border px-6 py-4 md:flex">
              <span className="text-ui text-foreground">Type</span>
              <span className="text-sm text-muted-foreground">Appartement, magasin…</span>
            </div>
            <div className="flex flex-1 items-center justify-between gap-3 px-5 py-3 sm:py-4">
              <div className="flex flex-col justify-center sm:hidden">
                <span className="text-sm font-medium text-foreground">Rechercher un logement</span>
                <span className="text-xs text-muted-foreground">Voir les annonces disponibles</span>
              </div>
              <div className="hidden flex-col justify-center sm:flex">
                <span className="text-ui text-foreground">Budget</span>
                <span className="text-sm text-muted-foreground">Ajouter un montant</span>
              </div>
              <span className="flex h-12 w-12 shrink-0 items-center justify-center rounded-full bg-accent text-accent-foreground">
                <Search className="h-5 w-5" />
              </span>
            </div>
          </Link>

          <div className="mt-8 flex flex-wrap items-center justify-center gap-4">
            <Button asChild variant="accent" size="lg">
              <Link href="/login">
                Accéder à l&apos;application
                <ArrowRight className="h-4 w-4" />
              </Link>
            </Button>
            <Button asChild variant="outline" size="lg">
              <Link href="/contact">Nous contacter</Link>
            </Button>
          </div>
          <div className="mt-6">
            <ApiStatus />
          </div>
        </div>
      </section>

      <section className="mx-auto max-w-[1440px] px-5 py-12 sm:px-10">
        <div className="mb-8 flex items-center gap-2">
          <h2 className="heading-section">Pourquoi Gestion Immo ?</h2>
          <ArrowRight className="h-5 w-5 text-foreground" />
        </div>
        <div className="grid gap-10 sm:grid-cols-3">
          {[
            { icon: Building2, title: "Patrimoine", text: "Immeubles, logements et baux centralisés" },
            { icon: Wallet, title: "Finances", text: "Paiements, impayés et reçus en francs guinéens" },
            { icon: Shield, title: "Sécurité", text: "Rôles, validations et traçabilité complète" },
          ].map((item) => (
            <div key={item.title} className="space-y-3">
              <item.icon className="h-6 w-6 text-foreground" strokeWidth={1.75} />
              <h3 className="text-sm font-medium text-foreground">{item.title}</h3>
              <p className="text-sm text-muted-foreground">{item.text}</p>
            </div>
          ))}
        </div>
      </section>
    </PublicShell>
  );
}
