import { setRequestLocale } from "next-intl/server";
import { Navbar, MarketingFooter, CTASection } from "@/components/marketing";
import { FeaturesPageContent } from "./FeaturesPageContent";

export default async function FeaturesPage({
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
        <FeaturesPageContent />
        <CTASection />
      </main>
      <MarketingFooter />
    </>
  );
}
