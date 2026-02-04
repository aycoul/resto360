/**
 * Delivery API client for customer tracking.
 */
const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export interface DeliveryInfo {
  id: string;
  status: 'pending_assignment' | 'assigned' | 'picked_up' | 'en_route' | 'delivered' | 'cancelled';
  delivery_address: string;
  estimated_delivery_time: string | null;
  customer_name: string;
  customer_phone: string;
  delivery_fee: number;
  order_number: number;
  driver?: {
    name: string;
    phone: string;
    vehicle_type: string;
    lat?: number;
    lng?: number;
  };
  restaurant?: {
    name: string;
    phone: string;
    address: string;
    lat?: number;
    lng?: number;
  };
  delivery_lat: number;
  delivery_lng: number;
  created_at: string;
  assigned_at?: string;
  picked_up_at?: string;
  en_route_at?: string;
  delivered_at?: string;
}

export async function getDeliveryInfo(deliveryId: string): Promise<DeliveryInfo | null> {
  try {
    // Public endpoint - no auth required for tracking
    const response = await fetch(`${API_URL}/api/v1/delivery/track/${deliveryId}/`);

    if (!response.ok) {
      if (response.status === 404) {
        return null;
      }
      throw new Error('Failed to fetch delivery info');
    }

    return response.json();
  } catch (error) {
    console.error('Error fetching delivery:', error);
    return null;
  }
}
