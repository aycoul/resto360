'use client';

import { useTranslations } from 'next-intl';
import Link from 'next/link';
import { useLocale } from 'next-intl';

export function Pricing() {
  const t = useTranslations('landing.pricing');
  const locale = useLocale();

  const freeFeatures = t.raw('free_features') as string[];
  const proFeatures = t.raw('pro_features') as string[];

  return (
    <section className="py-20 bg-gray-50">
      <div className="max-w-5xl mx-auto px-4">
        {/* Section Header */}
        <div className="text-center mb-16">
          <h2 className="text-3xl sm:text-4xl font-bold text-gray-900 mb-4">
            {t('title')}
          </h2>
          <div className="w-20 h-1 bg-emerald-500 mx-auto rounded-full" />
        </div>

        {/* Pricing Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8 max-w-4xl mx-auto">
          {/* Free Tier */}
          <div className="bg-white rounded-2xl shadow-lg p-8 border-2 border-gray-100">
            <div className="text-center mb-8">
              <h3 className="text-2xl font-bold text-gray-900 mb-2">
                {t('free_tier')}
              </h3>
              <div className="flex items-baseline justify-center">
                <span className="text-5xl font-bold text-gray-900">0</span>
                <span className="text-xl text-gray-500 ml-1">XOF</span>
              </div>
              <p className="text-gray-500 mt-2">{t('per_month')}</p>
            </div>

            {/* Features List */}
            <ul className="space-y-4 mb-8">
              {freeFeatures.map((feature: string, index: number) => (
                <li key={index} className="flex items-start gap-3">
                  <svg className="w-5 h-5 text-emerald-500 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                  </svg>
                  <span className="text-gray-600">{feature}</span>
                </li>
              ))}
            </ul>

            {/* CTA */}
            <Link
              href={`/${locale}/register`}
              className="block w-full py-4 text-center bg-emerald-500 text-white font-semibold rounded-xl hover:bg-emerald-600 transition-colors"
            >
              {t('start_free')}
            </Link>
          </div>

          {/* Pro Tier */}
          <div className="bg-white rounded-2xl shadow-xl p-8 border-2 border-emerald-500 relative">
            {/* Popular Badge */}
            <div className="absolute -top-4 left-1/2 -translate-x-1/2">
              <span className="bg-emerald-500 text-white text-sm font-semibold px-4 py-1 rounded-full">
                Populaire
              </span>
            </div>

            <div className="text-center mb-8">
              <h3 className="text-2xl font-bold text-gray-900 mb-2">
                {t('pro_tier')}
              </h3>
              <div className="flex items-baseline justify-center">
                <span className="text-5xl font-bold text-emerald-600">6,000</span>
                <span className="text-xl text-gray-500 ml-1">XOF</span>
              </div>
              <p className="text-gray-500 mt-2">{t('per_month')}</p>
            </div>

            {/* Features List */}
            <ul className="space-y-4 mb-8">
              {proFeatures.map((feature: string, index: number) => (
                <li key={index} className="flex items-start gap-3">
                  <svg className="w-5 h-5 text-emerald-500 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                  </svg>
                  <span className="text-gray-600">{feature}</span>
                </li>
              ))}
            </ul>

            {/* CTA */}
            <Link
              href={`/${locale}/register?plan=pro`}
              className="block w-full py-4 text-center bg-emerald-600 text-white font-semibold rounded-xl hover:bg-emerald-700 transition-colors shadow-lg hover:shadow-xl"
            >
              {t('go_pro')}
            </Link>
          </div>
        </div>

        {/* Full Platform Note */}
        <div className="mt-12 text-center">
          <p className="text-gray-500 text-sm max-w-2xl mx-auto bg-white rounded-xl p-4 shadow-sm">
            {t('full_platform_note')}
          </p>
        </div>
      </div>
    </section>
  );
}
