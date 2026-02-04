'use client';

import { useState } from 'react';
import { useTranslations, useLocale } from 'next-intl';
import Link from 'next/link';
import { LocaleSwitcher } from '@/components/ui/LocaleSwitcher';

export function Navbar() {
  const t = useTranslations('marketing.nav');
  const locale = useLocale();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const navLinks = [
    { href: `/${locale}/features`, label: t('features') },
    { href: `/${locale}/pricing`, label: t('pricing') },
    { href: `/${locale}/use-cases`, label: t('useCases') },
    { href: `/${locale}/menu/demo`, label: t('demo') },
  ];

  return (
    <nav className="fixed top-0 left-0 right-0 z-50 bg-white/80 backdrop-blur-md border-b border-gray-100">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <Link href={`/${locale}`} className="flex items-center gap-2">
            <div className="w-8 h-8 bg-gradient-to-br from-emerald-500 to-teal-600 rounded-lg flex items-center justify-center">
              <span className="text-white font-bold text-sm">B</span>
            </div>
            <span className="text-xl font-bold text-gray-900">BIZ360</span>
          </Link>

          {/* Desktop Navigation */}
          <div className="hidden md:flex items-center gap-8">
            {navLinks.map((link) => (
              <Link
                key={link.href}
                href={link.href}
                className="text-gray-600 hover:text-emerald-600 font-medium transition-colors"
              >
                {link.label}
              </Link>
            ))}
          </div>

          {/* Desktop Actions */}
          <div className="hidden md:flex items-center gap-4">
            <LocaleSwitcher />
            <Link
              href={`/${locale}/login`}
              className="text-gray-600 hover:text-emerald-600 font-medium transition-colors"
            >
              {t('login')}
            </Link>
            <Link
              href={`/${locale}/register`}
              className="inline-flex items-center justify-center px-5 py-2.5 bg-emerald-600 text-white font-semibold rounded-lg hover:bg-emerald-700 transition-colors shadow-sm"
            >
              {t('getStarted')}
            </Link>
          </div>

          {/* Mobile Menu Button */}
          <button
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="md:hidden p-2 text-gray-600 hover:text-gray-900"
            aria-label="Toggle menu"
          >
            {mobileMenuOpen ? (
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            ) : (
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
              </svg>
            )}
          </button>
        </div>
      </div>

      {/* Mobile Menu */}
      {mobileMenuOpen && (
        <div className="md:hidden bg-white border-t border-gray-100">
          <div className="px-4 py-4 space-y-3">
            {navLinks.map((link) => (
              <Link
                key={link.href}
                href={link.href}
                className="block py-2 text-gray-600 hover:text-emerald-600 font-medium"
                onClick={() => setMobileMenuOpen(false)}
              >
                {link.label}
              </Link>
            ))}
            <hr className="my-4" />
            <div className="flex items-center justify-between py-2">
              <span className="text-gray-500 text-sm">Language</span>
              <LocaleSwitcher />
            </div>
            <Link
              href={`/${locale}/login`}
              className="block py-2 text-gray-600 hover:text-emerald-600 font-medium"
              onClick={() => setMobileMenuOpen(false)}
            >
              {t('login')}
            </Link>
            <Link
              href={`/${locale}/register`}
              className="block w-full py-3 text-center bg-emerald-600 text-white font-semibold rounded-lg hover:bg-emerald-700 transition-colors"
              onClick={() => setMobileMenuOpen(false)}
            >
              {t('getStarted')}
            </Link>
          </div>
        </div>
      )}
    </nav>
  );
}
