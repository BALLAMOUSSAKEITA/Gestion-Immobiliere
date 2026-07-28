import { cn } from "@/lib/utils";

type KpiCardProps = {
  label: string;
  value: string;
  hint?: string;
  trend?: "up" | "down" | "neutral";
};

export function KpiCard({ label, value, hint, trend = "neutral" }: KpiCardProps) {
  return (
    <div className="surface-card p-4 sm:p-5">
      <p className="text-xs font-medium text-muted-foreground sm:text-sm">{label}</p>
      <p className="mt-2 break-words text-xl font-semibold tabular-nums tracking-tight text-foreground sm:text-2xl">
        {value}
      </p>
      {hint && (
        <p
          className={cn(
            "mt-2 text-xs font-medium",
            trend === "up" && "text-[var(--success)]",
            trend === "down" && "text-accent",
            trend === "neutral" && "text-muted-foreground",
          )}
        >
          {hint}
        </p>
      )}
    </div>
  );
}
