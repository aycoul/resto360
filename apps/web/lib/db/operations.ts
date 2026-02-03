import { db, LocalOrder, PendingOperation } from './schema';
import { queueOperation } from './sync';
import { api } from '@/lib/api/client';
import { CreateOrderPayload, Order } from '@/lib/api/types';

// Create order offline-first
export async function createOfflineOrder(
  orderData: Omit<LocalOrder, 'localId' | 'serverId' | 'orderNumber' | 'status' | 'createdAt' | 'syncedAt'>
): Promise<string> {
  const localId = crypto.randomUUID();
  const now = new Date();

  // 1. Store order locally
  await db.orders.add({
    localId,
    serverId: null,
    orderNumber: null,
    status: 'pending',
    createdAt: now,
    syncedAt: null,
    ...orderData,
  });

  // 2. Queue sync operation
  const apiPayload: CreateOrderPayload = {
    order_type: orderData.orderType,
    table: orderData.tableId || undefined,
    customer_name: orderData.customerName || undefined,
    customer_phone: orderData.customerPhone || undefined,
    notes: orderData.notes || undefined,
    items: orderData.items.map(item => ({
      menu_item_id: item.menuItemId,
      quantity: item.quantity,
      notes: item.notes || undefined,
      modifiers: item.modifiers.map(m => ({ modifier_option_id: m.optionId })),
    })),
  };

  await queueOperation('CREATE_ORDER', {
    localId,
    payload: apiPayload,
  });

  // 3. Trigger sync if online
  if (typeof navigator !== 'undefined' && navigator.onLine) {
    syncPendingOrders();
  }

  return localId;
}

// Sync pending orders to server
export async function syncPendingOrders(): Promise<void> {
  const pendingOps = await db.pendingOps
    .where('syncStatus')
    .equals('pending')
    .sortBy('createdAt');

  for (const op of pendingOps) {
    if (op.type === 'CREATE_ORDER') {
      await syncCreateOrder(op);
    }
  }
}

async function syncCreateOrder(op: PendingOperation): Promise<void> {
  if (!op.id) return;

  try {
    // Mark as syncing
    await db.pendingOps.update(op.id, { syncStatus: 'syncing' });

    // Send to API
    const payload = op.payload as { localId: string; payload: CreateOrderPayload };
    const result = await api.post<Order>('/api/v1/orders/', payload.payload);

    // Update local order with server data
    await db.orders.update(payload.localId, {
      serverId: result.id,
      orderNumber: result.order_number,
      status: result.status,
      syncedAt: new Date(),
    });

    // Remove operation from queue
    await db.pendingOps.delete(op.id);
  } catch (error) {
    // Mark as failed and increment retry count
    const retryCount = (op.retryCount || 0) + 1;
    await db.pendingOps.update(op.id, {
      syncStatus: retryCount >= 3 ? 'failed' : 'pending',
      retryCount,
      lastError: error instanceof Error ? error.message : 'Unknown error',
    });
  }
}

// Get local orders
export async function getLocalOrders(): Promise<LocalOrder[]> {
  return db.orders.orderBy('createdAt').reverse().toArray();
}

// Update local order status
export async function updateLocalOrderStatus(
  localId: string,
  status: LocalOrder['status']
): Promise<void> {
  await db.orders.update(localId, { status });
}
