'use client';

import { useTranslations } from 'next-intl';

const paymentProviders = [
  {
    name: 'Wave',
    logo: '🌊',
    description: 'Mobile money',
    available: true,
  },
  {
    name: 'Orange Money',
    logo: '🍊',
    description: 'Mobile money',
    available: true,
  },
  {
    name: 'MTN MoMo',
    logo: '💛',
    description: 'Mobile money',
    available: true,
  },
  {
    name: 'Flutterwave',
    logo: '🦋',
    description: 'Cards & transfers',
    available: true,
  },
  {
    name: 'Paystack',
    logo: '💳',
    description: 'Cards & transfers',
    available: true,
  },
  {
    name: 'CinetPay',
    logo: '🎬',
    description: 'Mobile money',
    available: true,
  },
];

const comingSoon = [
  { name: 'Google Business', logo: '📍' },
  { name: 'Meta Pixel', logo: '📊' },
  { name: 'Google Analytics', logo: '📈' },
  { name: 'Zapier', logo: '⚡' },
];

export function IntegrationsSection() {
  const t = useTranslations('marketing.integrations');

  return (
    <section className="py-20 bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Section Header */}
        <div className="text-center mb-16">
          <h2 className="text-3xl sm:text-4xl font-bold text-gray-900 mb-4">
            {t('title')}
          </h2>
          <p className="text-lg text-gray-600 max-w-2xl mx-auto">
            {t('subtitle')}
          </p>
        </div>

        {/* Payment Providers */}
        <div className="mb-16">
          <h3 className="text-xl font-semibold text-gray-900 mb-6 text-center">
            {t('payments')}
          </h3>
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
            {paymentProviders.map((provider) => (
              <div
                key={provider.name}
                className="bg-white rounded-xl p-6 text-center border border-gray-200 hover:border-emerald-300 hover:shadow-md transition-all"
              >
                <div className="text-4xl mb-3">{provider.logo}</div>
                <h4 className="font-semibold text-gray-900">{provider.name}</h4>
                <p className="text-sm text-gray-500">{provider.description}</p>
                {provider.available && (
                  <span className="inline-flex items-center mt-2 text-xs text-emerald-600 bg-emerald-50 px-2 py-1 rounded-full">
                    <svg className="w-3 h-3 mr-1" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                    </svg>
                    Available
                  </span>
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Coming Soon */}
        <div>
          <h3 className="text-xl font-semibold text-gray-900 mb-6 text-center">
            {t('coming_soon')}
          </h3>
          <div className="flex flex-wrap justify-center gap-4">
            {comingSoon.map((integration) => (
              <div
                key={integration.name}
                className="bg-white rounded-xl px-6 py-4 border border-gray-200 flex items-center gap-3 opacity-60"
              >
                <span className="text-2xl">{integration.logo}</span>
                <span className="font-medium text-gray-600">{integration.name}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
