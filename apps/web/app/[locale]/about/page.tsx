import { setRequestLocale } from "next-intl/server";
import { Navbar, MarketingFooter, CTASection } from "@/components/marketing";
import { AboutPageContent } from "./AboutPageContent";

export default async function AboutPage({
  params,
}: {
  params: Promise<{ locale: string }>;
}) {
  const { locale } = await params;
  setRequestLocale(locale);

  return (
    <>
      <Navbar />
      <main className="pt-16">
        <AboutPageContent />
        <CTASection />
      </main>
      <MarketingFooter />
    </>
  );
}
