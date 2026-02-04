'use client';

import { useTranslations, useLocale } from 'next-intl';
import Link from 'next/link';

const useCaseTypes = [
  {
    id: 'restaurant',
    emoji: '🍽️',
    color: 'emerald',
  },
  {
    id: 'cafe',
    emoji: '☕',
    color: 'amber',
  },
  {
    id: 'hotel',
    emoji: '🏨',
    color: 'blue',
  },
  {
    id: 'foodtruck',
    emoji: '🚚',
    color: 'orange',
  },
  {
    id: 'darkKitchen',
    emoji: '🥡',
    color: 'purple',
  },
  {
    id: 'catering',
    emoji: '🎉',
    color: 'pink',
  },
];

const colorClasses: Record<string, { bg: string; border: string; light: string; text: string }> = {
  emerald: { bg: 'bg-emerald-600', border: 'border-emerald-200', light: 'bg-emerald-50', text: 'text-emerald-600' },
  amber: { bg: 'bg-amber-600', border: 'border-amber-200', light: 'bg-amber-50', text: 'text-amber-600' },
  blue: { bg: 'bg-blue-600', border: 'border-blue-200', light: 'bg-blue-50', text: 'text-blue-600' },
  orange: { bg: 'bg-orange-600', border: 'border-orange-200', light: 'bg-orange-50', text: 'text-orange-600' },
  purple: { bg: 'bg-purple-600', border: 'border-purple-200', light: 'bg-purple-50', text: 'text-purple-600' },
  pink: { bg: 'bg-pink-600', border: 'border-pink-200', light: 'bg-pink-50', text: 'text-pink-600' },
};

export function UseCasesPageContent() {
  const t = useTranslations('marketing.use_cases');
  const locale = useLocale();

  return (
    <div className="py-20">
      {/* Hero Section */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center mb-16">
        <h1 className="text-4xl sm:text-5xl font-bold text-gray-900 mb-6">
          {t('title')}
        </h1>
        <p className="text-xl text-gray-600 max-w-3xl mx-auto">
          {t('subtitle')}
        </p>
      </div>

      {/* Use Cases Grid */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-16">
        {useCaseTypes.map((useCase, index) => {
          const colors = colorClasses[useCase.color];
          const isReversed = index % 2 === 1;
          const benefits = t.raw(`types.${useCase.id}.benefits`) as string[];

          return (
            <div
              key={useCase.id}
              className={`grid lg:grid-cols-2 gap-12 items-center ${isReversed ? 'lg:flex-row-reverse' : ''}`}
            >
              {/* Content */}
              <div className={isReversed ? 'lg:order-2' : ''}>
                <div className="flex items-center gap-4 mb-4">
                  <span className="text-5xl">{useCase.emoji}</span>
                  <div>
                    <h2 className="text-2xl font-bold text-gray-900">
                      {t(`types.${useCase.id}.title`)}
                    </h2>
                    <p className={`${colors.text} font-medium`}>
                      {t(`types.${useCase.id}.subtitle`)}
                    </p>
                  </div>
                </div>

                <p className="text-gray-600 mb-6 leading-relaxed">
                  {t(`types.${useCase.id}.description`)}
                </p>

                {/* Benefits */}
                <ul className="space-y-3 mb-8">
                  {benefits.map((benefit: string, idx: number) => (
                    <li key={idx} className="flex items-start gap-3">
                      <svg className={`w-5 h-5 ${colors.text} mt-0.5 flex-shrink-0`} fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                      </svg>
                      <span className="text-gray-600">{benefit}</span>
                    </li>
                  ))}
                </ul>

                <Link
                  href={`/${locale}/register`}
                  className={`inline-flex items-center justify-center px-6 py-3 ${colors.bg} text-white font-semibold rounded-xl hover:opacity-90 transition-opacity`}
                >
                  Get Started
                  <svg className="w-5 h-5 ml-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
                  </svg>
                </Link>
              </div>

              {/* Testimonial Card */}
              <div className={`${colors.light} rounded-2xl p-8 ${isReversed ? 'lg:order-1' : ''}`}>
                <div className="bg-white rounded-xl p-6 shadow-sm">
                  {/* Quote */}
                  <svg className={`w-10 h-10 ${colors.text} mb-4 opacity-50`} fill="currentColor" viewBox="0 0 24 24">
                    <path d="M14.017 21v-7.391c0-5.704 3.731-9.57 8.983-10.609l.995 2.151c-2.432.917-3.995 3.638-3.995 5.849h4v10h-9.983zm-14.017 0v-7.391c0-5.704 3.748-9.57 9-10.609l.996 2.151c-2.433.917-3.996 3.638-3.996 5.849h3.983v10h-9.983z" />
                  </svg>

                  <p className="text-gray-700 text-lg mb-6 leading-relaxed">
                    "{t(`types.${useCase.id}.quote`)}"
                  </p>

                  <div className="flex items-center gap-4">
                    <div className={`w-12 h-12 ${colors.bg} rounded-full flex items-center justify-center text-white font-bold`}>
                      {t(`types.${useCase.id}.quoteAuthor`).split(' ').map((n: string) => n[0]).join('')}
                    </div>
                    <div>
                      <p className="font-semibold text-gray-900">
                        {t(`types.${useCase.id}.quoteAuthor`)}
                      </p>
                      <p className="text-sm text-gray-500">
                        {t(`types.${useCase.id}.quoteRole`)}
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
