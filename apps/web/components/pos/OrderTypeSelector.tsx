'use client';

import { useTranslations } from 'next-intl';
import { useCart } from '@/lib/hooks/useCart';

export function OrderTypeSelector() {
  const t = useTranslations('pos.order');
  const { orderType, setOrderType } = useCart();

  const types = [
    { value: 'dine_in', label: t('dineIn') },
    { value: 'takeout', label: t('takeout') },
    { value: 'delivery', label: t('delivery') },
  ] as const;

  return (
    <div>
      <label className="block text-sm font-medium text-gray-700 mb-2">
        {t('type')}
      </label>
      <div className="flex gap-2">
        {types.map(type => (
          <button
            key={type.value}
            onClick={() => setOrderType(type.value)}
            className={`flex-1 py-2 rounded-lg transition-colors ${
              orderType === type.value
                ? 'bg-blue-600 text-white'
                : 'bg-gray-100 hover:bg-gray-200'
            }`}
          >
            {type.label}
          </button>
        ))}
      </div>
    </div>
  );
}
