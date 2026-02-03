'use client';

import { useQuery } from '@tanstack/react-query';
import { useLiveQuery } from 'dexie-react-hooks';
import { api } from '@/lib/api/client';
import { db, LocalCategory, LocalMenuItem } from '@/lib/db/schema';
import { Category } from '@/lib/api/types';
import { useOnlineStatus } from './useOnlineStatus';

// Sync menu from API to IndexedDB
async function syncMenuToLocal(categories: Category[]): Promise<void> {
  const now = new Date();

  await db.transaction('rw', db.categories, db.menuItems, async () => {
    // Clear existing data
    await db.categories.clear();
    await db.menuItems.clear();

    // Store categories
    for (const category of categories) {
      await db.categories.add({
        id: category.id,
        name: category.name,
        displayOrder: category.display_order,
        isVisible: category.is_visible,
        syncedAt: now,
      });

      // Store menu items
      for (const item of category.items) {
        await db.menuItems.add({
          id: item.id,
          categoryId: category.id,
          name: item.name,
          description: item.description,
          price: item.price,
          thumbnailUrl: item.thumbnail_url,
          isAvailable: item.is_available,
          modifiers: item.modifiers.map(m => ({
            id: m.id,
            name: m.name,
            required: m.required,
            maxSelections: m.max_selections,
            options: m.options.map(o => ({
              id: o.id,
              name: o.name,
              priceAdjustment: o.price_adjustment,
              isAvailable: o.is_available,
            })),
          })),
          syncedAt: now,
        });
      }
    }
  });
}

export function useMenu() {
  const isOnline = useOnlineStatus();

  // Fetch from API when online
  const apiQuery = useQuery({
    queryKey: ['menu'],
    queryFn: async () => {
      const data = await api.get<{ categories: Category[] }>('/api/v1/menu/full/');
      await syncMenuToLocal(data.categories);
      return data.categories;
    },
    enabled: isOnline,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });

  // Read from IndexedDB (reactive)
  const localCategories = useLiveQuery(
    () => db.categories.orderBy('displayOrder').toArray(),
    [],
    []
  );

  const localItems = useLiveQuery(
    () => db.menuItems.toArray(),
    [],
    []
  );

  // Organize items by category
  const categoriesWithItems = localCategories.map(cat => ({
    ...cat,
    items: localItems.filter(item => item.categoryId === cat.id),
  }));

  return {
    categories: categoriesWithItems,
    isLoading: apiQuery.isLoading && localCategories.length === 0,
    error: apiQuery.error,
    refetch: apiQuery.refetch,
    isOnline,
  };
}

// Get single menu item by ID
export function useMenuItem(itemId: string) {
  return useLiveQuery(
    () => db.menuItems.get(itemId),
    [itemId]
  );
}
