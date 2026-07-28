import Link from "next/link";

import type { PublicUnitSummary } from "@/lib/api";
import { formatCurrency, UNIT_TYPE_LABELS } from "@/lib/api";
import { Badge } from "@/components/ui/badge";

type PublicUnitCardProps = {
  unit: PublicUnitSummary;
};

export function PublicUnitCard({ unit }: PublicUnitCardProps) {
  const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
  const photoUrl = unit.primary_photo_url ? `${apiUrl}${unit.primary_photo_url}` : null;

  return (
    <Link href={`/annonces/${unit.id}`} className="group block">
      <article>
        <div className="relative aspect-square overflow-hidden rounded-[12px] bg-[var(--deco)]">
          {photoUrl ? (
            // eslint-disable-next-line @next/next/no-img-element
            <img
              src={photoUrl}
              alt={unit.code}
              className="h-full w-full object-cover transition-transform duration-300 group-hover:scale-[1.02]"
            />
          ) : (
            <div className="flex h-full items-center justify-center text-sm text-muted-foreground">
              Aucune photo
            </div>
          )}
          <Badge className="absolute left-3 top-3">
            {UNIT_TYPE_LABELS[unit.type]}
          </Badge>
        </div>
        <div className="mt-3 space-y-0.5">
          <p className="truncate text-sm font-medium text-foreground">
            {unit.code} · {[unit.commune, unit.quartier].filter(Boolean).join(", ")}
          </p>
          <p className="text-sm text-muted-foreground">Disponible · Location mensuelle</p>
          <p className="text-sm text-foreground">
            <span className="font-semibold">{formatCurrency(unit.rent_amount)}</span>
            <span className="text-muted-foreground"> / mois</span>
          </p>
        </div>
      </article>
    </Link>
  );
}
