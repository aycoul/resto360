'use client';

import { useState } from 'react';
import Link from 'next/link';
import { useLocale, useTranslations } from 'next-intl';

interface UpgradePromptProps {
  variant: 'banner' | 'card' | 'inline';
}

export function UpgradePrompt({ variant }: UpgradePromptProps) {
  const locale = useLocale();
  const t = useTranslations('lite.upgrade');
  const [dismissed, setDismissed] = useState(false);

  if (dismissed && variant === 'banner') {
    return null;
  }

  if (variant === 'banner') {
    return (
      <div className="relative bg-gradient-to-r from-emerald-500 to-teal-500 text-white px-4 py-3 rounded-lg mb-6">
        <div className="flex items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-white/20 rounded-lg">
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 3v4M3 5h4M6 17v4m-2-2h4m5-16l2.286 6.857L21 12l-5.714 2.143L13 21l-2.286-6.857L5 12l5.714-2.143L13 3z" />
              </svg>
            </div>
            <div>
              <p className="font-medium">{t('bannerTitle')}</p>
              <p className="text-sm text-white/80">{t('bannerDescription')}</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <Link
              href={`/${locale}/lite/upgrade`}
              className="px-4 py-2 bg-white text-emerald-600 font-medium rounded-lg hover:bg-gray-50 transition-colors text-sm whitespace-nowrap"
            >
              {t('upgradeCta')}
            </Link>
            <button
              onClick={() => setDismissed(true)}
              className="p-1 text-white/70 hover:text-white hover:bg-white/10 rounded-lg"
              aria-label="Dismiss"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>
      </div>
    );
  }

  if (variant === 'card') {
    return (
      <div className="bg-white border border-emerald-200 rounded-xl p-6 shadow-sm">
        <div className="flex items-start gap-4">
          <div className="p-3 bg-emerald-100 rounded-xl">
            <svg className="w-6 h-6 text-emerald-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 3v4M3 5h4M6 17v4m-2-2h4m5-16l2.286 6.857L21 12l-5.714 2.143L13 21l-2.286-6.857L5 12l5.714-2.143L13 3z" />
            </svg>
          </div>
          <div className="flex-1">
            <h3 className="font-semibold text-gray-900">{t('cardTitle')}</h3>
            <p className="text-sm text-gray-600 mt-1">{t('cardDescription')}</p>
            <ul className="mt-3 space-y-2">
              <li className="flex items-center gap-2 text-sm text-gray-600">
                <svg className="w-4 h-4 text-emerald-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
                {t('feature1')}
              </li>
              <li className="flex items-center gap-2 text-sm text-gray-600">
                <svg className="w-4 h-4 text-emerald-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
                {t('feature2')}
              </li>
              <li className="flex items-center gap-2 text-sm text-gray-600">
                <svg className="w-4 h-4 text-emerald-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
                {t('feature3')}
              </li>
            </ul>
            <Link
              href={`/${locale}/lite/upgrade`}
              className="inline-flex items-center gap-2 mt-4 px-4 py-2 bg-emerald-600 text-white font-medium rounded-lg hover:bg-emerald-700 transition-colors"
            >
              {t('upgradeCta')}
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
              </svg>
            </Link>
          </div>
        </div>
      </div>
    );
  }

  // inline variant
  return (
    <div className="flex items-center gap-2 text-sm">
      <svg className="w-4 h-4 text-emerald-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 3v4M3 5h4M6 17v4m-2-2h4m5-16l2.286 6.857L21 12l-5.714 2.143L13 21l-2.286-6.857L5 12l5.714-2.143L13 3z" />
      </svg>
      <span className="text-gray-600">{t('inlineText')}</span>
      <Link
        href={`/${locale}/lite/upgrade`}
        className="text-emerald-600 font-medium hover:text-emerald-700 underline-offset-2 hover:underline"
      >
        {t('upgradeCta')}
      </Link>
    </div>
  );
}
