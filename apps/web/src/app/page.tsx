import CursorGlow from "@/components/ui/CursorGlow";
import ScrollProgress from "@/components/ui/ScrollProgress";
import GrainOverlay from "@/components/ui/GrainOverlay";
import AuthModal from "@/components/auth/AuthModal";
import Navbar from "@/components/layout/Navbar";
import Footer from "@/components/layout/Footer";
import Hero from "@/components/sections/Hero";
import Problem from "@/components/sections/Problem";
import Transformation from "@/components/sections/Transformation";
import Features from "@/components/sections/Features";
import DemoStrip from "@/components/sections/DemoStrip";
import HowItWorks from "@/components/sections/HowItWorks";
import Waitlist from "@/components/sections/Waitlist";
import FAQ from "@/components/sections/FAQ";
import Founders from "@/components/sections/Founders";
import FinalCTA from "@/components/sections/FinalCTA";

export default function Home() {
  return (
    <div className="min-h-screen overflow-x-hidden">
      <CursorGlow />
      <ScrollProgress />
      <GrainOverlay />
      <AuthModal />
      <Navbar />
      <main className="relative" style={{ zIndex: 1 }}>
        <Hero />
        <Problem />
        <Transformation />
        <Features />
        <DemoStrip />
        <HowItWorks />
        <Founders />
        <Waitlist />
        <FAQ />
        <FinalCTA />
      </main>
      <Footer />
    </div>
  );
}
