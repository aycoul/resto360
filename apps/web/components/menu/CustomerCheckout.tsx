'use client';

import { useState } from 'react';
import { useTranslations } from 'next-intl';
import { useCart } from '@/lib/hooks/useCart';
import { createPublicOrder } from '@/lib/hooks/usePublicMenu';
import { OrderConfirmation } from './OrderConfirmation';
import { Button } from '@/components/ui/Button';

interface CustomerCheckoutProps {
  restaurantSlug: string;
  onBack: () => void;
  onComplete: () => void;
}

export function CustomerCheckout({
  restaurantSlug,
  onBack,
  onComplete,
}: CustomerCheckoutProps) {
  const t = useTranslations('pos.order');
  const tCommon = useTranslations('common');
  const { items, total, clearCart } = useCart();

  const [orderType, setOrderType] = useState<'dine_in' | 'takeout'>('dine_in');
  const [tableNumber, setTableNumber] = useState('');
  const [customerName, setCustomerName] = useState('');
  const [customerPhone, setCustomerPhone] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [orderResult, setOrderResult] = useState<{
    orderNumber: number;
    total: number;
    estimatedWait: number;
  } | null>(null);

  const handleSubmit = async () => {
    setError(null);

    // Validation
    if (orderType === 'dine_in' && !tableNumber.trim()) {
      setError('Please enter your table number');
      return;
    }
    if (!customerName.trim()) {
      setError('Please enter your name');
      return;
    }

    setIsSubmitting(true);
    try {
      const result = await createPublicOrder(restaurantSlug, {
        order_type: orderType,
        table: orderType === 'dine_in' ? tableNumber : undefined,
        customer_name: customerName,
        customer_phone: customerPhone || undefined,
        items: items.map(item => ({
          menu_item_id: item.menuItemId,
          quantity: item.quantity,
          notes: item.notes || undefined,
          modifiers: item.modifiers.map(m => ({ modifier_option_id: m.optionId })),
        })),
      });

      setOrderResult({
        orderNumber: result.order_number,
        total: result.total,
        estimatedWait: result.estimated_wait,
      });
      clearCart();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to submit order');
    } finally {
      setIsSubmitting(false);
    }
  };

  if (orderResult) {
    return (
      <OrderConfirmation
        orderNumber={orderResult.orderNumber}
        total={orderResult.total}
        estimatedWait={orderResult.estimatedWait}
        onClose={onComplete}
      />
    );
  }

  return (
    <div className="fixed inset-0 bg-black/50 flex items-end justify-center z-50">
      <div className="bg-white rounded-t-2xl w-full max-w-lg max-h-[80vh] overflow-hidden">
        {/* Header */}
        <div className="p-4 border-b flex items-center">
          <button
            onClick={onBack}
            className="mr-4 text-gray-500 hover:text-gray-700 text-xl"
            aria-label="Back"
          >
            &larr;
          </button>
          <h2 className="text-lg font-bold">{t('submit')}</h2>
        </div>

        {/* Form */}
        <div className="p-4 space-y-4 overflow-y-auto max-h-[50vh]">
          {/* Error message */}
          {error && (
            <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
              {error}
            </div>
          )}

          {/* Order Type */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              {t('type')}
            </label>
            <div className="flex gap-2">
              <button
                onClick={() => setOrderType('dine_in')}
                className={`flex-1 py-3 rounded-lg border-2 transition-colors ${
                  orderType === 'dine_in'
                    ? 'border-blue-500 bg-blue-50 text-blue-700'
                    : 'border-gray-200 hover:border-gray-300'
                }`}
              >
                {t('dineIn')}
              </button>
              <button
                onClick={() => setOrderType('takeout')}
                className={`flex-1 py-3 rounded-lg border-2 transition-colors ${
                  orderType === 'takeout'
                    ? 'border-blue-500 bg-blue-50 text-blue-700'
                    : 'border-gray-200 hover:border-gray-300'
                }`}
              >
                {t('takeout')}
              </button>
            </div>
          </div>

          {/* Table Number (for dine-in) */}
          {orderType === 'dine_in' && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                {t('table')} *
              </label>
              <input
                type="text"
                value={tableNumber}
                onChange={e => setTableNumber(e.target.value)}
                placeholder="e.g. Table 5"
                className="w-full p-3 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              />
            </div>
          )}

          {/* Customer Name */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Your Name *
            </label>
            <input
              type="text"
              value={customerName}
              onChange={e => setCustomerName(e.target.value)}
              className="w-full p-3 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            />
          </div>

          {/* Phone (optional) */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Phone (optional)
            </label>
            <input
              type="tel"
              value={customerPhone}
              onChange={e => setCustomerPhone(e.target.value)}
              placeholder="+225"
              className="w-full p-3 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            />
          </div>

          {/* Total */}
          <div className="pt-4 border-t">
            <div className="flex justify-between text-lg font-bold">
              <span>Total</span>
              <span>{total.toLocaleString()} XOF</span>
            </div>
          </div>
        </div>

        {/* Submit */}
        <div className="p-4 border-t bg-gray-50">
          <Button
            onClick={handleSubmit}
            disabled={isSubmitting}
            className="w-full"
            size="lg"
          >
            {isSubmitting ? tCommon('loading') : t('submit')}
          </Button>
        </div>
      </div>
    </div>
  );
}
