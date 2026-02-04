import { setRequestLocale } from "next-intl/server";
import { Navbar, MarketingFooter, CTASection } from "@/components/marketing";
import { UseCasesPageContent } from "./UseCasesPageContent";

export default async function UseCasesPage({
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
        <UseCasesPageContent />
        <CTASection />
      </main>
      <MarketingFooter />
    </>
  );
}
