import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Waitlist Status · Ittera",
  description: "Your position on the Ittera beta waitlist.",
};

export default function WaitlistStatusLayout({ children }: { children: React.ReactNode }) {
  return children;
}
