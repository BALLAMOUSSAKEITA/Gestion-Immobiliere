import { cn } from "@/lib/utils";

type KpiCardProps = {
  label: string;
  value: string;
  hint?: string;
  trend?: "up" | "down" | "neutral";
};

export function KpiCard({ label, value, hint, trend = "neutral" }: KpiCardProps) {
  return (
    <div className="glass-card p-4 transition-shadow hover:shadow-[var(--shadow-md)] sm:p-5">
      <p className="text-xs font-medium text-muted-foreground sm:text-sm">{label}</p>
      <p className="mt-2 break-words text-xl font-bold tabular-nums tracking-tight text-foreground sm:text-2xl lg:text-3xl">
        {value}
      </p>
      {hint && (
        <p
          className={cn(
            "mt-2 text-xs font-medium",
            trend === "up" && "text-emerald-600",
            trend === "down" && "text-red-600",
            trend === "neutral" && "text-muted-foreground",
          )}
        >
          {hint}
        </p>
      )}
    </div>
  );
}
