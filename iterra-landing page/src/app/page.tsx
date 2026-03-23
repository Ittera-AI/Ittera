import CursorGlow from "@/components/ui/CursorGlow";
import ScrollProgress from "@/components/ui/ScrollProgress";
import GrainOverlay from "@/components/ui/GrainOverlay";
import AuthModal from "@/components/auth/AuthModal";
import Navbar from "@/components/layout/Navbar";
import Footer from "@/components/layout/Footer";
import Hero from "@/components/sections/Hero";
import SocialProof from "@/components/sections/SocialProof";
import Problem from "@/components/sections/Problem";
import Solution from "@/components/sections/Solution";
import Features from "@/components/sections/Features";
import ProductShowcase from "@/components/sections/ProductShowcase";
import HowItWorks from "@/components/sections/HowItWorks";
import Benefits from "@/components/sections/Benefits";
import Waitlist from "@/components/sections/Waitlist";
import FAQ from "@/components/sections/FAQ";
import Founders from "@/components/sections/Founders";
import FinalCTA from "@/components/sections/FinalCTA";

export default function Home() {
  return (
    <div className="min-h-screen overflow-x-hidden" style={{ background: "#030407" }}>
      <CursorGlow />
      <ScrollProgress />
      <GrainOverlay />
      <AuthModal />
      <Navbar />
      <main className="relative" style={{ zIndex: 1 }}>
        <Hero />
        <SocialProof />
        <Problem />
        <Solution />
        <Features />
        <ProductShowcase />
        <HowItWorks />
        <Benefits />
        <Waitlist />
        <FAQ />
        <Founders />
        <FinalCTA />
      </main>
      <Footer />
    </div>
  );
}
