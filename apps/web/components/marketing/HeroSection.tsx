'use client';

import { useTranslations, useLocale } from 'next-intl';
import Link from 'next/link';
import Image from 'next/image';

export function HeroSection() {
  const t = useTranslations('marketing.hero');
  const locale = useLocale();

  return (
    <section className="relative min-h-screen flex items-center overflow-hidden pt-16">
      {/* Background */}
      <div className="absolute inset-0 bg-gradient-to-br from-emerald-600 via-teal-500 to-emerald-400">
        {/* Animated gradient orbs */}
        <div className="absolute inset-0 overflow-hidden">
          <div className="absolute -top-40 -right-40 w-80 h-80 bg-white/10 rounded-full blur-3xl animate-pulse" />
          <div className="absolute top-1/2 -left-20 w-60 h-60 bg-teal-300/20 rounded-full blur-3xl animate-pulse" style={{ animationDelay: '1s' }} />
          <div className="absolute -bottom-20 right-1/3 w-72 h-72 bg-emerald-300/20 rounded-full blur-3xl animate-pulse" style={{ animationDelay: '2s' }} />
        </div>

        {/* Grid pattern overlay */}
        <div className="absolute inset-0 bg-[url('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNjAiIGhlaWdodD0iNjAiIHZpZXdCb3g9IjAgMCA2MCA2MCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48ZyBmaWxsPSJub25lIiBmaWxsLXJ1bGU9ImV2ZW5vZGQiPjxnIGZpbGw9IiNmZmZmZmYiIGZpbGwtb3BhY2l0eT0iMC4wNSI+PHBhdGggZD0iTTM2IDM0djItSDI0di0yaDEyek0zNiAyNHYySDI0di0yaDEyeiIvPjwvZz48L2c+PC9zdmc+')] opacity-50" />
      </div>

      {/* Content */}
      <div className="relative z-10 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20">
        <div className="grid lg:grid-cols-2 gap-12 items-center">
          {/* Left Column - Text */}
          <div className="text-white">
            {/* Badge */}
            <div className="inline-flex items-center gap-2 bg-white/10 backdrop-blur-sm border border-white/20 rounded-full px-4 py-2 mb-6">
              <span className="w-2 h-2 bg-emerald-300 rounded-full animate-pulse" />
              <span className="text-sm font-medium">{t('badge')}</span>
            </div>

            {/* Headline */}
            <h1 className="text-4xl sm:text-5xl lg:text-6xl font-bold leading-tight mb-6">
              {t('title')}
            </h1>

            {/* Subheadline */}
            <p className="text-lg sm:text-xl text-white/90 max-w-xl mb-8 leading-relaxed">
              {t('subtitle')}
            </p>

            {/* CTAs */}
            <div className="flex flex-col sm:flex-row gap-4 mb-10">
              <Link
                href={`/${locale}/register`}
                className="inline-flex items-center justify-center px-8 py-4 bg-white text-emerald-600 font-semibold rounded-xl shadow-lg hover:bg-gray-50 hover:shadow-xl transform hover:-translate-y-0.5 transition-all group"
              >
                {t('cta_primary')}
                <svg className="w-5 h-5 ml-2 group-hover:translate-x-1 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
                </svg>
              </Link>
              <Link
                href={`/${locale}/menu/demo`}
                className="inline-flex items-center justify-center px-8 py-4 bg-white/10 text-white font-semibold rounded-xl border-2 border-white/30 hover:bg-white/20 backdrop-blur-sm transition-all group"
              >
                <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                {t('cta_secondary')}
              </Link>
            </div>

            {/* Stats */}
            <div className="grid grid-cols-3 gap-6 pt-8 border-t border-white/20">
              <div>
                <div className="text-3xl font-bold">{t('stats.restaurants')}</div>
                <div className="text-white/70 text-sm">{t('stats.restaurantsLabel')}</div>
              </div>
              <div>
                <div className="text-3xl font-bold">{t('stats.orders')}</div>
                <div className="text-white/70 text-sm">{t('stats.ordersLabel')}</div>
              </div>
              <div>
                <div className="text-3xl font-bold">{t('stats.countries')}</div>
                <div className="text-white/70 text-sm">{t('stats.countriesLabel')}</div>
              </div>
            </div>
          </div>

          {/* Right Column - Visual */}
          <div className="relative lg:pl-8">
            {/* Phone Mockup */}
            <div className="relative mx-auto w-72 sm:w-80">
              {/* Phone Frame */}
              <div className="relative bg-gray-900 rounded-[3rem] p-3 shadow-2xl">
                {/* Screen */}
                <div className="bg-white rounded-[2.5rem] overflow-hidden aspect-[9/19]">
                  {/* Status Bar */}
                  <div className="bg-gray-100 px-6 py-2 flex justify-between items-center">
                    <span className="text-xs text-gray-500">9:41</span>
                    <div className="flex items-center gap-1">
                      <svg className="w-4 h-4 text-gray-500" fill="currentColor" viewBox="0 0 24 24">
                        <path d="M12.01 21.49L23.64 7c-.45-.34-4.93-4-11.64-4C5.28 3 .81 6.66.36 7l11.63 14.49.01.01.01-.01z"/>
                      </svg>
                      <svg className="w-4 h-4 text-gray-500" fill="currentColor" viewBox="0 0 24 24">
                        <path d="M15.67 4H14V2h-4v2H8.33C7.6 4 7 4.6 7 5.33v15.33C7 21.4 7.6 22 8.33 22h7.33c.74 0 1.34-.6 1.34-1.33V5.33C17 4.6 16.4 4 15.67 4z"/>
                      </svg>
                    </div>
                  </div>

                  {/* Menu Preview */}
                  <div className="p-4">
                    {/* Restaurant Header */}
                    <div className="text-center mb-4">
                      <div className="w-12 h-12 bg-emerald-100 rounded-full mx-auto mb-2 flex items-center justify-center">
                        <span className="text-emerald-600 font-bold">R</span>
                      </div>
                      <h3 className="font-bold text-gray-900 text-sm">Chez Aminata</h3>
                      <p className="text-xs text-gray-500">Abidjan, Côte d'Ivoire</p>
                    </div>

                    {/* Categories */}
                    <div className="flex gap-2 mb-4 overflow-x-auto pb-2">
                      <span className="px-3 py-1 bg-emerald-500 text-white text-xs rounded-full whitespace-nowrap">Plats</span>
                      <span className="px-3 py-1 bg-gray-100 text-gray-600 text-xs rounded-full whitespace-nowrap">Boissons</span>
                      <span className="px-3 py-1 bg-gray-100 text-gray-600 text-xs rounded-full whitespace-nowrap">Desserts</span>
                    </div>

                    {/* Menu Items */}
                    <div className="space-y-3">
                      <div className="flex gap-3 p-2 bg-gray-50 rounded-lg">
                        <div className="w-14 h-14 bg-orange-100 rounded-lg flex items-center justify-center text-2xl">
                          🍛
                        </div>
                        <div className="flex-1">
                          <h4 className="font-medium text-gray-900 text-sm">Kédjenou</h4>
                          <p className="text-xs text-gray-500">Poulet mijoté</p>
                          <p className="text-sm font-bold text-emerald-600 mt-1">4,500 XOF</p>
                        </div>
                      </div>
                      <div className="flex gap-3 p-2 bg-gray-50 rounded-lg">
                        <div className="w-14 h-14 bg-yellow-100 rounded-lg flex items-center justify-center text-2xl">
                          🍌
                        </div>
                        <div className="flex-1">
                          <h4 className="font-medium text-gray-900 text-sm">Garba</h4>
                          <p className="text-xs text-gray-500">Attiéké au thon</p>
                          <p className="text-sm font-bold text-emerald-600 mt-1">1,500 XOF</p>
                        </div>
                      </div>
                      <div className="flex gap-3 p-2 bg-gray-50 rounded-lg">
                        <div className="w-14 h-14 bg-red-100 rounded-lg flex items-center justify-center text-2xl">
                          🍖
                        </div>
                        <div className="flex-1">
                          <h4 className="font-medium text-gray-900 text-sm">Sauce Graine</h4>
                          <p className="text-xs text-gray-500">Sauce de palme</p>
                          <p className="text-sm font-bold text-emerald-600 mt-1">5,000 XOF</p>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Notch */}
                <div className="absolute top-0 left-1/2 -translate-x-1/2 w-32 h-7 bg-gray-900 rounded-b-2xl" />
              </div>

              {/* Floating Elements */}
              <div className="absolute -left-16 top-20 bg-white rounded-xl shadow-xl p-3 animate-float">
                <div className="flex items-center gap-2">
                  <div className="w-8 h-8 bg-emerald-100 rounded-full flex items-center justify-center">
                    <svg className="w-4 h-4 text-emerald-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                  </div>
                  <div>
                    <p className="text-xs font-medium text-gray-900">New Order</p>
                    <p className="text-xs text-gray-500">#1234</p>
                  </div>
                </div>
              </div>

              <div className="absolute -right-12 top-40 bg-white rounded-xl shadow-xl p-3 animate-float" style={{ animationDelay: '1s' }}>
                <div className="flex items-center gap-2">
                  <div className="w-8 h-8 bg-orange-100 rounded-full flex items-center justify-center">
                    <svg className="w-4 h-4 text-orange-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v1m6 11h2m-6 0h-2v4m0-11v3m0 0h.01M12 12h4.01M16 20h4M4 12h4m12 0h.01M5 8h2a1 1 0 001-1V5a1 1 0 00-1-1H5a1 1 0 00-1 1v2a1 1 0 001 1zm12 0h2a1 1 0 001-1V5a1 1 0 00-1-1h-2a1 1 0 00-1 1v2a1 1 0 001 1zM5 20h2a1 1 0 001-1v-2a1 1 0 00-1-1H5a1 1 0 00-1 1v2a1 1 0 001 1z" />
                    </svg>
                  </div>
                  <div>
                    <p className="text-xs font-medium text-gray-900">QR Scanned</p>
                    <p className="text-xs text-gray-500">+1 view</p>
                  </div>
                </div>
              </div>

              <div className="absolute -right-8 bottom-20 bg-white rounded-xl shadow-xl p-3 animate-float" style={{ animationDelay: '2s' }}>
                <div className="flex items-center gap-2">
                  <div className="w-8 h-8 bg-teal-100 rounded-full flex items-center justify-center">
                    <span className="text-sm">💰</span>
                  </div>
                  <div>
                    <p className="text-xs font-medium text-gray-900">Payment</p>
                    <p className="text-xs text-emerald-600 font-semibold">+7,500 XOF</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Bottom wave */}
      <div className="absolute bottom-0 left-0 right-0">
        <svg viewBox="0 0 1440 120" fill="none" xmlns="http://www.w3.org/2000/svg" className="w-full">
          <path d="M0 120L60 110C120 100 240 80 360 70C480 60 600 60 720 65C840 70 960 80 1080 85C1200 90 1320 90 1380 90L1440 90V120H1380C1320 120 1200 120 1080 120C960 120 840 120 720 120C600 120 480 120 360 120C240 120 120 120 60 120H0Z" fill="white"/>
        </svg>
      </div>

      <style jsx>{`
        @keyframes float {
          0%, 100% { transform: translateY(0px); }
          50% { transform: translateY(-10px); }
        }
        .animate-float {
          animation: float 3s ease-in-out infinite;
        }
      `}</style>
    </section>
  );
}
