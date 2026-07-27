import Link from "next/link";

import type { PublicUnitSummary } from "@/lib/api";
import { formatCurrency, UNIT_TYPE_LABELS } from "@/lib/api";

type PublicUnitCardProps = {
  unit: PublicUnitSummary;
};

export function PublicUnitCard({ unit }: PublicUnitCardProps) {
  const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
  const photoUrl = unit.primary_photo_url
    ? `${apiUrl}${unit.primary_photo_url}`
    : null;

  return (
    <Link
      href={`/annonces/${unit.id}`}
      className="overflow-hidden rounded-xl border border-zinc-200 bg-white shadow-sm transition hover:shadow-md"
    >
      <div className="aspect-video bg-zinc-100">
        {photoUrl ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img src={photoUrl} alt={unit.code} className="h-full w-full object-cover" />
        ) : (
          <div className="flex h-full items-center justify-center text-sm text-zinc-400">
            Aucune photo
          </div>
        )}
      </div>
      <div className="space-y-2 p-4">
        <div className="flex items-center justify-between gap-2">
          <p className="font-semibold">{UNIT_TYPE_LABELS[unit.type]}</p>
          <span className="text-xs text-zinc-500">{unit.code}</span>
        </div>
        <p className="text-lg font-bold">{formatCurrency(unit.rent_amount)}</p>
        <p className="text-sm text-zinc-600">
          {[unit.commune, unit.quartier].filter(Boolean).join(" · ")}
        </p>
      </div>
    </Link>
  );
}
