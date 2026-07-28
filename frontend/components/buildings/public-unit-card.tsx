import Link from "next/link";

import type { PublicUnitSummary } from "@/lib/api";
import { formatCurrency, UNIT_TYPE_LABELS } from "@/lib/api";
import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";

type PublicUnitCardProps = {
  unit: PublicUnitSummary;
};

export function PublicUnitCard({ unit }: PublicUnitCardProps) {
  const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
  const photoUrl = unit.primary_photo_url ? `${apiUrl}${unit.primary_photo_url}` : null;

  return (
    <Link href={`/annonces/${unit.id}`} className="group block">
      <Card className="overflow-hidden transition-all duration-300 hover:-translate-y-1 hover:shadow-[var(--shadow-lg)]">
        <div className="relative aspect-[4/3] overflow-hidden bg-muted">
          {photoUrl ? (
            // eslint-disable-next-line @next/next/no-img-element
            <img
              src={photoUrl}
              alt={unit.code}
              className="h-full w-full object-cover transition-transform duration-500 group-hover:scale-105"
            />
          ) : (
            <div className="flex h-full items-center justify-center text-sm text-muted-foreground">
              Aucune photo
            </div>
          )}
          <Badge variant="accent" className="absolute left-3 top-3">
            {UNIT_TYPE_LABELS[unit.type]}
          </Badge>
        </div>
        <div className="space-y-2 p-5">
          <div className="flex items-center justify-between gap-2">
            <p className="text-xl font-bold text-primary">{formatCurrency(unit.rent_amount)}</p>
            <span className="text-xs text-muted-foreground">{unit.code}</span>
          </div>
          <p className="text-sm text-muted-foreground">
            {[unit.commune, unit.quartier].filter(Boolean).join(" · ")}
          </p>
        </div>
      </Card>
    </Link>
  );
}
