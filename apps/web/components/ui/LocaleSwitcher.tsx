"use client";

import { useLocale } from "next-intl";
import { useRouter, usePathname } from "next/navigation";

export function LocaleSwitcher() {
  const locale = useLocale();
  const router = useRouter();
  const pathname = usePathname();

  const switchLocale = (newLocale: string) => {
    const newPath = pathname.replace(`/${locale}`, `/${newLocale}`);
    router.push(newPath);
  };

  return (
    <div className="flex gap-2">
      <button
        onClick={() => switchLocale("fr")}
        className={`px-2 py-1 rounded ${
          locale === "fr" ? "bg-blue-500 text-white" : "bg-gray-200"
        }`}
      >
        FR
      </button>
      <button
        onClick={() => switchLocale("en")}
        className={`px-2 py-1 rounded ${
          locale === "en" ? "bg-blue-500 text-white" : "bg-gray-200"
        }`}
      >
        EN
      </button>
    </div>
  );
}
