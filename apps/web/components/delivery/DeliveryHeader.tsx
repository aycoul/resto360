/**
 * Header component for delivery tracking page.
 */
'use client';

import { useTranslations } from 'next-intl';

interface DeliveryHeaderProps {
  orderNumber: number;
  estimatedTime?: string;
  status: string;
}

export default function DeliveryHeader({
  orderNumber,
  estimatedTime,
  status,
}: DeliveryHeaderProps) {
  const t = useTranslations('delivery');

  const formatEta = (isoString?: string) => {
    if (!isoString) return null;
    const date = new Date(isoString);
    return date.toLocaleTimeString([], {
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const eta = formatEta(estimatedTime);

  const statusMessages: Record<string, string> = {
    pending_assignment: t('findingDriver', { defaultValue: 'Finding a driver for your order...' }),
    assigned: t('driverAssigned', { defaultValue: 'A driver has been assigned to your order' }),
    picked_up: t('orderPickedUp', { defaultValue: 'Your order has been picked up' }),
    en_route: t('onTheWay', { defaultValue: 'Your order is on the way!' }),
    delivered: t('orderDelivered', { defaultValue: 'Your order has been delivered' }),
  };

  return (
    <div className="bg-green-500 text-white p-6 rounded-b-3xl shadow-lg">
      <div className="flex justify-between items-start mb-4">
        <div>
          <p className="text-green-100 text-sm">
            {t('order', { defaultValue: 'Order' })} #{orderNumber}
          </p>
          <h1 className="text-2xl font-bold">
            {statusMessages[status] || status}
          </h1>
        </div>
        {status === 'en_route' && eta && (
          <div className="text-right">
            <p className="text-green-100 text-sm">{t('eta', { defaultValue: 'ETA' })}</p>
            <p className="text-2xl font-bold">{eta}</p>
          </div>
        )}
      </div>

      {status === 'delivered' && (
        <div className="bg-green-600 rounded-lg p-3 text-center">
          <span className="text-lg">{t('thankYou', { defaultValue: 'Thank you for your order!' })}</span>
        </div>
      )}
    </div>
  );
}
