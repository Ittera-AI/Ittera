import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { AuthProvider } from "@/context/AuthContext";
import { ThemeProvider } from "@/context/ThemeContext";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
  display: "swap",
});

export const metadata: Metadata = {
  title: "Ittera - AI Content Strategy Engine",
  description:
    "Plan, optimize, and analyze your content strategy across platforms with AI. Join the Ittera founding cohort waitlist.",
  keywords: ["content strategy", "AI", "content calendar", "creators", "marketing"],
  openGraph: {
    title: "Ittera - AI Content Strategy Engine",
    description: "Plan, optimize, and analyze your content strategy across platforms with AI.",
    siteName: "Ittera",
    type: "website",
  },
  twitter: {
    card: "summary_large_image",
    title: "Ittera - AI Content Strategy Engine",
    description: "Plan, optimize, and analyze your content strategy across platforms with AI.",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="scroll-smooth" suppressHydrationWarning>
      <head>
        {/* Prevent flash of wrong theme — runs before React hydration */}
        <script
          dangerouslySetInnerHTML={{
            __html: `(function(){try{var t=localStorage.getItem('ittera-theme');var d=window.matchMedia('(prefers-color-scheme:dark)').matches;if(t==='dark'||(t===null&&d))document.documentElement.classList.add('dark')}catch(e){}})()`,
          }}
        />
      </head>
      <body className={`${inter.variable} antialiased`}>
        <ThemeProvider>
          <AuthProvider>{children}</AuthProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}
