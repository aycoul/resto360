'use client';

import { useState, useCallback, useMemo } from 'react';
import { Order } from '@/lib/api/types';
import { api } from '@/lib/api/client';

type OrderStatus = 'pending' | 'preparing' | 'ready' | 'completed' | 'cancelled';

export function useKitchenQueue() {
  const [orders, setOrders] = useState<Order[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  const handleInitialQueue = useCallback((initialOrders: Order[]) => {
    setOrders(initialOrders);
    setIsLoading(false);
  }, []);

  const handleOrderCreated = useCallback((order: Order) => {
    setOrders(prev => {
      // Check if order already exists
      if (prev.some(o => o.id === order.id)) {
        return prev;
      }
      // Add to end, maintaining sort by created_at
      return [...prev, order].sort(
        (a, b) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime()
      );
    });
  }, []);

  const handleOrderUpdated = useCallback((order: Order) => {
    setOrders(prev =>
      prev.map(o => (o.id === order.id ? order : o))
    );
  }, []);

  const handleStatusChanged = useCallback((orderId: string, status: string) => {
    setOrders(prev =>
      prev.map(o =>
        o.id === orderId ? { ...o, status: status as OrderStatus } : o
      )
    );
  }, []);

  const updateOrderStatus = useCallback(async (orderId: string, status: OrderStatus) => {
    try {
      // Optimistic update
      setOrders(prev =>
        prev.map(o => (o.id === orderId ? { ...o, status } : o))
      );

      // API call
      await api.patch(`/api/v1/orders/${orderId}/status/`, { status });
    } catch (error) {
      console.error('Failed to update order status:', error);
      // Revert on error - refetch from server would be better
    }
  }, []);

  const pendingOrders = useMemo(
    () => orders.filter(o => o.status === 'pending'),
    [orders]
  );

  const preparingOrders = useMemo(
    () => orders.filter(o => o.status === 'preparing'),
    [orders]
  );

  const readyOrders = useMemo(
    () => orders.filter(o => o.status === 'ready'),
    [orders]
  );

  return {
    orders,
    pendingOrders,
    preparingOrders,
    readyOrders,
    isLoading,
    handleInitialQueue,
    handleOrderCreated,
    handleOrderUpdated,
    handleStatusChanged,
    updateOrderStatus,
  };
}
