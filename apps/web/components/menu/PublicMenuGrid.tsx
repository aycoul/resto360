'use client';

import { MenuItem } from '@/lib/api/types';
import { PublicMenuItemCard } from './PublicMenuItemCard';

interface PublicMenuGridProps {
  items: MenuItem[];
}

export function PublicMenuGrid({ items }: PublicMenuGridProps) {
  if (items.length === 0) {
    return (
      <p className="text-gray-400 text-center py-4">
        No items available
      </p>
    );
  }

  return (
    <div className="space-y-3">
      {items.map(item => (
        <PublicMenuItemCard key={item.id} item={item} />
      ))}
    </div>
  );
}
