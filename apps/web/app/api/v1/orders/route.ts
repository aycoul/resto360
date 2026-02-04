import { NextRequest, NextResponse } from 'next/server';

// In-memory store for demo (resets on server restart)
let orders: any[] = [];
let orderCounter = 1;

export async function GET() {
  return NextResponse.json({ orders });
}

export async function POST(request: NextRequest) {
  const body = await request.json();

  const order = {
    id: `order-${Date.now()}`,
    order_number: `#${String(orderCounter++).padStart(4, '0')}`,
    status: 'pending',
    order_type: body.order_type || 'dine_in',
    table_number: body.table_number,
    items: body.items,
    subtotal: body.subtotal,
    total: body.total,
    notes: body.notes,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  };

  orders.push(order);

  return NextResponse.json(order, { status: 201 });
}
