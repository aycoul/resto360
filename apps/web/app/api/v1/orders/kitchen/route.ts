import { NextResponse } from 'next/server';

// Mock kitchen orders with different statuses
// Localized for Côte d'Ivoire
const KITCHEN_ORDERS = [
  {
    id: 'order-k1',
    order_number: '#0001',
    status: 'pending',
    order_type: 'dine_in',
    table_number: '5',
    items: [
      { id: 'i1', name: 'Kédjenou de Poulet', quantity: 2, modifiers: ['Attiéké'] },
      { id: 'i2', name: 'Bissap', quantity: 2, modifiers: [] },
    ],
    created_at: new Date(Date.now() - 5 * 60000).toISOString(),
  },
  {
    id: 'order-k2',
    order_number: '#0002',
    status: 'preparing',
    order_type: 'takeout',
    table_number: null,
    items: [
      { id: 'i3', name: 'Garba', quantity: 2, modifiers: ['Oeuf', 'Avocat'] },
      { id: 'i4', name: 'Gnamakoudji', quantity: 2, modifiers: [] },
    ],
    created_at: new Date(Date.now() - 10 * 60000).toISOString(),
  },
  {
    id: 'order-k3',
    order_number: '#0003',
    status: 'ready',
    order_type: 'delivery',
    table_number: null,
    items: [
      { id: 'i5', name: 'Sauce Graine', quantity: 1, modifiers: ['Foutou igname'] },
      { id: 'i6', name: 'Alloco Poisson', quantity: 1, modifiers: [] },
    ],
    created_at: new Date(Date.now() - 15 * 60000).toISOString(),
  },
  {
    id: 'order-k4',
    order_number: '#0004',
    status: 'pending',
    order_type: 'dine_in',
    table_number: '3',
    items: [
      { id: 'i7', name: 'Poisson Braisé', quantity: 1, modifiers: ['Sauce claire', 'Alloco'] },
    ],
    created_at: new Date(Date.now() - 2 * 60000).toISOString(),
  },
];

export async function GET() {
  return NextResponse.json({ orders: KITCHEN_ORDERS });
}
