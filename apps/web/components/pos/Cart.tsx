'use client';

import { useState } from 'react';
import { useTranslations } from 'next-intl';
import { useCart } from '@/lib/hooks/useCart';
import { CartItem } from './CartItem';
import { CheckoutModal } from './CheckoutModal';
import { Button } from '@/components/ui/Button';

export function Cart() {
  const t = useTranslations('pos.cart');
  const { items, subtotal, total, itemCount, clearCart } = useCart();
  const [showCheckout, setShowCheckout] = useState(false);

  return (
    <>
      <div className="flex flex-col h-full">
        {/* Header */}
        <div className="p-4 border-b">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-bold">{t('title')}</h2>
            {items.length > 0 && (
              <button
                onClick={clearCart}
                className="text-sm text-red-500 hover:text-red-700"
              >
                {t('clear')}
              </button>
            )}
          </div>
        </div>

        {/* Items */}
        <div className="flex-1 overflow-y-auto p-4">
          {items.length === 0 ? (
            <p className="text-gray-400 text-center py-8">{t('empty')}</p>
          ) : (
            <div className="space-y-3">
              {items.map(item => (
                <CartItem key={item.id} item={item} />
              ))}
            </div>
          )}
        </div>

        {/* Footer */}
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
            disabled={items.length === 0}
            className="w-full"
            size="lg"
          >
            {t('checkout')} ({itemCount})
          </Button>
        </div>
      </div>

      {showCheckout && (
        <CheckoutModal onClose={() => setShowCheckout(false)} />
      )}
    </>
  );
}
