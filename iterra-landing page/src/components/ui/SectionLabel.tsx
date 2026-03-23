import { cn } from "@/lib/utils";

interface SectionLabelProps {
  children: React.ReactNode;
  className?: string;
}

export default function SectionLabel({ children, className }: SectionLabelProps) {
  return (
    <div
      className={cn(
        "inline-flex items-center gap-2 px-3 py-1.5 rounded-full",
        "bg-purple-500/10 border border-purple-500/20",
        "text-xs font-semibold uppercase tracking-widest text-purple-300",
        className
      )}
    >
      <span className="w-1.5 h-1.5 rounded-full bg-purple-400 animate-pulse" />
      {children}
    </div>
  );
}
