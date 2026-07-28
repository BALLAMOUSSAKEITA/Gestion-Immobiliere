import { cn } from "@/lib/utils";

import type { LeaseStatus } from "@/lib/api";
import { LEASE_STATUS_LABELS } from "@/lib/api";

const STATUS_COLORS: Record<LeaseStatus, string> = {
  pending: "bg-muted text-foreground",
  active: "bg-emerald-100 text-emerald-800",
  expired: "bg-amber-100 text-amber-800",
  terminated: "bg-red-100 text-red-800",
};

export function LeaseStatusBadge({
  status,
  className,
}: {
  status: LeaseStatus;
  className?: string;
}) {
  return (
    <span
      className={cn(
        "inline-flex rounded-full px-2.5 py-0.5 text-xs font-medium",
        STATUS_COLORS[status],
        className,
      )}
    >
      {LEASE_STATUS_LABELS[status]}
    </span>
  );
}
