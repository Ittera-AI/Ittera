import Badge from "@/components/ui/Badge";

export function StatusPill({ children }: { children: React.ReactNode }) {
  return <Badge variant="default">{children}</Badge>;
}
