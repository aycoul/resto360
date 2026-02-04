import { setRequestLocale } from "next-intl/server";
import { Navbar, HeroSection, FeaturesGrid, StatsSection, Testimonials, IntegrationsSection, CTASection, MarketingFooter } from "@/components/marketing";

export default async function LandingPage({
  params,
}: {
  params: Promise<{ locale: string }>;
}) {
  const { locale } = await params;
  setRequestLocale(locale);

  return (
    <>
      <Navbar />
      <main>
        <HeroSection />
        <StatsSection />
        <FeaturesGrid />
        <Testimonials />
        <IntegrationsSection />
        <CTASection />
      </main>
      <MarketingFooter />
    </>
  );
}
