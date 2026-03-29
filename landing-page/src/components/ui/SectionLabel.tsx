import { cn } from "@/lib/utils";

interface SectionLabelProps {
  children: React.ReactNode;
  className?: string;
}

export default function SectionLabel({ children, className }: SectionLabelProps) {
  return (
    <div
      className={cn(
        "inline-flex items-center gap-2 px-3 py-1.5 rounded-md",
        "bg-[#A38A70]/10 border border-[#A38A70]/25",
        "text-xs font-semibold uppercase tracking-widest text-[#8B6F52]",
        className
      )}
    >
      <span className="w-1.5 h-1.5 rounded-full bg-[#A38A70] animate-pulse" />
      {children}
    </div>
  );
}
