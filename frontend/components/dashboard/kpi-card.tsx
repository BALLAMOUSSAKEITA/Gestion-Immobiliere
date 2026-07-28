import { cn } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";

type KpiCardProps = {
  label: string;
  value: string;
  hint?: string;
  trend?: "up" | "down" | "neutral";
};

export function KpiCard({ label, value, hint, trend = "neutral" }: KpiCardProps) {
  return (
    <div className="glass-card p-5 transition-shadow hover:shadow-[var(--shadow-md)]">
      <p className="text-sm font-medium text-muted-foreground">{label}</p>
      <p className="mt-2 text-3xl font-bold tracking-tight text-foreground">{value}</p>
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
