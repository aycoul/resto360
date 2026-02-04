import { NextRequest, NextResponse } from 'next/server';

// Mock delivery data matching DeliveryInfo interface
// Localized for Côte d'Ivoire (Abidjan)
const DELIVERIES: Record<string, any> = {
  'demo-delivery-1': {
    id: 'demo-delivery-1',
    status: 'en_route',
    delivery_address: 'Rue des Jardins, Cocody, Abidjan',
    delivery_lat: 5.3500,
    delivery_lng: -3.9833,
    estimated_delivery_time: new Date(Date.now() + 15 * 60000).toISOString(),
    customer_name: 'Kouamé Yao',
    customer_phone: '+225 07 55 12 34',
    delivery_fee: 1500,
    order_number: 5,
    driver: {
      name: 'Koné Ibrahim',
      phone: '+225 05 12 34 56',
      vehicle_type: 'Moto',
      lat: 5.3600,
      lng: -3.9900,
    },
    restaurant: {
      name: 'Maquis Ivoire',
      phone: '+225 27 20 21 22 23',
      address: 'Boulevard de France, Cocody, Abidjan',
      lat: 5.3450,
      lng: -3.9867,
    },
    created_at: new Date(Date.now() - 30 * 60000).toISOString(),
    assigned_at: new Date(Date.now() - 20 * 60000).toISOString(),
    picked_up_at: new Date(Date.now() - 10 * 60000).toISOString(),
    en_route_at: new Date(Date.now() - 5 * 60000).toISOString(),
  },
  'demo-delivery-2': {
    id: 'demo-delivery-2',
    status: 'assigned',
    delivery_address: 'Avenue Houdaille, Plateau, Abidjan',
    delivery_lat: 5.3200,
    delivery_lng: -4.0167,
    estimated_delivery_time: new Date(Date.now() + 30 * 60000).toISOString(),
    customer_name: 'Adjoua Koffi',
    customer_phone: '+225 07 66 78 90',
    delivery_fee: 1000,
    order_number: 6,
    driver: {
      name: 'Traoré Awa',
      phone: '+225 05 98 76 54',
      vehicle_type: 'Moto',
      lat: 5.3450,
      lng: -3.9867,
    },
    restaurant: {
      name: 'Maquis Ivoire',
      phone: '+225 27 20 21 22 23',
      address: 'Boulevard de France, Cocody, Abidjan',
      lat: 5.3450,
      lng: -3.9867,
    },
    created_at: new Date(Date.now() - 10 * 60000).toISOString(),
    assigned_at: new Date(Date.now() - 5 * 60000).toISOString(),
  },
  'demo-delivery-3': {
    id: 'demo-delivery-3',
    status: 'delivered',
    delivery_address: 'Boulevard Lagunaire, Marcory, Abidjan',
    delivery_lat: 5.3000,
    delivery_lng: -4.0000,
    estimated_delivery_time: null,
    customer_name: 'Coulibaly Drissa',
    customer_phone: '+225 07 77 43 21',
    delivery_fee: 1500,
    order_number: 4,
    driver: {
      name: 'Koné Ibrahim',
      phone: '+225 05 12 34 56',
      vehicle_type: 'Moto',
    },
    restaurant: {
      name: 'Maquis Ivoire',
      phone: '+225 27 20 21 22 23',
      address: 'Boulevard de France, Cocody, Abidjan',
      lat: 5.3450,
      lng: -3.9867,
    },
    created_at: new Date(Date.now() - 60 * 60000).toISOString(),
    assigned_at: new Date(Date.now() - 55 * 60000).toISOString(),
    picked_up_at: new Date(Date.now() - 45 * 60000).toISOString(),
    en_route_at: new Date(Date.now() - 40 * 60000).toISOString(),
    delivered_at: new Date(Date.now() - 30 * 60000).toISOString(),
  },
};

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params;

  const delivery = DELIVERIES[id];

  if (!delivery) {
    return NextResponse.json(
      { error: 'Delivery not found' },
      { status: 404 }
    );
  }

  return NextResponse.json(delivery);
}
