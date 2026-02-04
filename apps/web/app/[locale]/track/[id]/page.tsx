/**
 * Customer delivery tracking page.
 *
 * URL: /track/{delivery_id}
 * No authentication required - delivery ID serves as the "key".
 */
'use client';

import { useParams } from 'next/navigation';
import { useTranslations } from 'next-intl';
import { useDeliveryTracking } from '@/lib/hooks/useDeliveryTracking';
import TrackingMap from '@/components/delivery/TrackingMap';
import DriverInfo from '@/components/delivery/DriverInfo';
import DeliveryTimeline from '@/components/delivery/DeliveryTimeline';
import DeliveryHeader from '@/components/delivery/DeliveryHeader';

export default function TrackingPage() {
  const params = useParams();
  const deliveryId = params.id as string;
  const t = useTranslations('delivery');

  const {
    delivery,
    driverLocation,
    isLoading,
    isConnected,
    error,
  } = useDeliveryTracking(deliveryId);

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-green-500 mx-auto mb-4" />
          <p className="text-gray-500">{t('loading', { defaultValue: 'Loading...' })}</p>
        </div>
      </div>
    );
  }

  if (error || !delivery) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
        <div className="text-center">
          <div className="text-6xl mb-4">📦</div>
          <h1 className="text-xl font-bold text-gray-800 mb-2">
            {t('notFound', { defaultValue: 'Delivery not found' })}
          </h1>
          <p className="text-gray-500">
            {t('notFoundDesc', { defaultValue: 'This tracking link may have expired or the delivery does not exist.' })}
          </p>
        </div>
      </div>
    );
  }

  const deliveryLocation = {
    lat: delivery.delivery_lat,
    lng: delivery.delivery_lng,
  };

  const restaurantLocation = delivery.restaurant?.lat && delivery.restaurant?.lng
    ? { lat: delivery.restaurant.lat, lng: delivery.restaurant.lng }
    : undefined;

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <DeliveryHeader
        orderNumber={delivery.order_number}
        estimatedTime={delivery.estimated_delivery_time || undefined}
        status={delivery.status}
      />

      {/* Content */}
      <div className="p-4 space-y-4 -mt-4">
        {/* Connection status indicator */}
        {!isConnected && delivery.status !== 'delivered' && (
          <div className="bg-yellow-100 text-yellow-800 px-4 py-2 rounded-lg text-sm text-center">
            {t('reconnecting', { defaultValue: 'Reconnecting for live updates...' })}
          </div>
        )}

        {/* Map - only show for active deliveries with driver */}
        {delivery.driver && delivery.status !== 'delivered' && (
          <TrackingMap
            driverLocation={driverLocation}
            deliveryLocation={deliveryLocation}
            restaurantLocation={restaurantLocation}
          />
        )}

        {/* Driver info - show when driver is assigned */}
        {delivery.driver && (
          <DriverInfo driver={delivery.driver} />
        )}

        {/* Delivery address */}
        <div className="bg-white rounded-lg shadow-md p-4">
          <h3 className="text-sm font-medium text-gray-500 mb-2">
            {t('deliveryAddress', { defaultValue: 'Delivery Address' })}
          </h3>
          <p className="text-gray-900">{delivery.delivery_address}</p>
        </div>

        {/* Status timeline */}
        <DeliveryTimeline
          status={delivery.status}
          assignedAt={delivery.assigned_at}
          pickedUpAt={delivery.picked_up_at}
          enRouteAt={delivery.en_route_at}
          deliveredAt={delivery.delivered_at}
        />

        {/* Restaurant info */}
        {delivery.restaurant && (
          <div className="bg-white rounded-lg shadow-md p-4">
            <h3 className="text-sm font-medium text-gray-500 mb-2">
              {t('restaurant', { defaultValue: 'Restaurant' })}
            </h3>
            <p className="font-medium">{delivery.restaurant.name}</p>
            <p className="text-sm text-gray-500">{delivery.restaurant.address}</p>
          </div>
        )}
      </div>
    </div>
  );
}
