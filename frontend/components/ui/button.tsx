import * as React from "react";
import { Slot } from "@radix-ui/react-slot";
import { cva, type VariantProps } from "class-variance-authority";

import { cn } from "@/lib/utils";

const buttonVariants = cva(
  "inline-flex items-center justify-center gap-2 whitespace-nowrap text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50",
  {
    variants: {
      variant: {
        default: "rounded-full bg-primary text-primary-foreground hover:bg-primary/90",
        accent: "rounded-full bg-accent text-accent-foreground hover:bg-[var(--rausch-600)]",
        outline:
          "rounded-lg border border-foreground bg-transparent text-foreground hover:bg-faint",
        ghost: "rounded-full text-foreground hover:bg-faint",
        destructive: "rounded-full bg-destructive text-destructive-foreground hover:opacity-90",
        inverse: "rounded-lg bg-primary px-4 text-primary-foreground hover:bg-primary/90",
      },
      size: {
        default: "h-11 px-5",
        lg: "h-12 px-8 text-base",
        sm: "h-9 px-4 text-sm",
        icon: "h-10 w-10 rounded-full",
        pill: "h-12 w-12 rounded-full",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  },
);

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  asChild?: boolean;
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, asChild = false, ...props }, ref) => {
    const Comp = asChild ? Slot : "button";
    return (
      <Comp className={cn(buttonVariants({ variant, size, className }))} ref={ref} {...props} />
    );
  },
);
Button.displayName = "Button";

export { Button, buttonVariants };
