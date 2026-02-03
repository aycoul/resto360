'use client';

import { useState } from 'react';
import { useTranslations } from 'next-intl';
import { useMenu } from '@/lib/hooks/useMenu';
import { CategoryTabs } from '@/components/pos/CategoryTabs';
import { MenuGrid } from '@/components/pos/MenuGrid';
import { Cart } from '@/components/pos/Cart';
import { LocaleSwitcher } from '@/components/ui/LocaleSwitcher';

export default function POSPage() {
  const t = useTranslations('pos');
  // useMenu hook fetches categories from API, syncs to IndexedDB, and returns
  // categoriesWithItems which includes both category data and their menu items
  const { categories, isLoading, isOnline } = useMenu();
  const [selectedCategoryId, setSelectedCategoryId] = useState<string | null>(null);

  // Default to first category
  const activeCategory = selectedCategoryId
    ? categories.find(c => c.id === selectedCategoryId)
    : categories[0];

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <p className="text-gray-500">{t('menu.title')}...</p>
      </div>
    );
  }

  return (
    <div className="flex h-screen bg-gray-100">
      {/* Left: Menu Section */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Header */}
        <header className="bg-white shadow-sm px-4 py-3 flex items-center justify-between">
          <h1 className="text-xl font-bold">{t('title')}</h1>
          <div className="flex items-center gap-4">
            {!isOnline && (
              <span className="text-red-500 text-sm">Offline</span>
            )}
            <LocaleSwitcher />
          </div>
        </header>

        {/* Category Tabs - receives categories from useMenu */}
        <CategoryTabs
          categories={categories}
          selectedId={activeCategory?.id || null}
          onSelect={setSelectedCategoryId}
        />

        {/* Menu Grid - receives items from activeCategory (which comes from useMenu) */}
        <div className="flex-1 overflow-y-auto p-4">
          {activeCategory && (
            <MenuGrid items={activeCategory.items} />
          )}
        </div>
      </div>

      {/* Right: Cart Section */}
      <div className="w-96 bg-white shadow-lg flex flex-col">
        <Cart />
      </div>
    </div>
  );
}
