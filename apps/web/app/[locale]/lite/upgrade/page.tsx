'use client';

import { useState } from 'react';
import { useLocale, useTranslations } from 'next-intl';
import Link from 'next/link';
import { useLiteContext } from '../layout';

export default function UpgradePage() {
  const locale = useLocale();
  const t = useTranslations('lite.upgradePage');
  const { restaurant } = useLiteContext();
  const [email, setEmail] = useState('');
  const [submitted, setSubmitted] = useState(false);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    // For now, just mark as submitted - no backend integration yet
    setSubmitted(true);
    // TODO: Send to backend when payment processing is implemented
    console.log('Upgrade interest captured:', { email, restaurant: restaurant?.name });
  };

  const tiers = [
    {
      name: t('tiers.free.name'),
      price: '0',
      period: '',
      description: t('tiers.free.description'),
      features: [
        t('tiers.free.features.items'),
        t('tiers.free.features.qr'),
        t('tiers.free.features.analytics'),
        t('tiers.free.features.branding'),
      ],
      cta: t('tiers.free.cta'),
      current: restaurant?.plan_type === 'free',
      highlighted: false,
    },
    {
      name: t('tiers.pro.name'),
      price: '6000',
      period: t('perMonth'),
      description: t('tiers.pro.description'),
      features: [
        t('tiers.pro.features.everything'),
        t('tiers.pro.features.noBranding'),
        t('tiers.pro.features.colors'),
        t('tiers.pro.features.logo'),
        t('tiers.pro.features.priority'),
      ],
      cta: t('tiers.pro.cta'),
      current: restaurant?.plan_type === 'pro',
      highlighted: true,
    },
    {
      name: t('tiers.full.name'),
      price: t('tiers.full.price'),
      period: '',
      description: t('tiers.full.description'),
      features: [
        t('tiers.full.features.everything'),
        t('tiers.full.features.pos'),
        t('tiers.full.features.payments'),
        t('tiers.full.features.delivery'),
        t('tiers.full.features.inventory'),
        t('tiers.full.features.support'),
      ],
      cta: t('tiers.full.cta'),
      current: restaurant?.plan_type === 'full',
      highlighted: false,
    },
  ];

  return (
    <div className="max-w-6xl mx-auto">
      {/* Header */}
      <div className="text-center mb-10">
        <h1 className="text-3xl font-bold text-gray-900 mb-3">
          {t('title')}
        </h1>
        <p className="text-gray-600 max-w-2xl mx-auto">
          {t('subtitle')}
        </p>
      </div>

      {/* Pricing Grid */}
      <div className="grid md:grid-cols-3 gap-6 mb-12">
        {tiers.map((tier, index) => (
          <div
            key={index}
            className={`relative rounded-2xl p-6 ${
              tier.highlighted
                ? 'bg-emerald-600 text-white ring-4 ring-emerald-600 ring-offset-2'
                : 'bg-white border border-gray-200'
            }`}
          >
            {tier.highlighted && (
              <span className="absolute -top-3 left-1/2 -translate-x-1/2 bg-emerald-800 text-white text-xs font-semibold px-3 py-1 rounded-full">
                {t('popular')}
              </span>
            )}

            <div className="mb-6">
              <h3 className={`text-xl font-bold ${tier.highlighted ? 'text-white' : 'text-gray-900'}`}>
                {tier.name}
              </h3>
              <p className={`text-sm mt-1 ${tier.highlighted ? 'text-emerald-100' : 'text-gray-500'}`}>
                {tier.description}
              </p>
            </div>

            <div className="mb-6">
              <span className={`text-4xl font-bold ${tier.highlighted ? 'text-white' : 'text-gray-900'}`}>
                {tier.price === '0' ? t('free') : `${tier.price} XOF`}
              </span>
              {tier.period && (
                <span className={tier.highlighted ? 'text-emerald-100' : 'text-gray-500'}>
                  {tier.period}
                </span>
              )}
            </div>

            <ul className="space-y-3 mb-6">
              {tier.features.map((feature, featureIndex) => (
                <li key={featureIndex} className="flex items-start gap-2">
                  <svg
                    className={`w-5 h-5 mt-0.5 flex-shrink-0 ${
                      tier.highlighted ? 'text-emerald-200' : 'text-emerald-600'
                    }`}
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M5 13l4 4L19 7"
                    />
                  </svg>
                  <span className={`text-sm ${tier.highlighted ? 'text-white' : 'text-gray-600'}`}>
                    {feature}
                  </span>
                </li>
              ))}
            </ul>

            {tier.current ? (
              <button
                disabled
                className={`w-full py-3 rounded-lg font-semibold ${
                  tier.highlighted
                    ? 'bg-white/20 text-white cursor-not-allowed'
                    : 'bg-gray-100 text-gray-400 cursor-not-allowed'
                }`}
              >
                {t('currentPlan')}
              </button>
            ) : tier.name === t('tiers.full.name') ? (
              <Link
                href={`/${locale}/contact`}
                className={`block w-full py-3 rounded-lg font-semibold text-center ${
                  tier.highlighted
                    ? 'bg-white text-emerald-600 hover:bg-emerald-50'
                    : 'bg-emerald-600 text-white hover:bg-emerald-700'
                }`}
              >
                {tier.cta}
              </Link>
            ) : tier.name === t('tiers.pro.name') && !tier.current ? (
              <button
                disabled
                className="w-full py-3 rounded-lg font-semibold bg-white/90 text-emerald-600"
              >
                {t('comingSoon')}
              </button>
            ) : (
              <Link
                href={`/${locale}/lite/dashboard`}
                className={`block w-full py-3 rounded-lg font-semibold text-center ${
                  tier.highlighted
                    ? 'bg-white text-emerald-600 hover:bg-emerald-50'
                    : 'bg-emerald-600 text-white hover:bg-emerald-700'
                }`}
              >
                {tier.cta}
              </Link>
            )}
          </div>
        ))}
      </div>

      {/* Feature Comparison Table */}
      <div className="bg-white rounded-2xl border border-gray-200 overflow-hidden mb-12">
        <div className="p-6 border-b border-gray-200">
          <h2 className="text-xl font-bold text-gray-900">{t('comparison.title')}</h2>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-gray-200">
                <th className="text-left p-4 font-semibold text-gray-900">{t('comparison.feature')}</th>
                <th className="text-center p-4 font-semibold text-gray-900">{t('tiers.free.name')}</th>
                <th className="text-center p-4 font-semibold text-emerald-600">{t('tiers.pro.name')}</th>
                <th className="text-center p-4 font-semibold text-gray-900">{t('tiers.full.name')}</th>
              </tr>
            </thead>
            <tbody>
              {[
                { feature: t('comparison.features.menuItems'), free: t('unlimited'), pro: t('unlimited'), full: t('unlimited') },
                { feature: t('comparison.features.qrCode'), free: true, pro: true, full: true },
                { feature: t('comparison.features.basicAnalytics'), free: true, pro: true, full: true },
                { feature: t('comparison.features.customBranding'), free: false, pro: true, full: true },
                { feature: t('comparison.features.customColors'), free: false, pro: true, full: true },
                { feature: t('comparison.features.logoUpload'), free: false, pro: true, full: true },
                { feature: t('comparison.features.pos'), free: false, pro: false, full: true },
                { feature: t('comparison.features.mobilePayments'), free: false, pro: false, full: true },
                { feature: t('comparison.features.deliveryManagement'), free: false, pro: false, full: true },
                { feature: t('comparison.features.inventory'), free: false, pro: false, full: true },
                { feature: t('comparison.features.support'), free: t('comparison.community'), pro: t('comparison.priority'), full: t('comparison.dedicated') },
              ].map((row, index) => (
                <tr key={index} className="border-b border-gray-100 last:border-b-0">
                  <td className="p-4 text-gray-700">{row.feature}</td>
                  <td className="p-4 text-center">
                    {typeof row.free === 'boolean' ? (
                      row.free ? (
                        <svg className="w-5 h-5 mx-auto text-emerald-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                        </svg>
                      ) : (
                        <svg className="w-5 h-5 mx-auto text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                        </svg>
                      )
                    ) : (
                      <span className="text-gray-600">{row.free}</span>
                    )}
                  </td>
                  <td className="p-4 text-center bg-emerald-50/50">
                    {typeof row.pro === 'boolean' ? (
                      row.pro ? (
                        <svg className="w-5 h-5 mx-auto text-emerald-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                        </svg>
                      ) : (
                        <svg className="w-5 h-5 mx-auto text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                        </svg>
                      )
                    ) : (
                      <span className="text-emerald-700 font-medium">{row.pro}</span>
                    )}
                  </td>
                  <td className="p-4 text-center">
                    {typeof row.full === 'boolean' ? (
                      row.full ? (
                        <svg className="w-5 h-5 mx-auto text-emerald-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                        </svg>
                      ) : (
                        <svg className="w-5 h-5 mx-auto text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                        </svg>
                      )
                    ) : (
                      <span className="text-gray-600">{row.full}</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Upgrade Interest Form */}
      {restaurant?.plan_type === 'free' && (
        <div className="bg-gradient-to-r from-emerald-600 to-emerald-700 rounded-2xl p-8 text-white">
          <div className="max-w-2xl mx-auto text-center">
            <h2 className="text-2xl font-bold mb-3">{t('interest.title')}</h2>
            <p className="text-emerald-100 mb-6">{t('interest.subtitle')}</p>

            {submitted ? (
              <div className="bg-white/10 rounded-lg p-4">
                <svg className="w-12 h-12 mx-auto text-emerald-200 mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <p className="font-semibold">{t('interest.thanks')}</p>
                <p className="text-emerald-100 text-sm mt-1">{t('interest.weWillContact')}</p>
              </div>
            ) : (
              <form onSubmit={handleSubmit} className="flex flex-col sm:flex-row gap-3 max-w-md mx-auto">
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder={t('interest.emailPlaceholder')}
                  required
                  className="flex-1 px-4 py-3 rounded-lg text-gray-900 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-emerald-300"
                />
                <button
                  type="submit"
                  className="px-6 py-3 bg-white text-emerald-600 rounded-lg font-semibold hover:bg-emerald-50 transition-colors"
                >
                  {t('interest.notify')}
                </button>
              </form>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
