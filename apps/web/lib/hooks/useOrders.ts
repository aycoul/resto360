'use client';

import { useLiveQuery } from 'dexie-react-hooks';
import { db, LocalOrder } from '@/lib/db/schema';

export function useLocalOrders() {
  const orders = useLiveQuery(
    () => db.orders.orderBy('createdAt').reverse().toArray(),
    [],
    []
  );

  const pendingOrders = orders.filter(o => o.status === 'pending');
  const preparingOrders = orders.filter(o => o.status === 'preparing');
  const readyOrders = orders.filter(o => o.status === 'ready');

  return {
    orders,
    pendingOrders,
    preparingOrders,
    readyOrders,
  };
}

export function useOrder(localId: string) {
  return useLiveQuery(
    () => db.orders.get({ localId }),
    [localId]
  );
}
