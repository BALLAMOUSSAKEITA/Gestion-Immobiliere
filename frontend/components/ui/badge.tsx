import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";

import { cn } from "@/lib/utils";

const badgeVariants = cva(
  "inline-flex items-center rounded-full px-3 py-1.5 text-xs font-semibold shadow-[var(--shadow-subtle)]",
  {
    variants: {
      variant: {
        default: "bg-card text-foreground",
        accent: "bg-card text-foreground",
        primary: "bg-card text-foreground",
        success: "bg-card text-foreground",
        warning: "bg-card text-foreground",
        destructive: "bg-card text-foreground",
        outline: "border border-border bg-card text-muted-foreground shadow-none",
      },
    },
    defaultVariants: { variant: "default" },
  },
);

export interface BadgeProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof badgeVariants> {}

function Badge({ className, variant, ...props }: BadgeProps) {
  return <div className={cn(badgeVariants({ variant }), className)} {...props} />;
}

export { Badge, badgeVariants };
