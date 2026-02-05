'use client';

import { useState, useEffect } from 'react';
import { useTranslations } from 'next-intl';
import { useAuth } from '@/lib/hooks/useAuth';
import { useKitchenSocket } from '@/lib/hooks/useKitchenSocket';
import { useKitchenQueue } from '@/lib/hooks/useKitchenQueue';
import { OrderQueue } from '@/components/kitchen/OrderQueue';
import { LocaleSwitcher } from '@/components/ui/LocaleSwitcher';

// In real app, get this from auth context
const MOCK_RESTAURANT_ID = 'restaurant-uuid-here';

export default function KitchenPage() {
  const t = useTranslations('kitchen');
  const { isLoading: authLoading, isAuthenticated } = useAuth({ required: true });
  const [currentTime, setCurrentTime] = useState(new Date());

  const {
    pendingOrders,
    preparingOrders,
    readyOrders,
    isLoading,
    handleInitialQueue,
    handleOrderCreated,
    handleOrderUpdated,
    handleStatusChanged,
    updateOrderStatus,
  } = useKitchenQueue();

  const { isConnected, error } = useKitchenSocket({
    restaurantId: MOCK_RESTAURANT_ID,
    onInitialQueue: handleInitialQueue,
    onOrderCreated: handleOrderCreated,
    onOrderUpdated: handleOrderUpdated,
    onStatusChanged: handleStatusChanged,
  });

  // Auto-update time every second
  useEffect(() => {
    const interval = setInterval(() => {
      setCurrentTime(new Date());
    }, 1000);
    return () => clearInterval(interval);
  }, []);

  if (authLoading || !isAuthenticated) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <p className="text-gray-500">Loading...</p>
      </div>
    );
  }

  return (
    <div className="h-screen flex flex-col">
      {/* Header */}
      <header className="bg-gray-800 text-white px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-4">
          <h1 className="text-2xl font-bold">{t('title')}</h1>
          <div className={`w-3 h-3 rounded-full ${
            isConnected ? 'bg-green-500' : 'bg-red-500'
          }`} />
          {error && <span className="text-red-400 text-sm">{error}</span>}
        </div>
        <div className="flex items-center gap-4">
          <span className="text-gray-400">
            {currentTime.toLocaleTimeString()}
          </span>
          <LocaleSwitcher />
        </div>
      </header>

      {/* Queue */}
      {isLoading ? (
        <div className="flex-1 flex items-center justify-center text-white">
          <p>{t('queue')}...</p>
        </div>
      ) : (
        <OrderQueue
          pendingOrders={pendingOrders}
          preparingOrders={preparingOrders}
          readyOrders={readyOrders}
          onUpdateStatus={updateOrderStatus}
        />
      )}
    </div>
  );
}
