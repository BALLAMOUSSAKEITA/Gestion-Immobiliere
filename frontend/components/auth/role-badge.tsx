import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

const ROLE_VARIANTS: Record<string, "default" | "primary" | "accent" | "outline" | "success" | "warning"> = {
  super_admin: "primary",
  admin_familial: "default",
  proprietaire: "accent",
  gestionnaire: "warning",
  visiteur: "outline",
  locataire: "success",
};

type RoleBadgeProps = {
  code: string;
  label: string;
  className?: string;
};

export function RoleBadge({ code, label, className }: RoleBadgeProps) {
  return (
    <Badge variant={ROLE_VARIANTS[code] ?? "outline"} className={cn(className)}>
      {label}
    </Badge>
  );
}
