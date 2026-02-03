'use client';

import { useState } from 'react';
import { useTranslations } from 'next-intl';
import { LocalMenuItem } from '@/lib/db/schema';
import { useCart } from '@/lib/hooks/useCart';
import { ModifierModal } from './ModifierModal';

interface MenuItemCardProps {
  item: LocalMenuItem;
  disabled?: boolean;
}

export function MenuItemCard({ item, disabled }: MenuItemCardProps) {
  const t = useTranslations('pos.menu');
  const { addItem } = useCart();
  const [showModifiers, setShowModifiers] = useState(false);

  const handleClick = () => {
    if (disabled) return;

    // If item has modifiers, show modal
    if (item.modifiers.length > 0) {
      setShowModifiers(true);
    } else {
      // Add directly to cart
      addItem(item);
    }
  };

  const handleAddWithModifiers = (
    selectedModifiers: { optionId: string; optionName: string; priceAdjustment: number }[]
  ) => {
    addItem(item, 1, selectedModifiers);
    setShowModifiers(false);
  };

  return (
    <>
      <button
        onClick={handleClick}
        disabled={disabled}
        className={`bg-white rounded-lg shadow p-4 text-left transition-transform hover:scale-105 ${
          disabled ? 'opacity-50 cursor-not-allowed' : ''
        }`}
      >
        {item.thumbnailUrl && (
          <img
            src={item.thumbnailUrl}
            alt={item.name}
            className="w-full h-24 object-cover rounded mb-2"
          />
        )}
        <h3 className="font-medium text-gray-900">{item.name}</h3>
        {item.description && (
          <p className="text-sm text-gray-500 line-clamp-2">{item.description}</p>
        )}
        <p className="mt-2 font-bold text-blue-600">
          {item.price.toLocaleString()} XOF
        </p>
        {disabled && (
          <span className="text-xs text-red-500">{t('unavailable')}</span>
        )}
      </button>

      {showModifiers && (
        <ModifierModal
          item={item}
          onClose={() => setShowModifiers(false)}
          onAdd={handleAddWithModifiers}
        />
      )}
    </>
  );
}
