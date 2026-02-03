'use client';

import { useTranslations } from 'next-intl';
import { Order } from '@/lib/api/types';
import { OrderCard } from './OrderCard';

interface OrderStatusColumnProps {
  title: 'pending' | 'preparing' | 'ready';
  orders: Order[];
  color: 'yellow' | 'blue' | 'green';
  nextStatus: 'preparing' | 'ready' | 'completed';
  onUpdateStatus: (orderId: string, status: 'pending' | 'preparing' | 'ready' | 'completed') => void;
}

const colorClasses = {
  yellow: {
    bg: 'bg-yellow-500/20',
    border: 'border-yellow-500',
    header: 'bg-yellow-500',
  },
  blue: {
    bg: 'bg-blue-500/20',
    border: 'border-blue-500',
    header: 'bg-blue-500',
  },
  green: {
    bg: 'bg-green-500/20',
    border: 'border-green-500',
    header: 'bg-green-500',
  },
};

export function OrderStatusColumn({
  title,
  orders,
  color,
  nextStatus,
  onUpdateStatus,
}: OrderStatusColumnProps) {
  const t = useTranslations('kitchen');
  const colors = colorClasses[color];

  return (
    <div className={`flex-1 flex flex-col border-r border-gray-700 ${colors.bg}`}>
      {/* Column Header */}
      <div className={`${colors.header} text-white px-4 py-3 flex items-center justify-between`}>
        <h2 className="font-bold text-lg">{t(title)}</h2>
        <span className="bg-white/20 px-2 py-0.5 rounded text-sm">
          {orders.length}
        </span>
      </div>

      {/* Orders */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {orders.map(order => (
          <OrderCard
            key={order.id}
            order={order}
            nextStatus={nextStatus}
            onStatusUpdate={(status) => onUpdateStatus(order.id, status)}
          />
        ))}
        {orders.length === 0 && (
          <p className="text-gray-500 text-center py-8">
            No orders
          </p>
        )}
      </div>
    </div>
  );
}
