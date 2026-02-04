'use client';

import { useTranslations } from 'next-intl';
import Link from 'next/link';
import { useLocale } from 'next-intl';
import { LocaleSwitcher } from '@/components/ui/LocaleSwitcher';

export function Hero() {
  const t = useTranslations('landing.hero');
  const locale = useLocale();

  return (
    <section className="relative min-h-[600px] flex items-center justify-center overflow-hidden">
      {/* Background Gradient */}
      <div className="absolute inset-0 bg-gradient-to-br from-emerald-600 via-teal-500 to-emerald-400">
        {/* Decorative circles */}
        <div className="absolute inset-0 opacity-20">
          <div className="absolute top-20 left-10 w-64 h-64 border-2 border-white/30 rounded-full" />
          <div className="absolute top-40 right-20 w-48 h-48 border-2 border-white/30 rounded-full" />
          <div className="absolute bottom-20 left-1/4 w-32 h-32 border-2 border-white/30 rounded-full" />
          <div className="absolute bottom-10 right-1/3 w-56 h-56 border-2 border-white/30 rounded-full" />
          <div className="absolute top-1/2 left-1/2 w-72 h-72 border-2 border-white/30 rounded-full -translate-x-1/2 -translate-y-1/2" />
        </div>
      </div>

      {/* Language Switcher */}
      <div className="absolute top-4 right-4 z-20">
        <LocaleSwitcher />
      </div>

      {/* Content */}
      <div className="relative z-10 max-w-4xl mx-auto px-4 text-center text-white">
        {/* Logo */}
        <div className="mb-8">
          <h2 className="text-2xl font-bold tracking-wide">RESTO360</h2>
        </div>

        {/* Headline */}
        <h1 className="text-4xl sm:text-5xl lg:text-6xl font-bold mb-6 leading-tight">
          {t('title')}
        </h1>

        {/* Subheadline */}
        <p className="text-lg sm:text-xl text-white/90 max-w-2xl mx-auto mb-10">
          {t('subtitle')}
        </p>

        {/* CTAs */}
        <div className="flex flex-col sm:flex-row gap-4 justify-center">
          <Link
            href={`/${locale}/register`}
            className="inline-flex items-center justify-center px-8 py-4 bg-white text-emerald-600 font-semibold rounded-xl shadow-lg hover:bg-gray-50 hover:shadow-xl transform hover:-translate-y-0.5 transition-all"
          >
            {t('cta_primary')}
            <svg className="w-5 h-5 ml-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
            </svg>
          </Link>
          <Link
            href={`/${locale}/menu/demo`}
            className="inline-flex items-center justify-center px-8 py-4 bg-white/10 text-white font-semibold rounded-xl border-2 border-white/30 hover:bg-white/20 transition-all"
          >
            {t('cta_secondary')}
            <svg className="w-5 h-5 ml-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
            </svg>
          </Link>
        </div>

        {/* Trust indicator */}
        <p className="mt-10 text-sm text-white/70">
          Pas de carte de credit requise
        </p>
      </div>

      {/* Bottom wave */}
      <div className="absolute bottom-0 left-0 right-0">
        <svg viewBox="0 0 1440 120" fill="none" xmlns="http://www.w3.org/2000/svg" className="w-full">
          <path d="M0 120L60 110C120 100 240 80 360 70C480 60 600 60 720 65C840 70 960 80 1080 85C1200 90 1320 90 1380 90L1440 90V120H1380C1320 120 1200 120 1080 120C960 120 840 120 720 120C600 120 480 120 360 120C240 120 120 120 60 120H0Z" fill="white"/>
        </svg>
      </div>
    </section>
  );
}
