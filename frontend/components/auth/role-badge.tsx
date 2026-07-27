import { cn } from "@/lib/utils";

const ROLE_STYLES: Record<string, string> = {
  super_admin: "bg-purple-100 text-purple-800",
  admin_familial: "bg-blue-100 text-blue-800",
  proprietaire: "bg-emerald-100 text-emerald-800",
  gestionnaire: "bg-amber-100 text-amber-800",
  visiteur: "bg-zinc-100 text-zinc-800",
  locataire: "bg-cyan-100 text-cyan-800",
};

type RoleBadgeProps = {
  code: string;
  label: string;
  className?: string;
};

export function RoleBadge({ code, label, className }: RoleBadgeProps) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full px-3 py-1 text-xs font-medium",
        ROLE_STYLES[code] ?? "bg-zinc-100 text-zinc-800",
        className,
      )}
    >
      {label}
    </span>
  );
}
