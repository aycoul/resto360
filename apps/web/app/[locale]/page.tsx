import { useTranslations } from "next-intl";
import { setRequestLocale } from "next-intl/server";
import Link from "next/link";

export default async function HomePage({
  params,
}: {
  params: Promise<{ locale: string }>;
}) {
  const { locale } = await params;
  setRequestLocale(locale);

  return <HomeContent locale={locale} />;
}

function HomeContent({ locale }: { locale: string }) {
  const t = useTranslations("pos");

  return (
    <main className="min-h-screen p-8">
      <h1 className="text-3xl font-bold mb-4">RESTO360</h1>
      <nav className="space-y-2">
        <Link
          href={`/${locale}/pos`}
          className="block p-4 bg-blue-500 text-white rounded hover:bg-blue-600 transition-colors"
        >
          {t("title")}
        </Link>
        <Link
          href={`/${locale}/kitchen`}
          className="block p-4 bg-green-500 text-white rounded hover:bg-green-600 transition-colors"
        >
          Kitchen
        </Link>
      </nav>
      <div className="mt-8 flex gap-4">
        <Link
          href="/en"
          className={`px-3 py-1 rounded ${
            locale === "en" ? "bg-blue-500 text-white" : "bg-gray-200"
          }`}
        >
          English
        </Link>
        <Link
          href="/fr"
          className={`px-3 py-1 rounded ${
            locale === "fr" ? "bg-blue-500 text-white" : "bg-gray-200"
          }`}
        >
          Francais
        </Link>
      </div>
    </main>
  );
}
