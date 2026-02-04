'use client';

import { useState, useEffect } from 'react';
import { useTranslations } from 'next-intl';
import { api } from '@/lib/api/client';
import { MenuEditor } from '@/components/lite/MenuEditor';

interface Category {
  id: string;
  name: string;
  display_order: number;
  is_visible: boolean;
}

interface MenuItem {
  id: string;
  category: string;
  name: string;
  description: string;
  price: number;
  thumbnail_url: string | null;
  is_available: boolean;
}

export default function LiteMenuPage() {
  const t = useTranslations('lite.menu');
  const tCommon = useTranslations('common');

  const [categories, setCategories] = useState<Category[]>([]);
  const [items, setItems] = useState<MenuItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadMenu();
  }, []);

  async function loadMenu() {
    try {
      setIsLoading(true);
      setError(null);

      // API returns paginated response {count, next, previous, results}
      interface PaginatedResponse<T> {
        count: number;
        next: string | null;
        previous: string | null;
        results: T[];
      }

      const [categoriesResponse, itemsResponse] = await Promise.all([
        api.get<PaginatedResponse<Category>>('/api/v1/menu/categories/'),
        api.get<PaginatedResponse<MenuItem>>('/api/v1/menu/items/'),
      ]);

      setCategories(categoriesResponse.results || []);
      setItems(itemsResponse.results || []);
    } catch (err) {
      console.error('Failed to load menu:', err);
      setError(t('error'));
    } finally {
      setIsLoading(false);
    }
  }

  const handleCategoryCreate = async (name: string): Promise<Category> => {
    const newCategory = await api.post<Category>('/api/v1/menu/categories/', {
      name,
      display_order: categories.length,
      is_visible: true,
    });
    setCategories([...categories, newCategory]);
    return newCategory;
  };

  const handleCategoryUpdate = async (id: string, data: Partial<Category>): Promise<void> => {
    const updated = await api.patch<Category>(`/api/v1/menu/categories/${id}/`, data);
    setCategories(categories.map((c) => (c.id === id ? updated : c)));
  };

  const handleCategoryDelete = async (id: string): Promise<void> => {
    await api.delete(`/api/v1/menu/categories/${id}/`);
    setCategories(categories.filter((c) => c.id !== id));
  };

  const handleItemCreate = async (data: Partial<MenuItem>): Promise<MenuItem> => {
    const newItem = await api.post<MenuItem>('/api/v1/menu/items/', data);
    setItems([...items, newItem]);
    return newItem;
  };

  const handleItemUpdate = async (id: string, data: Partial<MenuItem>): Promise<void> => {
    const updated = await api.patch<MenuItem>(`/api/v1/menu/items/${id}/`, data);
    setItems(items.map((i) => (i.id === id ? updated : i)));
  };

  const handleItemDelete = async (id: string): Promise<void> => {
    await api.delete(`/api/v1/menu/items/${id}/`);
    setItems(items.filter((i) => i.id !== id));
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

  if (error) {
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
            onClick={loadMenu}
            className="px-4 py-2 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700"
          >
            {tCommon('cancel') === 'Cancel' ? 'Try Again' : 'Reessayer'}
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

      <MenuEditor
        categories={categories}
        items={items}
        onCategoryCreate={handleCategoryCreate}
        onCategoryUpdate={handleCategoryUpdate}
        onCategoryDelete={handleCategoryDelete}
        onItemCreate={handleItemCreate}
        onItemUpdate={handleItemUpdate}
        onItemDelete={handleItemDelete}
      />
    </div>
  );
}
