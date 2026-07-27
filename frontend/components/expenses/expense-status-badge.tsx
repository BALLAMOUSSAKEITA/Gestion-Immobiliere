import { EXPENSE_STATUS_LABELS, type ExpenseStatus } from "@/lib/api";
import { cn } from "@/lib/utils";

const STATUS_STYLES: Record<ExpenseStatus, string> = {
  recorded: "bg-zinc-100 text-zinc-700",
  pending_validation: "bg-amber-100 text-amber-800",
  validated: "bg-green-100 text-green-800",
  rejected: "bg-red-100 text-red-800",
};

type ExpenseStatusBadgeProps = {
  status: ExpenseStatus;
  className?: string;
};

export function ExpenseStatusBadge({ status, className }: ExpenseStatusBadgeProps) {
  return (
    <span
      className={cn(
        "inline-flex rounded-full px-2.5 py-1 text-xs font-medium",
        STATUS_STYLES[status],
        className,
      )}
    >
      {EXPENSE_STATUS_LABELS[status]}
    </span>
  );
}
