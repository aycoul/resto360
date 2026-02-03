'use client';

import { useQuery } from '@tanstack/react-query';
import { Category } from '@/lib/api/types';

interface Restaurant {
  id: string;
  name: string;
  slug: string;
  address: string;
  phone: string;
}

interface PublicMenuResponse {
  restaurant: Restaurant;
  categories: Category[];
}

export function usePublicMenu(slug: string) {
  return useQuery({
    queryKey: ['public-menu', slug],
    queryFn: async (): Promise<PublicMenuResponse> => {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || '';
      const response = await fetch(`${apiUrl}/api/v1/menu/public/${slug}/`);

      if (!response.ok) {
        if (response.status === 404) {
          throw new Error('Restaurant not found');
        }
        throw new Error('Failed to load menu');
      }

      return response.json();
    },
    staleTime: 5 * 60 * 1000, // 5 minutes
    retry: 2,
  });
}

interface CreateOrderPayload {
  order_type: 'dine_in' | 'takeout';
  table?: string;
  customer_name: string;
  customer_phone?: string;
  items: {
    menu_item_id: string;
    quantity: number;
    notes?: string;
    modifiers: { modifier_option_id: string }[];
  }[];
}

interface OrderResponse {
  id: string;
  order_number: number;
  status: string;
  total: number;
  estimated_wait: number;
}

export async function createPublicOrder(
  slug: string,
  payload: CreateOrderPayload
): Promise<OrderResponse> {
  const apiUrl = process.env.NEXT_PUBLIC_API_URL || '';
  const response = await fetch(`${apiUrl}/api/v1/menu/public/${slug}/order/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.detail || 'Failed to create order');
  }

  return response.json();
}
