'use client';

import { useTranslations } from 'next-intl';
import { Order } from '@/lib/api/types';
import { Button } from '@/components/ui/Button';

interface OrderCardProps {
  order: Order;
  nextStatus: 'preparing' | 'ready' | 'completed';
  onStatusUpdate: (status: 'preparing' | 'ready' | 'completed') => void;
}

export function OrderCard({ order, nextStatus, onStatusUpdate }: OrderCardProps) {
  const t = useTranslations('kitchen');

  const orderTypeLabel = {
    dine_in: 'Dine In',
    takeout: 'Takeout',
    delivery: 'Delivery',
  }[order.order_type];

  const actionLabel = {
    preparing: t('markPreparing'),
    ready: t('markReady'),
    completed: t('markComplete'),
  }[nextStatus];

  const timeSinceCreated = getTimeSince(new Date(order.created_at));

  // When nextStatus is 'completed', clicking the button will:
  // 1. Call onStatusUpdate('completed')
  // 2. The useKitchenQueue hook will update the order status
  // 3. The order will be filtered out of readyOrders (since it's now 'completed')
  // 4. The order card will be removed from the display

  return (
    <div className="bg-white rounded-lg shadow-lg overflow-hidden">
      {/* Header */}
      <div className="bg-gray-800 text-white px-4 py-2 flex items-center justify-between">
        <span className="font-bold text-lg">#{order.order_number}</span>
        <div className="flex items-center gap-2">
          <span className="text-sm bg-white/20 px-2 py-0.5 rounded">
            {orderTypeLabel}
          </span>
          {order.table && (
            <span className="text-sm bg-blue-500 px-2 py-0.5 rounded">
              {order.table}
            </span>
          )}
        </div>
      </div>

      {/* Items */}
      <div className="p-4">
        <ul className="space-y-2">
          {order.items.map((item, index) => (
            <li key={index} className="flex justify-between">
              <div>
                <span className="font-medium">
                  {item.quantity}x {item.menu_item_name}
                </span>
                {item.modifiers.length > 0 && (
                  <p className="text-sm text-gray-500 ml-4">
                    {item.modifiers.map(m => m.modifier_option_name).join(', ')}
                  </p>
                )}
                {item.notes && (
                  <p className="text-sm text-orange-600 ml-4 italic">
                    {item.notes}
                  </p>
                )}
              </div>
            </li>
          ))}
        </ul>

        {order.notes && (
          <div className="mt-3 p-2 bg-orange-100 rounded text-orange-800 text-sm">
            Note: {order.notes}
          </div>
        )}
      </div>

      {/* Footer */}
      <div className="px-4 py-3 bg-gray-50 flex items-center justify-between">
        <span className="text-sm text-gray-500">{timeSinceCreated}</span>
        <Button
          onClick={() => onStatusUpdate(nextStatus)}
          size="sm"
          variant={nextStatus === 'completed' ? 'secondary' : 'primary'}
        >
          {actionLabel}
        </Button>
      </div>
    </div>
  );
}

function getTimeSince(date: Date): string {
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / 60000);

  if (diffMins < 1) return 'Just now';
  if (diffMins < 60) return `${diffMins} min ago`;
  const diffHours = Math.floor(diffMins / 60);
  return `${diffHours}h ${diffMins % 60}m ago`;
}
