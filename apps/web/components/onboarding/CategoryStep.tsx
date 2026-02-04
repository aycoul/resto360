'use client';

import { useState } from 'react';
import { useTranslations } from 'next-intl';
import { api } from '@/lib/api/client';

interface CategoryStepProps {
  onNext: (categoryId: string, categoryName: string) => void;
  onBack: () => void;
}

interface CategoryResponse {
  id: string;
  name: string;
  display_order: number;
  is_visible: boolean;
}

export function CategoryStep({ onNext, onBack }: CategoryStepProps) {
  const t = useTranslations('onboarding.category');

  const [categoryName, setCategoryName] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!categoryName.trim()) {
      setError(t('category_name') + ' is required');
      return;
    }

    setIsSubmitting(true);
    setError(null);

    try {
      const response = await api.post<CategoryResponse>('/api/v1/menu/categories/', {
        name: categoryName.trim(),
        display_order: 1,
        is_visible: true,
      });

      setSuccess(true);

      // Wait a moment to show success feedback
      setTimeout(() => {
        onNext(response.id, response.name);
      }, 1000);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create category');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="max-w-lg mx-auto">
      <div className="text-center mb-8">
        <h2 className="text-2xl font-bold text-gray-900">{t('title')}</h2>
        <p className="text-gray-500 mt-2">{t('subtitle')}</p>
      </div>

      {error && (
        <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
          {error}
        </div>
      )}

      {success && (
        <div className="mb-6 p-4 bg-emerald-50 border border-emerald-200 rounded-lg text-emerald-700 text-sm flex items-center gap-2">
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
          </svg>
          {t('success')}
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Category Name */}
        <div>
          <label htmlFor="categoryName" className="block text-sm font-medium text-gray-700 mb-1">
            {t('category_name')}
          </label>
          <input
            type="text"
            id="categoryName"
            value={categoryName}
            onChange={(e) => setCategoryName(e.target.value)}
            className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500"
            placeholder={t('placeholder')}
            disabled={isSubmitting || success}
          />
        </div>

        {/* Suggestions */}
        <div className="flex flex-wrap gap-2">
          {['Plats principaux', 'Entrees', 'Boissons', 'Desserts'].map((suggestion) => (
            <button
              key={suggestion}
              type="button"
              onClick={() => setCategoryName(suggestion)}
              disabled={isSubmitting || success}
              className="px-3 py-1.5 text-sm bg-gray-100 text-gray-700 rounded-full hover:bg-emerald-100 hover:text-emerald-700 transition-colors disabled:opacity-50"
            >
              {suggestion}
            </button>
          ))}
        </div>

        {/* Actions */}
        <div className="flex gap-3 pt-4">
          <button
            type="button"
            onClick={onBack}
            disabled={isSubmitting}
            className="flex-1 py-3 border border-gray-300 text-gray-700 font-medium rounded-xl hover:bg-gray-50 disabled:opacity-50 transition-colors"
          >
            {t('back')}
          </button>
          <button
            type="submit"
            disabled={isSubmitting || success || !categoryName.trim()}
            className="flex-1 py-3 bg-emerald-600 text-white font-semibold rounded-xl hover:bg-emerald-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {isSubmitting ? (
              <span className="flex items-center justify-center">
                <svg className="animate-spin -ml-1 mr-2 h-5 w-5 text-white" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                {t('creating')}
              </span>
            ) : success ? (
              <span className="flex items-center justify-center">
                <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
                {t('success')}
              </span>
            ) : (
              t('create')
            )}
          </button>
        </div>
      </form>
    </div>
  );
}
