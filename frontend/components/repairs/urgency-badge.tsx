import { URGENCY_LABELS, type UrgencyLevel } from "@/lib/api";
import { cn } from "@/lib/utils";

const STYLES: Record<UrgencyLevel, string> = {
  low: "bg-green-100 text-green-800",
  medium: "bg-orange-100 text-orange-800",
  high: "bg-red-100 text-red-800",
};

export function UrgencyBadge({
  urgency,
  className,
}: {
  urgency: UrgencyLevel;
  className?: string;
}) {
  return (
    <span
      className={cn(
        "inline-flex rounded-full px-2.5 py-1 text-xs font-medium",
        STYLES[urgency],
        className,
      )}
    >
      {URGENCY_LABELS[urgency]}
    </span>
  );
}
