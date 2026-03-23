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
        "bg-white/[0.04] backdrop-blur-md border border-white/[0.08] rounded-2xl",
        glow && "shadow-glow-purple",
        hover &&
          "transition-all duration-300 hover:bg-white/[0.06] hover:border-white/[0.15] hover:-translate-y-1",
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
