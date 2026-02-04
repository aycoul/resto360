import { setRequestLocale } from "next-intl/server";
import { Navbar, MarketingFooter } from "@/components/marketing";
import { PricingPageContent } from "./PricingPageContent";

export default async function PricingPage({
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
        <PricingPageContent />
      </main>
      <MarketingFooter />
    </>
  );
}
