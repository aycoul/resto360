'use client';

import { useState, useEffect } from 'react';
import { useTranslations } from 'next-intl';
import { api } from '@/lib/api/client';
import { ThemeEditor } from '@/components/lite/ThemeEditor';
import type { MenuTheme, ThemeChoices } from '@/lib/api/types';

export default function ThemesPage() {
  const t = useTranslations('lite.themes');
  const tCommon = useTranslations('common');

  const [theme, setTheme] = useState<MenuTheme | null>(null);
  const [choices, setChoices] = useState<ThemeChoices | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadData();
  }, []);

  async function loadData() {
    try {
      setIsLoading(true);
      setError(null);

      const [themeResponse, choicesResponse] = await Promise.all([
        api.get<MenuTheme | null>('/api/v1/menu/theme/active/').catch(() => null),
        api.get<ThemeChoices>('/api/v1/menu/theme/choices/'),
      ]);

      setTheme(themeResponse || getDefaultTheme());
      setChoices(choicesResponse);
    } catch (err) {
      console.error('Failed to load theme:', err);
      setError(tCommon('error'));
    } finally {
      setIsLoading(false);
    }
  }

  function getDefaultTheme(): MenuTheme {
    return {
      is_active: true,
      template: 'minimalist',
      primary_color: '#059669',
      secondary_color: '#14b8a6',
      background_color: '#ffffff',
      text_color: '#111827',
      heading_font: 'inter',
      body_font: 'inter',
      logo_position: 'center',
      show_prices: true,
      show_descriptions: true,
      show_images: true,
      compact_mode: false,
    };
  }

  const handleSave = async (updatedTheme: MenuTheme): Promise<void> => {
    const response = await api.post<MenuTheme>('/api/v1/menu/theme/active/', updatedTheme);
    setTheme(response);
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center">
          <div className="w-8 h-8 border-4 border-emerald-600 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
          <p className="text-gray-500">{tCommon('loading')}</p>
        </div>
      </div>
    );
  }

  if (error || !choices) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center">
          <div className="w-12 h-12 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <svg className="w-6 h-6 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
          </div>
          <p className="text-red-600 mb-2">{error}</p>
          <button
            onClick={loadData}
            className="px-4 py-2 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700"
          >
            Try Again
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">{t('title')}</h1>
        <p className="text-gray-500 mt-1">{t('subtitle')}</p>
      </div>

      <ThemeEditor
        theme={theme || getDefaultTheme()}
        choices={choices}
        onSave={handleSave}
      />
    </div>
  );
}
