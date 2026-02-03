'use client';

import { useState } from 'react';
import { MenuItem } from '@/lib/api/types';
import { useCart } from '@/lib/hooks/useCart';
import { LocalMenuItem } from '@/lib/db/schema';
import { PublicModifierModal } from './PublicModifierModal';

// Convert API MenuItem to LocalMenuItem for cart
function toLocalMenuItem(item: MenuItem): LocalMenuItem {
  return {
    id: item.id,
    categoryId: item.category,
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
    syncedAt: new Date(),
  };
}

interface PublicMenuItemCardProps {
  item: MenuItem;
}

export function PublicMenuItemCard({ item }: PublicMenuItemCardProps) {
  const { addItem } = useCart();
  const [showModifiers, setShowModifiers] = useState(false);

  const handleClick = () => {
    if (item.modifiers.length > 0) {
      setShowModifiers(true);
    } else {
      addItem(toLocalMenuItem(item));
    }
  };

  const handleAddWithModifiers = (
    selectedModifiers: { optionId: string; optionName: string; priceAdjustment: number }[]
  ) => {
    addItem(toLocalMenuItem(item), 1, selectedModifiers);
    setShowModifiers(false);
  };

  return (
    <>
      <button
        onClick={handleClick}
        className="w-full bg-white rounded-lg shadow p-4 text-left flex gap-4 hover:shadow-md transition-shadow"
      >
        {item.thumbnail_url && (
          <img
            src={item.thumbnail_url}
            alt={item.name}
            className="w-20 h-20 object-cover rounded flex-shrink-0"
          />
        )}
        <div className="flex-1 min-w-0">
          <h3 className="font-medium">{item.name}</h3>
          {item.description && (
            <p className="text-sm text-gray-500 line-clamp-2 mt-1">
              {item.description}
            </p>
          )}
          <p className="text-blue-600 font-bold mt-2">
            {item.price.toLocaleString()} XOF
          </p>
        </div>
        <div className="flex items-center flex-shrink-0">
          <span className="w-8 h-8 bg-blue-600 text-white rounded-full flex items-center justify-center text-lg font-medium">
            +
          </span>
        </div>
      </button>

      {showModifiers && (
        <PublicModifierModal
          item={toLocalMenuItem(item)}
          onClose={() => setShowModifiers(false)}
          onAdd={handleAddWithModifiers}
        />
      )}
    </>
  );
}
