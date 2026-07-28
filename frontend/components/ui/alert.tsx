import { cn } from "@/lib/utils";

type AlertProps = {
  variant?: "default" | "success" | "destructive" | "warning";
  className?: string;
  children: React.ReactNode;
};

const variants = {
  default: "border-border bg-card text-foreground",
  success: "border-emerald-200 bg-emerald-50 text-emerald-900",
  destructive: "border-red-200 bg-red-50 text-red-900",
  warning: "border-amber-200 bg-amber-50 text-amber-900",
};

export function Alert({ variant = "default", className, children }: AlertProps) {
  return (
    <div className={cn("rounded-lg border px-4 py-3 text-sm", variants[variant], className)}>
      {children}
    </div>
  );
}
