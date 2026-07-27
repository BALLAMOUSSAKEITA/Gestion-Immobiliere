import { cn } from "@/lib/utils";

import type { UnitStatus } from "@/lib/api";

const STATUS_CONFIG: Record<
  UnitStatus,
  { label: string; className: string }
> = {
  free: { label: "Libre", className: "bg-emerald-100 text-emerald-800" },
  occupied: { label: "Occupé", className: "bg-blue-100 text-blue-800" },
  reserved: { label: "Réservé", className: "bg-amber-100 text-amber-800" },
  under_repair: { label: "En réparation", className: "bg-red-100 text-red-800" },
};

type UnitStatusBadgeProps = {
  status: UnitStatus;
  className?: string;
};

export function UnitStatusBadge({ status, className }: UnitStatusBadgeProps) {
  const config = STATUS_CONFIG[status];
  return (
    <span
      className={cn(
        "inline-flex rounded-full px-2.5 py-0.5 text-xs font-medium",
        config.className,
        className,
      )}
    >
      {config.label}
    </span>
  );
}
