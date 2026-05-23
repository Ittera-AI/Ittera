import type { Metadata } from "next";
import Script from "next/script";
import { Inter, Geist } from "next/font/google";
import "./globals.css";
import { AuthProvider } from "@/context/AuthContext";
import AuthShell from "@/components/auth/AuthShell";
import { ThemeProvider } from "@/context/ThemeContext";
import { cn } from "@/lib/utils";

const geist = Geist({subsets:['latin'],variable:'--font-sans'});

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
    <html lang="en" className={cn("scroll-smooth", "font-sans", geist.variable)} suppressHydrationWarning>
      <body className={`${inter.variable} antialiased`}>
        <Script
          id="ittera-auth-redirect"
          strategy="beforeInteractive"
          dangerouslySetInnerHTML={{
            __html: `(function(){try{var p=location.pathname;if(p!=='/'&&p!=='/login')return;for(var i=0;i<localStorage.length;i++){var k=localStorage.key(i);if(!k||k.indexOf('sb-')!==0||k.slice(-11)!=='-auth-token')continue;var v=localStorage.getItem(k);if(v&&v!=='null'){location.replace('/waitlist-status');return}}}catch(e){}})()`,
          }}
        />
        <Script
          id="ittera-theme-init"
          strategy="beforeInteractive"
          dangerouslySetInnerHTML={{
            __html: `(function(){try{var t=localStorage.getItem('ittera-theme');var d=window.matchMedia('(prefers-color-scheme:dark)').matches;if(t==='dark'||(t===null&&d))document.documentElement.classList.add('dark')}catch(e){}})()`,
          }}
        />
        <ThemeProvider>
          <AuthProvider>
            <AuthShell>{children}</AuthShell>
          </AuthProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}
