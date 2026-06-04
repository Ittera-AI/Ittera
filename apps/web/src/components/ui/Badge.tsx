import { cn } from "@/lib/utils";

type BadgeVariant =
  | "default"
  | "gradient"
  | "success"
  | "warning"
  | "secondary"
  | "outline"
  | "destructive";

interface BadgeProps {
  children: React.ReactNode;
  className?: string;
  variant?: BadgeVariant;
}

const variantClasses: Record<BadgeVariant, string> = {
  default: "bg-neutral-100 text-neutral-700 border border-neutral-200",
  gradient:
    "bg-[#A38A70]/10 border border-[#A38A70]/25 text-[#8B6F52]",
  success: "bg-emerald-500/10 text-emerald-600 border-emerald-500/20",
  warning: "bg-amber-500/10 text-amber-600 border-amber-500/20",
  secondary: "bg-secondary text-secondary-foreground border-transparent",
  outline: "bg-transparent text-foreground border-border",
  destructive: "bg-destructive/10 text-destructive border-destructive/20",
};

export function Badge({
  children,
  className,
  variant = "default",
}: BadgeProps) {
  return (
    <span
      className={cn(
        "inline-flex items-center px-2.5 py-0.5 rounded-md text-xs font-medium border",
        variantClasses[variant],
        className
      )}
    >
      {children}
    </span>
  );
}

export default Badge;
