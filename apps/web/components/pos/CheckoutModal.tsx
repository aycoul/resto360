'use client';

import { useState } from 'react';
import { useTranslations } from 'next-intl';
import { useCart } from '@/lib/hooks/useCart';
import { createOfflineOrder } from '@/lib/db/operations';
import { OrderTypeSelector } from './OrderTypeSelector';
import { Button } from '@/components/ui/Button';

interface CheckoutModalProps {
  onClose: () => void;
}

export function CheckoutModal({ onClose }: CheckoutModalProps) {
  const t = useTranslations('pos.order');
  const tCommon = useTranslations('common');
  const {
    items,
    orderType,
    tableId,
    customerName,
    customerPhone,
    notes,
    subtotal,
    total,
    setTable,
    setCustomerName,
    setCustomerPhone,
    setNotes,
    clearCart,
  } = useCart();

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [orderCreated, setOrderCreated] = useState(false);
  const [localOrderId, setLocalOrderId] = useState<string | null>(null);

  const handleSubmit = async () => {
    // Validate
    if (orderType === 'dine_in' && !tableId) {
      alert('Please select a table');
      return;
    }

    setIsSubmitting(true);
    try {
      const orderId = await createOfflineOrder({
        orderType,
        tableId,
        customerName,
        customerPhone,
        notes,
        items: items.map(item => ({
          menuItemId: item.menuItemId,
          menuItemName: item.menuItemName,
          quantity: item.quantity,
          unitPrice: item.unitPrice,
          notes: item.notes,
          modifiers: item.modifiers,
        })),
        subtotal,
        total,
      });

      setLocalOrderId(orderId);
      setOrderCreated(true);
      clearCart();
    } catch (error) {
      alert('Failed to create order');
    } finally {
      setIsSubmitting(false);
    }
  };

  if (orderCreated) {
    return (
      <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
        <div className="bg-white rounded-lg p-6 w-full max-w-md text-center">
          <div className="text-green-500 text-5xl mb-4">&#10003;</div>
          <h2 className="text-xl font-bold mb-2">Order Created!</h2>
          <p className="text-gray-500 mb-4">
            Order has been queued for processing.
          </p>
          <Button onClick={onClose} className="w-full">
            Continue
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg w-full max-w-md max-h-[80vh] overflow-hidden">
        <div className="p-4 border-b">
          <h2 className="text-lg font-bold">{t('submit')}</h2>
        </div>

        <div className="p-4 space-y-4 overflow-y-auto max-h-[50vh]">
          <OrderTypeSelector />

          {orderType === 'dine_in' && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                {t('table')}
              </label>
              <input
                type="text"
                value={tableId || ''}
                onChange={e => setTable(e.target.value || null)}
                placeholder="Table number"
                className="w-full p-2 border rounded"
              />
            </div>
          )}

          {orderType === 'delivery' && (
            <>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Customer Name
                </label>
                <input
                  type="text"
                  value={customerName}
                  onChange={e => setCustomerName(e.target.value)}
                  className="w-full p-2 border rounded"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Phone
                </label>
                <input
                  type="tel"
                  value={customerPhone}
                  onChange={e => setCustomerPhone(e.target.value)}
                  className="w-full p-2 border rounded"
                />
              </div>
            </>
          )}

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              {t('notes')}
            </label>
            <textarea
              value={notes}
              onChange={e => setNotes(e.target.value)}
              className="w-full p-2 border rounded"
              rows={2}
            />
          </div>

          <div className="border-t pt-4">
            <div className="flex justify-between text-lg font-bold">
              <span>Total</span>
              <span>{total.toLocaleString()} XOF</span>
            </div>
          </div>
        </div>

        <div className="p-4 border-t flex gap-2">
          <Button variant="secondary" onClick={onClose} className="flex-1">
            {tCommon('cancel')}
          </Button>
          <Button
            onClick={handleSubmit}
            disabled={isSubmitting}
            className="flex-1"
          >
            {isSubmitting ? tCommon('loading') : t('submit')}
          </Button>
        </div>
      </div>
    </div>
  );
}
