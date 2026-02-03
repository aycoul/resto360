'use client';

import { useState } from 'react';
import { useTranslations } from 'next-intl';
import { useCart } from '@/lib/hooks/useCart';
import { CartItem } from '@/lib/store/cartStore';
import { CustomerCheckout } from './CustomerCheckout';
import { Button } from '@/components/ui/Button';

interface CustomerCartProps {
  restaurantSlug: string;
  onClose: () => void;
}

export function CustomerCart({ restaurantSlug, onClose }: CustomerCartProps) {
  const t = useTranslations('pos.cart');
  const { items, subtotal, total, updateQuantity, removeItem } = useCart();
  const [showCheckout, setShowCheckout] = useState(false);

  if (showCheckout) {
    return (
      <CustomerCheckout
        restaurantSlug={restaurantSlug}
        onBack={() => setShowCheckout(false)}
        onComplete={onClose}
      />
    );
  }

  return (
    <div className="fixed inset-0 bg-black/50 flex items-end justify-center z-50">
      <div className="bg-white rounded-t-2xl w-full max-w-lg max-h-[80vh] overflow-hidden">
        {/* Header */}
        <div className="p-4 border-b flex items-center justify-between">
          <h2 className="text-lg font-bold">{t('title')}</h2>
          <button
            onClick={onClose}
            className="text-2xl text-gray-400 hover:text-gray-600 w-8 h-8 flex items-center justify-center"
            aria-label="Close"
          >
            &times;
          </button>
        </div>

        {/* Items */}
        <div className="p-4 overflow-y-auto max-h-[50vh]">
          {items.length === 0 ? (
            <p className="text-gray-400 text-center py-8">{t('empty')}</p>
          ) : (
            <div className="space-y-3">
              {items.map(item => (
                <CustomerCartItem
                  key={item.id}
                  item={item}
                  onUpdateQuantity={(qty) => updateQuantity(item.id, qty)}
                  onRemove={() => removeItem(item.id)}
                />
              ))}
            </div>
          )}
        </div>

        {/* Footer */}
        {items.length > 0 && (
          <div className="p-4 border-t bg-gray-50">
            <div className="flex justify-between mb-2">
              <span className="text-gray-600">{t('subtotal')}</span>
              <span>{subtotal.toLocaleString()} XOF</span>
            </div>
            <div className="flex justify-between mb-4 text-lg font-bold">
              <span>{t('total')}</span>
              <span>{total.toLocaleString()} XOF</span>
            </div>
            <Button
              onClick={() => setShowCheckout(true)}
              className="w-full"
              size="lg"
            >
              {t('checkout')}
            </Button>
          </div>
        )}
      </div>
    </div>
  );
}

function CustomerCartItem({
  item,
  onUpdateQuantity,
  onRemove,
}: {
  item: CartItem;
  onUpdateQuantity: (qty: number) => void;
  onRemove: () => void;
}) {
  return (
    <div className="flex items-center gap-3 bg-gray-50 rounded-lg p-3">
      <div className="flex-1 min-w-0">
        <h4 className="font-medium truncate">{item.menuItemName}</h4>
        {item.modifiers.length > 0 && (
          <p className="text-sm text-gray-500 truncate">
            {item.modifiers.map(m => m.optionName).join(', ')}
          </p>
        )}
        <p className="text-blue-600 font-medium mt-1">
          {(item.unitPrice * item.quantity).toLocaleString()} XOF
        </p>
      </div>
      <div className="flex items-center gap-2 flex-shrink-0">
        <button
          onClick={() => onUpdateQuantity(item.quantity - 1)}
          className="w-8 h-8 rounded-full bg-gray-200 flex items-center justify-center hover:bg-gray-300 transition-colors"
          aria-label="Decrease quantity"
        >
          -
        </button>
        <span className="w-6 text-center font-medium">{item.quantity}</span>
        <button
          onClick={() => onUpdateQuantity(item.quantity + 1)}
          className="w-8 h-8 rounded-full bg-gray-200 flex items-center justify-center hover:bg-gray-300 transition-colors"
          aria-label="Increase quantity"
        >
          +
        </button>
      </div>
    </div>
  );
}
