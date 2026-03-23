import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { AuthProvider } from "@/context/AuthContext";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
  display: "swap",
});

export const metadata: Metadata = {
  title: "Ittera — AI Content Strategy Engine",
  description:
    "Plan, optimize, and analyze your content strategy across platforms with AI. Join 847+ creators on the waitlist.",
  keywords: ["content strategy", "AI", "content calendar", "creators", "marketing"],
  openGraph: {
    title: "Ittera — AI Content Strategy Engine",
    description: "Plan, optimize, and analyze your content strategy across platforms with AI.",
    siteName: "Ittera",
    type: "website",
  },
  twitter: {
    card: "summary_large_image",
    title: "Ittera — AI Content Strategy Engine",
    description: "Plan, optimize, and analyze your content strategy across platforms with AI.",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="scroll-smooth">
      <body className={`${inter.variable} antialiased`} style={{ background: "#030407", color: "#e8eaf0" }}>
        <AuthProvider>
          {children}
        </AuthProvider>
      </body>
    </html>
  );
}
