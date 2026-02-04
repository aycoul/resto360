'use client';

import { useState, useRef } from 'react';
import { useTranslations } from 'next-intl';
import { api } from '@/lib/api/client';

interface MenuItemStepProps {
  categoryId: string;
  categoryName: string;
  onNext: () => void;
  onBack: () => void;
}

interface FormData {
  name: string;
  price: string;
  description: string;
}

interface MenuItemResponse {
  id: string;
  name: string;
  price: number;
  description: string;
  thumbnail_url: string | null;
}

export function MenuItemStep({ categoryId, categoryName, onNext, onBack }: MenuItemStepProps) {
  const t = useTranslations('onboarding.menuItem');
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [formData, setFormData] = useState<FormData>({
    name: '',
    price: '',
    description: '',
  });
  const [photoFile, setPhotoFile] = useState<File | null>(null);
  const [photoPreview, setPhotoPreview] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);
  const [createdItem, setCreatedItem] = useState<MenuItemResponse | null>(null);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handlePhotoChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      if (file.size > 2 * 1024 * 1024) {
        setError('Photo file must be less than 2MB');
        return;
      }
      setPhotoFile(file);
      setPhotoPreview(URL.createObjectURL(file));
      setError(null);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!formData.name.trim()) {
      setError(t('item_name') + ' is required');
      return;
    }

    if (!formData.price || parseInt(formData.price) <= 0) {
      setError(t('price') + ' must be greater than 0');
      return;
    }

    setIsSubmitting(true);
    setError(null);

    try {
      const response = await api.post<MenuItemResponse>('/api/v1/menu/items/', {
        name: formData.name.trim(),
        price: parseInt(formData.price),
        description: formData.description.trim(),
        category: categoryId,
        is_available: true,
      });

      setCreatedItem(response);
      setSuccess(true);

      // TODO: Handle photo upload separately via multipart form data

      // Wait a moment to show success feedback and preview
      setTimeout(() => {
        onNext();
      }, 1500);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to add menu item');
    } finally {
      setIsSubmitting(false);
    }
  };

  const formatPrice = (price: string) => {
    const num = parseInt(price);
    if (isNaN(num)) return '';
    return new Intl.NumberFormat('fr-FR').format(num) + ' XOF';
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

      {success && createdItem && (
        <div className="mb-6 p-4 bg-emerald-50 border border-emerald-200 rounded-lg">
          <div className="flex items-center gap-2 text-emerald-700 mb-3">
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
            {t('success')}
          </div>

          {/* Item Preview Card */}
          <div className="bg-white rounded-lg p-4 shadow-sm">
            <div className="flex gap-4">
              {photoPreview ? (
                <img
                  src={photoPreview}
                  alt={createdItem.name}
                  className="w-20 h-20 rounded-lg object-cover"
                />
              ) : (
                <div className="w-20 h-20 rounded-lg bg-gray-100 flex items-center justify-center">
                  <svg className="w-8 h-8 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                  </svg>
                </div>
              )}
              <div className="flex-1">
                <h4 className="font-semibold text-gray-900">{createdItem.name}</h4>
                <p className="text-sm text-gray-500">{categoryName}</p>
                <p className="text-emerald-600 font-semibold mt-1">
                  {formatPrice(createdItem.price.toString())}
                </p>
              </div>
            </div>
          </div>
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Item Name */}
        <div>
          <label htmlFor="name" className="block text-sm font-medium text-gray-700 mb-1">
            {t('item_name')}
          </label>
          <input
            type="text"
            id="name"
            name="name"
            value={formData.name}
            onChange={handleChange}
            className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500"
            placeholder={t('item_name_placeholder')}
            disabled={isSubmitting || success}
          />
        </div>

        {/* Price */}
        <div>
          <label htmlFor="price" className="block text-sm font-medium text-gray-700 mb-1">
            {t('price')}
          </label>
          <div className="relative">
            <input
              type="number"
              id="price"
              name="price"
              value={formData.price}
              onChange={handleChange}
              className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500"
              placeholder={t('price_placeholder')}
              min="0"
              disabled={isSubmitting || success}
            />
            <span className="absolute right-4 top-1/2 -translate-y-1/2 text-gray-400">
              XOF
            </span>
          </div>
        </div>

        {/* Description */}
        <div>
          <label htmlFor="description" className="block text-sm font-medium text-gray-700 mb-1">
            {t('description')}
          </label>
          <textarea
            id="description"
            name="description"
            value={formData.description}
            onChange={handleChange}
            rows={3}
            className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 resize-none"
            placeholder={t('description_placeholder')}
            disabled={isSubmitting || success}
          />
        </div>

        {/* Category (readonly) */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            {t('category')}
          </label>
          <div className="px-4 py-3 bg-gray-50 border border-gray-200 rounded-xl text-gray-700">
            {categoryName}
          </div>
        </div>

        {/* Photo Upload */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            {t('photo')}
          </label>
          <p className="text-xs text-gray-500 mb-2">{t('photo_hint')}</p>

          <input
            type="file"
            ref={fileInputRef}
            onChange={handlePhotoChange}
            accept="image/png,image/jpeg"
            className="hidden"
          />

          <div className="flex items-center gap-4">
            {photoPreview ? (
              <div className="relative">
                <img
                  src={photoPreview}
                  alt="Photo preview"
                  className="w-20 h-20 rounded-lg object-cover border border-gray-200"
                />
                <button
                  type="button"
                  onClick={() => {
                    setPhotoFile(null);
                    setPhotoPreview(null);
                    if (fileInputRef.current) {
                      fileInputRef.current.value = '';
                    }
                  }}
                  disabled={isSubmitting || success}
                  className="absolute -top-2 -right-2 w-6 h-6 bg-red-500 text-white rounded-full flex items-center justify-center text-sm disabled:opacity-50"
                >
                  x
                </button>
              </div>
            ) : (
              <button
                type="button"
                onClick={() => fileInputRef.current?.click()}
                disabled={isSubmitting || success}
                className="flex items-center gap-2 px-4 py-2 border-2 border-dashed border-gray-300 rounded-xl text-gray-600 hover:border-emerald-500 hover:text-emerald-600 transition-colors disabled:opacity-50"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                </svg>
                {t('upload_photo')}
              </button>
            )}
          </div>
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
            disabled={isSubmitting || success || !formData.name.trim() || !formData.price}
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
            ) : (
              t('create')
            )}
          </button>
        </div>
      </form>
    </div>
  );
}
