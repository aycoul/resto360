'use client';

import { useTranslations } from 'next-intl';

export function AboutPageContent() {
  const t = useTranslations('marketing.about');

  return (
    <div className="py-20">
      {/* Hero Section */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center mb-16">
        <h1 className="text-4xl sm:text-5xl font-bold text-gray-900 mb-6">
          {t('title')}
        </h1>
      </div>

      {/* Mission Section */}
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 mb-20">
        <div className="bg-gradient-to-br from-emerald-600 to-teal-500 rounded-3xl p-12 text-white text-center">
          <h2 className="text-3xl font-bold mb-6">{t('mission.title')}</h2>
          <p className="text-xl text-white/90 leading-relaxed">
            {t('mission.description')}
          </p>
        </div>
      </div>

      {/* Story Section */}
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 mb-20">
        <h2 className="text-3xl font-bold text-gray-900 mb-6 text-center">
          {t('story.title')}
        </h2>
        <p className="text-lg text-gray-600 leading-relaxed text-center">
          {t('story.description')}
        </p>
      </div>

      {/* Values Section */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <h2 className="text-3xl font-bold text-gray-900 mb-12 text-center">
          {t('values.title')}
        </h2>
        <div className="grid md:grid-cols-3 gap-8">
          {/* Offline First */}
          <div className="bg-white rounded-2xl p-8 border border-gray-200 text-center hover:shadow-lg transition-shadow">
            <div className="w-16 h-16 bg-emerald-100 rounded-2xl flex items-center justify-center mx-auto mb-6">
              <svg className="w-8 h-8 text-emerald-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M18.364 5.636a9 9 0 010 12.728m0 0l-2.829-2.829m2.829 2.829L21 21M15.536 8.464a5 5 0 010 7.072m0 0l-2.829-2.829m-4.243 2.829a4.978 4.978 0 01-1.414-2.83m-1.414 5.658a9 9 0 01-2.167-9.238m7.824 2.167a1 1 0 111.414 1.414m-1.414-1.414L3 3m8.293 8.293l1.414 1.414" />
              </svg>
            </div>
            <h3 className="text-xl font-bold text-gray-900 mb-3">
              {t('values.offline.title')}
            </h3>
            <p className="text-gray-600">
              {t('values.offline.description')}
            </p>
          </div>

          {/* Local First */}
          <div className="bg-white rounded-2xl p-8 border border-gray-200 text-center hover:shadow-lg transition-shadow">
            <div className="w-16 h-16 bg-teal-100 rounded-2xl flex items-center justify-center mx-auto mb-6">
              <svg className="w-8 h-8 text-teal-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3.055 11H5a2 2 0 012 2v1a2 2 0 002 2 2 2 0 012 2v2.945M8 3.935V5.5A2.5 2.5 0 0010.5 8h.5a2 2 0 012 2 2 2 0 104 0 2 2 0 012-2h1.064M15 20.488V18a2 2 0 012-2h3.064M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <h3 className="text-xl font-bold text-gray-900 mb-3">
              {t('values.local.title')}
            </h3>
            <p className="text-gray-600">
              {t('values.local.description')}
            </p>
          </div>

          {/* Simple First */}
          <div className="bg-white rounded-2xl p-8 border border-gray-200 text-center hover:shadow-lg transition-shadow">
            <div className="w-16 h-16 bg-blue-100 rounded-2xl flex items-center justify-center mx-auto mb-6">
              <svg className="w-8 h-8 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
            </div>
            <h3 className="text-xl font-bold text-gray-900 mb-3">
              {t('values.simple.title')}
            </h3>
            <p className="text-gray-600">
              {t('values.simple.description')}
            </p>
          </div>
        </div>
      </div>

      {/* Team Section (Optional) */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 mt-20">
        <h2 className="text-3xl font-bold text-gray-900 mb-12 text-center">
          Our Focus Markets
        </h2>
        <div className="grid grid-cols-2 md:grid-cols-5 gap-8">
          {[
            { country: "Côte d'Ivoire", flag: '🇨🇮', city: 'Abidjan' },
            { country: 'Ghana', flag: '🇬🇭', city: 'Accra' },
            { country: 'Nigeria', flag: '🇳🇬', city: 'Lagos' },
            { country: 'Senegal', flag: '🇸🇳', city: 'Dakar' },
            { country: 'Cameroon', flag: '🇨🇲', city: 'Douala' },
          ].map((market) => (
            <div key={market.country} className="text-center">
              <div className="text-5xl mb-3">{market.flag}</div>
              <h3 className="font-semibold text-gray-900">{market.country}</h3>
              <p className="text-sm text-gray-500">{market.city}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
