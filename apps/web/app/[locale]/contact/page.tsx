import { setRequestLocale } from "next-intl/server";
import { Navbar, MarketingFooter } from "@/components/marketing";
import { ContactPageContent } from "./ContactPageContent";

export default async function ContactPage({
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
        <ContactPageContent />
      </main>
      <MarketingFooter />
    </>
  );
}
