import { REPAIR_STATUS_LABELS, type RepairStatus } from "@/lib/api";
import { cn } from "@/lib/utils";

const STYLES: Record<RepairStatus, string> = {
  new: "bg-blue-100 text-blue-800",
  under_review: "bg-purple-100 text-purple-800",
  technician_assigned: "bg-indigo-100 text-indigo-800",
  in_progress: "bg-amber-100 text-amber-800",
  completed: "bg-green-100 text-green-800",
  cancelled: "bg-muted text-foreground",
};

export function RepairStatusBadge({
  status,
  className,
}: {
  status: RepairStatus;
  className?: string;
}) {
  return (
    <span
      className={cn(
        "inline-flex rounded-full px-2.5 py-1 text-xs font-medium",
        STYLES[status],
        className,
      )}
    >
      {REPAIR_STATUS_LABELS[status]}
    </span>
  );
}
