'use client';

import { useTranslations, useLocale } from 'next-intl';
import Link from 'next/link';
import { useState } from 'react';

const tiers = ['starter', 'essential', 'pro', 'enterprise'] as const;

export function PricingPageContent() {
  const t = useTranslations('marketing.pricing_page');
  const locale = useLocale();
  const [billingPeriod, setBillingPeriod] = useState<'monthly' | 'yearly'>('monthly');

  return (
    <div className="py-20">
      {/* Hero Section */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center mb-16">
        <h1 className="text-4xl sm:text-5xl font-bold text-gray-900 mb-6">
          {t('title')}
        </h1>
        <p className="text-xl text-gray-600 max-w-3xl mx-auto mb-10">
          {t('subtitle')}
        </p>

        {/* Billing Toggle */}
        <div className="inline-flex items-center gap-4 bg-gray-100 rounded-xl p-1">
          <button
            onClick={() => setBillingPeriod('monthly')}
            className={`px-6 py-2 rounded-lg font-medium transition-all ${
              billingPeriod === 'monthly'
                ? 'bg-white text-gray-900 shadow-sm'
                : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            {t('monthly')}
          </button>
          <button
            onClick={() => setBillingPeriod('yearly')}
            className={`px-6 py-2 rounded-lg font-medium transition-all flex items-center gap-2 ${
              billingPeriod === 'yearly'
                ? 'bg-white text-gray-900 shadow-sm'
                : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            {t('yearly')}
            <span className="bg-emerald-100 text-emerald-700 text-xs px-2 py-0.5 rounded-full">
              {t('save')}
            </span>
          </button>
        </div>
      </div>

      {/* Pricing Cards */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 mb-20">
        <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-8">
          {tiers.map((tier) => {
            const isPopular = t.raw(`tiers.${tier}.popular`) === true;
            const price = billingPeriod === 'yearly'
              ? t(`tiers.${tier}.priceYearly`)
              : t(`tiers.${tier}.price`);
            const features = t.raw(`tiers.${tier}.features`) as string[];

            return (
              <div
                key={tier}
                className={`relative bg-white rounded-2xl p-8 ${
                  isPopular
                    ? 'border-2 border-emerald-500 shadow-xl'
                    : 'border border-gray-200 shadow-sm'
                }`}
              >
                {/* Popular Badge */}
                {isPopular && (
                  <div className="absolute -top-4 left-1/2 -translate-x-1/2">
                    <span className="bg-emerald-500 text-white text-sm font-semibold px-4 py-1 rounded-full">
                      {t('tiers.essential.popular') ? 'Most Popular' : ''}
                    </span>
                  </div>
                )}

                {/* Tier Name */}
                <h3 className="text-xl font-bold text-gray-900 mb-2">
                  {t(`tiers.${tier}.name`)}
                </h3>
                <p className="text-gray-500 text-sm mb-6">
                  {t(`tiers.${tier}.description`)}
                </p>

                {/* Price */}
                <div className="mb-6">
                  {price === 'Custom' || price === 'Sur mesure' ? (
                    <span className="text-3xl font-bold text-gray-900">{price}</span>
                  ) : (
                    <div className="flex items-baseline">
                      <span className="text-4xl font-bold text-gray-900">${price}</span>
                      {price !== '0' && (
                        <span className="text-gray-500 ml-2">
                          /{billingPeriod === 'yearly' ? 'year' : 'month'}
                        </span>
                      )}
                    </div>
                  )}
                </div>

                {/* CTA */}
                <Link
                  href={tier === 'enterprise' ? `/${locale}/contact` : `/${locale}/register${tier !== 'starter' ? `?plan=${tier}` : ''}`}
                  className={`block w-full py-3 text-center font-semibold rounded-xl transition-colors mb-8 ${
                    isPopular
                      ? 'bg-emerald-600 text-white hover:bg-emerald-700'
                      : tier === 'enterprise'
                      ? 'bg-gray-900 text-white hover:bg-gray-800'
                      : 'bg-gray-100 text-gray-900 hover:bg-gray-200'
                  }`}
                >
                  {t(`tiers.${tier}.cta`)}
                </Link>

                {/* Features */}
                <ul className="space-y-3">
                  {features.map((feature: string, index: number) => (
                    <li key={index} className="flex items-start gap-3">
                      <svg className="w-5 h-5 text-emerald-500 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                      </svg>
                      <span className="text-gray-600 text-sm">{feature}</span>
                    </li>
                  ))}
                </ul>
              </div>
            );
          })}
        </div>
      </div>

      {/* FAQ Section */}
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        <h2 className="text-3xl font-bold text-gray-900 text-center mb-12">
          {t('faq.title')}
        </h2>
        <div className="space-y-6">
          {['trial', 'cancel', 'payment', 'upgrade', 'currency'].map((faqKey) => (
            <div key={faqKey} className="bg-white rounded-xl p-6 border border-gray-200">
              <h3 className="text-lg font-semibold text-gray-900 mb-2">
                {t(`faq.questions.${faqKey}.q`)}
              </h3>
              <p className="text-gray-600">
                {t(`faq.questions.${faqKey}.a`)}
              </p>
            </div>
          ))}
        </div>
      </div>

      {/* Bottom CTA */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 mt-20">
        <div className="bg-gradient-to-r from-emerald-600 to-teal-500 rounded-3xl p-12 text-center text-white">
          <h2 className="text-3xl font-bold mb-4">Still have questions?</h2>
          <p className="text-white/90 mb-8 max-w-2xl mx-auto">
            Our team is here to help you find the perfect plan for your restaurant.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link
              href={`/${locale}/contact`}
              className="inline-flex items-center justify-center px-8 py-3 bg-white text-emerald-600 font-semibold rounded-xl hover:bg-gray-50 transition-colors"
            >
              Contact Sales
            </Link>
            <Link
              href={`/${locale}/menu/demo`}
              className="inline-flex items-center justify-center px-8 py-3 bg-white/10 text-white font-semibold rounded-xl border-2 border-white/30 hover:bg-white/20 transition-colors"
            >
              Try Demo Menu
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
