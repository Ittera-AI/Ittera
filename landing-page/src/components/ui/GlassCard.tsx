import { cn } from "@/lib/utils";

interface GlassCardProps {
  children: React.ReactNode;
  className?: string;
  glow?: boolean;
  glowColor?: string;
  hover?: boolean;
}

export default function GlassCard({
  children,
  className,
  glow = false,
  glowColor,
  hover = false,
}: GlassCardProps) {
  return (
    <div
      className={cn(
        "bg-white border border-[#EAEAEC] rounded-xl",
        glow && "[box-shadow:0_1px_3px_rgba(0,0,0,0.06),0_1px_2px_rgba(0,0,0,0.04)]",
        hover &&
          "transition-all duration-300 hover:border-[#D4D4D4] hover:shadow-card-hover hover:-translate-y-1",
        className
      )}
      style={
        glowColor
          ? { boxShadow: `0 0 40px ${glowColor}` }
          : undefined
      }
    >
      {children}
    </div>
  );
}
