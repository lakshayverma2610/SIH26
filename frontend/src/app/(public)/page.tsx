import Navbar from "@/components/layout/Navbar";
import Hero from "./landing/components/Hero";
import ProblemSection from "./landing/components/ProblemSection";
import HowItWorks from "./landing/components/HowItWorks";
import Capabilities from "./landing/components/Capabilities";
import IntelligencePreview from "./landing/components/IntelligencePreview";
import RealTimeResponse from "./landing/components/RealTimeResponse";
import ImpactSection from "./landing/components/ImpactSection";
import SecuritySection from "./landing/components/SecuritySection";
import FinalCTA from "./landing/components/FinalCTA";
import Footer from "./landing/components/Footer";

export default function Home() {
  return (
    <>
      <Navbar />
      <main>
        <Hero />
        <ProblemSection />
        <HowItWorks />
        <Capabilities />
        <IntelligencePreview />
        <RealTimeResponse />
        <ImpactSection />
        <SecuritySection />
        <FinalCTA />
      </main>
      <Footer />
    </>
  );
}
