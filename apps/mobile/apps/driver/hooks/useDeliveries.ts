/**
 * Hook for fetching and managing deliveries.
 */
import { useState, useEffect, useCallback } from 'react';
import { api } from '../services/api';

export interface Delivery {
  id: string;
  order_number: number;
  status: string;
  pickup_address: string;
  pickup_lat?: number;
  pickup_lng?: number;
  delivery_address: string;
  delivery_lat: number;
  delivery_lng: number;
  delivery_notes: string;
  delivery_fee: number;
  customer_name: string;
  customer_phone: string;
  estimated_delivery_time: string | null;
  created_at: string;
}

interface UseDeliveriesReturn {
  deliveries: Delivery[];
  loading: boolean;
  error: string | null;
  refresh: () => Promise<void>;
}

export function useDeliveries(): UseDeliveriesReturn {
  const [deliveries, setDeliveries] = useState<Delivery[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchDeliveries = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await api.getActiveDeliveries();
      setDeliveries(Array.isArray(data) ? data : []);
    } catch (err: unknown) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to fetch deliveries';
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  }, []);

  const refreshDeliveries = async () => {
    await fetchDeliveries();
  };

  useEffect(() => {
    fetchDeliveries();
  }, [fetchDeliveries]);

  return {
    deliveries,
    loading,
    error,
    refresh: refreshDeliveries,
  };
}
