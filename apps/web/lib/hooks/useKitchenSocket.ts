'use client';

import { useEffect, useRef, useState, useCallback } from 'react';
import { getAccessToken } from '@/lib/api/client';
import { Order } from '@/lib/api/types';

type KitchenMessage =
  | { type: 'initial_queue'; orders: Order[] }
  | { type: 'order_created'; order: Order }
  | { type: 'order_updated'; order: Order }
  | { type: 'order_status_changed'; order_id: string; status: string };

interface UseKitchenSocketOptions {
  restaurantId: string;
  onInitialQueue?: (orders: Order[]) => void;
  onOrderCreated?: (order: Order) => void;
  onOrderUpdated?: (order: Order) => void;
  onStatusChanged?: (orderId: string, status: string) => void;
}

export function useKitchenSocket({
  restaurantId,
  onInitialQueue,
  onOrderCreated,
  onOrderUpdated,
  onStatusChanged,
}: UseKitchenSocketOptions) {
  const wsRef = useRef<WebSocket | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const reconnectTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const reconnectAttempts = useRef(0);

  const connect = useCallback(() => {
    const token = getAccessToken();
    if (!token) {
      setError('No authentication token');
      return;
    }

    const wsUrl = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000';
    const ws = new WebSocket(
      `${wsUrl}/ws/kitchen/${restaurantId}/?token=${token}`
    );

    ws.onopen = () => {
      setIsConnected(true);
      setError(null);
      reconnectAttempts.current = 0;
    };

    ws.onmessage = (event) => {
      try {
        const message: KitchenMessage = JSON.parse(event.data);

        switch (message.type) {
          case 'initial_queue':
            onInitialQueue?.(message.orders);
            break;
          case 'order_created':
            onOrderCreated?.(message.order);
            break;
          case 'order_updated':
            onOrderUpdated?.(message.order);
            break;
          case 'order_status_changed':
            onStatusChanged?.(message.order_id, message.status);
            break;
        }
      } catch (e) {
        console.error('Failed to parse WebSocket message:', e);
      }
    };

    ws.onerror = () => {
      setError('WebSocket connection error');
    };

    ws.onclose = (event) => {
      setIsConnected(false);
      wsRef.current = null;

      // Reconnect with exponential backoff
      if (event.code !== 1000) { // Not a clean close
        const delay = Math.min(1000 * Math.pow(2, reconnectAttempts.current), 30000);
        reconnectAttempts.current += 1;
        reconnectTimeoutRef.current = setTimeout(connect, delay);
      }
    };

    wsRef.current = ws;
  }, [restaurantId, onInitialQueue, onOrderCreated, onOrderUpdated, onStatusChanged]);

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
    }
    if (wsRef.current) {
      wsRef.current.close(1000);
      wsRef.current = null;
    }
  }, []);

  const sendStatusUpdate = useCallback((orderId: string, status: string) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({
        type: 'update_status',
        order_id: orderId,
        status,
      }));
    }
  }, []);

  useEffect(() => {
    connect();
    return disconnect;
  }, [connect, disconnect]);

  return {
    isConnected,
    error,
    sendStatusUpdate,
    reconnect: connect,
  };
}
