'use client';

import { useState, useCallback, useMemo, useRef } from 'react';
import { Order } from '@/lib/api/types';
import { api } from '@/lib/api/client';

type OrderStatus = 'pending' | 'preparing' | 'ready' | 'completed' | 'cancelled';

// Play a beep sound using Web Audio API
function playNewOrderSound() {
  if (typeof window === 'undefined') return;
  try {
    const AudioContextClass = window.AudioContext || (window as unknown as { webkitAudioContext: typeof AudioContext }).webkitAudioContext;
    if (!AudioContextClass) return;

    const audioContext = new AudioContextClass();
    const oscillator = audioContext.createOscillator();
    const gainNode = audioContext.createGain();

    oscillator.connect(gainNode);
    gainNode.connect(audioContext.destination);

    oscillator.frequency.value = 800;
    oscillator.type = 'sine';
    gainNode.gain.setValueAtTime(0.3, audioContext.currentTime);
    gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.5);

    oscillator.start(audioContext.currentTime);
    oscillator.stop(audioContext.currentTime + 0.5);
  } catch {
    // Audio not supported or blocked by browser
  }
}

export function useKitchenQueue() {
  const [orders, setOrders] = useState<Order[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const completedOrderTimeouts = useRef<Map<string, ReturnType<typeof setTimeout>>>(new Map());

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
    // Play sound for new order
    playNewOrderSound();
  }, []);

  const handleOrderUpdated = useCallback((order: Order) => {
    setOrders(prev =>
      prev.map(o => (o.id === order.id ? order : o))
    );
  }, []);

  const handleStatusChanged = useCallback((orderId: string, status: string) => {
    setOrders(prev => {
      // Remove completed/cancelled orders after short delay
      // This ensures the order is removed from display after confirmation
      if (status === 'completed' || status === 'cancelled') {
        const timeout = setTimeout(() => {
          setOrders(current => current.filter(o => o.id !== orderId));
          completedOrderTimeouts.current.delete(orderId);
        }, 2000); // 2 second delay for visual confirmation
        completedOrderTimeouts.current.set(orderId, timeout);
      }
      return prev.map(o =>
        o.id === orderId ? { ...o, status: status as OrderStatus } : o
      );
    });
  }, []);

  const updateOrderStatus = useCallback(async (orderId: string, status: OrderStatus) => {
    try {
      // Optimistic update
      setOrders(prev =>
        prev.map(o => (o.id === orderId ? { ...o, status } : o))
      );

      await api.patch(`/api/v1/orders/${orderId}/status/`, { status });

      // Remove completed orders after delay (visual feedback before removal)
      // This implements: "Completed orders are removed from display after confirmation"
      if (status === 'completed') {
        const timeout = setTimeout(() => {
          setOrders(prev => prev.filter(o => o.id !== orderId));
          completedOrderTimeouts.current.delete(orderId);
        }, 2000);
        completedOrderTimeouts.current.set(orderId, timeout);
      }
    } catch (error) {
      console.error('Failed to update order status:', error);
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
