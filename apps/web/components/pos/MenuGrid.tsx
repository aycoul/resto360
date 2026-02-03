'use client';

import { LocalMenuItem } from '@/lib/db/schema';
import { MenuItemCard } from './MenuItemCard';

interface MenuGridProps {
  // items are passed from POSPage, which gets them from useMenu hook
  // via activeCategory.items
  items: LocalMenuItem[];
}

export function MenuGrid({ items }: MenuGridProps) {
  const availableItems = items.filter(item => item.isAvailable);
  const unavailableItems = items.filter(item => !item.isAvailable);

  return (
    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
      {availableItems.map(item => (
        <MenuItemCard key={item.id} item={item} />
      ))}
      {unavailableItems.map(item => (
        <MenuItemCard key={item.id} item={item} disabled />
      ))}
    </div>
  );
}
