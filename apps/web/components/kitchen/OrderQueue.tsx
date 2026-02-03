'use client';

import { Order } from '@/lib/api/types';
import { OrderStatusColumn } from './OrderStatusColumn';

interface OrderQueueProps {
  pendingOrders: Order[];
  preparingOrders: Order[];
  readyOrders: Order[];
  onUpdateStatus: (orderId: string, status: 'pending' | 'preparing' | 'ready' | 'completed') => void;
}

export function OrderQueue({
  pendingOrders,
  preparingOrders,
  readyOrders,
  onUpdateStatus,
}: OrderQueueProps) {
  return (
    <div className="flex-1 flex overflow-hidden">
      <OrderStatusColumn
        title="pending"
        orders={pendingOrders}
        color="yellow"
        nextStatus="preparing"
        onUpdateStatus={onUpdateStatus}
      />
      <OrderStatusColumn
        title="preparing"
        orders={preparingOrders}
        color="blue"
        nextStatus="ready"
        onUpdateStatus={onUpdateStatus}
      />
      <OrderStatusColumn
        title="ready"
        orders={readyOrders}
        color="green"
        nextStatus="completed"
        onUpdateStatus={onUpdateStatus}
      />
    </div>
  );
}
