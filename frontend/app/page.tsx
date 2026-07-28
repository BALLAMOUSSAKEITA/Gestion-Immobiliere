import Link from "next/link";
import { ArrowRight, Building2, Shield, Wallet } from "lucide-react";

import { PublicShell } from "@/components/layout/public-shell";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { fetchHealth } from "@/lib/api";

async function ApiStatus() {
  try {
    const health = await fetchHealth();
    return (
      <span className="inline-flex items-center gap-2 rounded-full bg-emerald-100 px-3 py-1 text-sm text-emerald-800">
        <span className="h-2 w-2 rounded-full bg-emerald-500" />
        API connectée — v{health.version}
      </span>
    );
  } catch {
    return (
      <span className="inline-flex items-center gap-2 rounded-full bg-red-100 px-3 py-1 text-sm text-red-800">
        <span className="h-2 w-2 rounded-full bg-red-500" />
        API hors ligne
      </span>
    );
  }
}

export default function Home() {
  return (
    <PublicShell>
      <section className="gradient-hero">
        <div className="mx-auto grid max-w-7xl gap-12 px-4 py-20 sm:px-6 lg:grid-cols-2 lg:items-center lg:py-28">
          <div>
            <div className="mb-6 inline-flex items-center gap-2 rounded-full border border-border bg-card px-4 py-1.5 text-sm text-muted-foreground shadow-sm">
              <Building2 className="h-4 w-4 text-accent" />
              Plateforme de gestion immobilière
            </div>
            <h1 className="text-4xl font-bold tracking-tight text-foreground sm:text-5xl lg:text-6xl">
              Pilotez votre patrimoine immobilier avec clarté
            </h1>
            <p className="mt-6 text-lg leading-relaxed text-muted-foreground">
              Immeubles, locataires, loyers, impayés, documents et rapports — une seule
              interface moderne pour toute votre activité.
            </p>
            <div className="mt-8 flex flex-wrap items-center gap-4">
              <Button asChild size="lg" variant="accent">
                <Link href="/login">
                  Accéder à l&apos;application
                  <ArrowRight className="h-4 w-4" />
                </Link>
              </Button>
              <Button asChild size="lg" variant="outline">
                <Link href="/annonces">Voir les annonces</Link>
              </Button>
            </div>
            <div className="mt-8">
              <ApiStatus />
            </div>
          </div>

          <div className="grid gap-4 sm:grid-cols-2">
            {[
              { icon: Building2, title: "Patrimoine", text: "Immeubles, logements et baux centralisés" },
              { icon: Wallet, title: "Finances", text: "Paiements, impayés et reçus automatisés" },
              { icon: Shield, title: "Sécurité", text: "Rôles, validations et traçabilité complète" },
            ].map((item) => (
              <Card key={item.title} className="border-border/60 shadow-[var(--shadow-md)]">
                <CardContent className="p-6">
                  <item.icon className="mb-4 h-8 w-8 text-accent" />
                  <h3 className="font-semibold">{item.title}</h3>
                  <p className="mt-2 text-sm text-muted-foreground">{item.text}</p>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </section>
    </PublicShell>
  );
}
