/**
 * Hook for real-time delivery tracking via WebSocket.
 */
'use client';

import { useState, useEffect, useCallback, useRef } from 'react';
import { getDeliveryInfo, DeliveryInfo } from '@/lib/api/delivery';

const WS_URL = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000';

interface DriverLocation {
  lat: number;
  lng: number;
  heading?: number;
  timestamp: string;
}

interface UseDeliveryTrackingResult {
  delivery: DeliveryInfo | null;
  driverLocation: DriverLocation | null;
  isLoading: boolean;
  isConnected: boolean;
  error: string | null;
  refresh: () => Promise<void>;
}

export function useDeliveryTracking(deliveryId: string): UseDeliveryTrackingResult {
  const [delivery, setDelivery] = useState<DeliveryInfo | null>(null);
  const [driverLocation, setDriverLocation] = useState<DriverLocation | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const reconnectAttempts = useRef(0);

  const fetchDelivery = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);
      const data = await getDeliveryInfo(deliveryId);

      if (!data) {
        setError('Delivery not found');
        return;
      }

      setDelivery(data);

      // Set initial driver location if available
      if (data.driver?.lat && data.driver?.lng) {
        setDriverLocation({
          lat: data.driver.lat,
          lng: data.driver.lng,
          timestamp: new Date().toISOString(),
        });
      }
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Failed to load delivery';
      setError(message);
    } finally {
      setIsLoading(false);
    }
  }, [deliveryId]);

  const connectWebSocket = useCallback(() => {
    if (!deliveryId) return;

    // Customer tracking doesn't require auth token - delivery ID is the "auth"
    const wsUrl = `${WS_URL}/ws/delivery/${deliveryId}/track/`;

    const ws = new WebSocket(wsUrl);

    ws.onopen = () => {
      setIsConnected(true);
      reconnectAttempts.current = 0;
      console.log('Tracking WebSocket connected');
    };

    ws.onclose = () => {
      setIsConnected(false);
      wsRef.current = null;

      // Reconnect with exponential backoff
      const delay = Math.min(1000 * Math.pow(2, reconnectAttempts.current), 30000);
      reconnectAttempts.current++;

      reconnectTimeoutRef.current = setTimeout(connectWebSocket, delay);
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);

        if (data.type === 'delivery_info') {
          // Initial delivery info from server
          setDelivery(data.delivery);
          if (data.delivery.driver?.lat && data.delivery.driver?.lng) {
            setDriverLocation({
              lat: data.delivery.driver.lat,
              lng: data.delivery.driver.lng,
              timestamp: new Date().toISOString(),
            });
          }
        } else if (data.type === 'driver_location') {
          // Real-time location update
          setDriverLocation({
            lat: data.lat,
            lng: data.lng,
            heading: data.heading,
            timestamp: data.timestamp,
          });
        } else if (data.type === 'status_update') {
          // Status change - refetch full delivery
          fetchDelivery();
        }
      } catch (err) {
        console.error('Failed to parse WebSocket message:', err);
      }
    };

    ws.onerror = (err) => {
      console.error('WebSocket error:', err);
    };

    wsRef.current = ws;
  }, [deliveryId, fetchDelivery]);

  // Initial load and WebSocket connection
  useEffect(() => {
    fetchDelivery();
    connectWebSocket();

    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [fetchDelivery, connectWebSocket]);

  return {
    delivery,
    driverLocation,
    isLoading,
    isConnected,
    error,
    refresh: fetchDelivery,
  };
}
